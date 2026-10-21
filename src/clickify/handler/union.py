import types
import typing
from collections.abc import Sequence
from dataclasses import replace
from typing import override

import click

from clickify.func.paraminfo import ParamInfo
from clickify.handler.base import BaseParamHandler, HandlerResult
from clickify.handler.registry import HandlerRegistry
from clickify.typeutil import unwrap_annotation


class UnionParamType[Tout, Tin](click.ParamType[Tout, Tin]):
    def __init__(self, params: Sequence[click.Parameter], allow_none: bool = False):
        self.params = params
        self.allow_none = allow_none

    @override
    def convert(self, value: Tin, param: click.Parameter | None, ctx: click.Context | None) -> Tout:

        # None is special case: Just pass out as-is without trying to convert.
        if self.allow_none and value is None:
            return typing.cast(Tout, None)  # Allow None to be passed through.

        for param in self.params:
            try:
                val = param.type.convert(value, param, ctx)
                return typing.cast(Tout, val)
            except click.BadParameter:
                pass
        self.fail("Cannot convert {value!} to any of defined union types")


class UnionParamHandler(BaseParamHandler):
    """For Unions, try to convert each type in turn until one is successful.

    NOTE: Order matters.  `int | float` will produce an int (`2`) `"2"`, but `float | int` will produce `2.0`
    None cases are ignored.

    None is ignored as an option, so for simple T | None types, equivalent to an annotation of just T.
    Otherwise, complex types which produce multiple (or no) parameters are not supported, and will raise an exception.
    """

    def __init__(self, registry: HandlerRegistry):
        self.registry = registry

    def __call__(self, info: ParamInfo) -> HandlerResult[typing.Any] | None:
        ann, meta = unwrap_annotation(info.annotation, resolve_generic=False)
        if typing.get_origin(ann) is not typing.Union:
            return None

        args = typing.get_args(ann)
        allow_none = types.NoneType in args
        union_types = [t for t in args if t is not types.NoneType]

        # Get handler for each type.
        handlers = [self.registry.handle_param(replace(info, annotation=union_type)) for union_type in union_types]
        if any((len(h.params) != 1) for h in handlers):
            return None

        if len(handlers) == 1:
            # Single item.
            return handlers[0]

        params = [h.params[0] for h in handlers]
        uniontype = UnionParamType(params, allow_none)

        return HandlerResult(info, [info.to_click_parameter(type=uniontype)])
