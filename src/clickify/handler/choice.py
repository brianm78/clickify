"""
Handle literal / enum types as a click.Choice
"""

import enum
import typing

import click
import click.types

from clickify.func.paraminfo import ParamInfo
from clickify.handler.base import HandlerResult
from clickify.handler.clicktypes import ClickTypeHandler
from clickify.types import ClickOptions, TypeOptions
from clickify.typeutil import unwrap_annotation


class ChoiceTypeHandler(ClickTypeHandler):
    def __init__(self, type_options: TypeOptions | None = None, **opts: typing.Any) -> None:
        super().__init__(click.Choice, type_options, **opts)

    def __call__(self, info: ParamInfo) -> HandlerResult[typing.Any] | None:
        annotation, meta = unwrap_annotation(info.annotation, resolve_generic=False)

        # Handle click / type opts.
        type_opts = dict(self.type_options)
        opts = dict(self.opts)
        for item in meta:
            if isinstance(item, TypeOptions):
                type_opts.update(item)
            elif isinstance(item, ClickOptions):
                opts.update(item)

        # Handle Literal[] / Enum types as a click.Choice (including as type aliases)
        if isinstance(annotation, type) and issubclass(annotation, enum.Enum):
            items = annotation
        elif typing.get_origin(annotation) is typing.Literal:
            items = typing.get_args(annotation)
        else:
            return None

        choicetype = click.Choice(items, **type_opts)
        return HandlerResult(info, [info.to_click_parameter(type=choicetype, **opts)])
