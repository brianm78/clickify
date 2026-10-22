import types
import typing
from collections.abc import Sequence
from dataclasses import replace
from typing import override

import click
from click._utils import UNSET

from clickify.func.paraminfo import ParamInfo
from clickify.handler.base import (
    BaseParamHandler,
    FailedHandlerException,
    HandlerResult,
    IgnoreParameterException,
    NotHandledException,
)
from clickify.registry import HandlerRegistry
from clickify.typeutil import unwrap_annotation


class UnionParamType[Tout, Tin](click.ParamType[Tout, Tin]):
    def __init__(self, params: Sequence[click.Parameter]):
        self.params = params

    @override
    def convert(self, value: Tin, param: click.Parameter | None, ctx: click.Context | None) -> Tout:
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

    Handling defaults is complicated by the fact that it'll still be passed to the type.
    As such, we set the default to UNSET, and if no value is provided, we return the default

    This also allows for unhandled types to still be defaults.  Eg.
        x : str | SomeSentinel = SomeSentinel()
    """

    def __init__(self, registry: HandlerRegistry):
        self.registry = registry

    def __call__(self, info: ParamInfo) -> HandlerResult[typing.Any] | None:
        ann, meta = unwrap_annotation(info.annotation, resolve_generic=False)

        if typing.get_origin(ann) is not typing.Union:
            return None

        args = typing.get_args(ann)
        union_types = [t for t in args if t is not types.NoneType]

        # Get handler for each type.
        # Note: If no handler exists for one of the types, we still allow it
        # (Eg. for cases where it's used as the default).  It just won't be settable from a commandline
        # option.  However, we require at least one to have a valid handler.
        handlers: list[HandlerResult[typing.Any]] = []
        for union_type in union_types:
            try:
                result = self.registry.handle_param(replace(info, default=UNSET, annotation=union_type))
                if len(result.params) != 1:
                    raise FailedHandlerException(
                        f"Type used in union parameter does not resolve to a single click parameter: {union_type}"
                    )
                handlers.append(result)
            except NotHandledException:
                # Allow types with no handler (eg. where default value is a different type)
                # These just don't get added to parameter handler.
                pass

        if len(handlers) == 0:
            raise FailedHandlerException(f"No handlers for any type in union: {union_types}")

        params = [h.params[0] for h in handlers]
        uniontype = UnionParamType(params)

        # We mark the parameter non-required and unset the default, instead handling this
        # after the fact.  This is because we don't want the default to go through the click
        # conversion process (indeed, it might not even be one of the handled types.)
        # Eg.  `str | None = None`
        #  or even `int | str = '1'`, where we want the string '1', not int 4 to come out with no default.

        def callback(opts: dict[str, typing.Any]):
            if info.name not in opts or opts[info.name] is None:
                if info.default is not UNSET:
                    return info.default
                raise IgnoreParameterException(f"Parameter not provided: {info.name}")

            return opts.pop(info.name)

        kwargs: dict[str, typing.Any] = {}
        if info.default is not UNSET:
            # Override required to be false, handle default in callback.
            kwargs = {"required": False}
        return HandlerResult(info, [info.to_click_parameter(type=uniontype, default=None, **kwargs)], callback)
