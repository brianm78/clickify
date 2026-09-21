"""
Handle literal / enum types as a click.Choice
"""

import enum
import typing
from collections.abc import Callable

import click
import click.types

from clickify.func.paraminfo import ParamInfo
from clickify.handler.base import HandlerResult, ParamHandler
from clickify.typeutil import unwrap_annotation


class ChoiceTypeHandler(ParamHandler):
    def get(self, info: ParamInfo) -> HandlerResult | None:
        annotation, _meta = unwrap_annotation(info.annotation, resolve_generic=False)

        callback: Callable[dict[str, typing.Any], typing.Any] | None = None
        # Handle Literal[] / Enum types as a click.Choice (including as type aliases)
        if isinstance(annotation, type) and issubclass(annotation, enum.Enum):
            choicetype = click.Choice(e.name for e in annotation)

            def callback(opts: dict[str, typing.Any]):
                val = opts[info.name]
                return annotation[val]

        elif typing.get_origin(annotation) is typing.Literal:
            choicetype = click.Choice(typing.get_args(annotation))
            callback = None
        else:
            return None

        return HandlerResult(info, [info.to_click_parameter(type=choicetype)], callback)
