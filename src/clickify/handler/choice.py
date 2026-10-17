"""
Handle literal / enum types as a click.Choice
"""

import enum
import typing
from collections.abc import Callable

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

    def __call__(self, info: ParamInfo) -> HandlerResult | None:
        annotation, meta = unwrap_annotation(info.annotation, resolve_generic=False)

        # Handle click / type opts.
        type_opts = dict(self.type_options)
        opts = dict(self.opts)
        for item in meta:
            if isinstance(item, TypeOptions):
                type_opts.update(item)
            elif isinstance(item, ClickOptions):
                opts.update(item)

        callback: Callable[[dict[str, typing.Any]], typing.Any] | None = None
        # Handle Literal[] / Enum types as a click.Choice (including as type aliases)
        if isinstance(annotation, type) and issubclass(annotation, enum.Enum):
            choicetype = click.Choice([e.name for e in annotation], **type_opts)

            def callback(opts: dict[str, typing.Any]):
                val = opts[info.name]
                # Note: the value may be set to the default by this point, which we
                # don't want to convert (it'll already be the final value)

                if isinstance(val, str):
                    return annotation[val]
                click.Choice

        elif typing.get_origin(annotation) is typing.Literal:
            choicetype = click.Choice(typing.get_args(annotation), **type_opts)
            callback = None
        else:
            return None

        return HandlerResult(info, [info.to_click_parameter(type=choicetype, **opts)], callback)
