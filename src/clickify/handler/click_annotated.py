"""
Handle an Annotated[T, click.Argument()] style annotation as using the given parameter directly
"""

import click
import click.types

from clickify.func.paraminfo import ParamInfo
from clickify.handler.base import HandlerResult, NotHandledException, ParamHandler
from clickify.typeutil import unwrap_annotation


class ParamNameMismatch(Exception):
    """Raised where a parameter and the assigned name don't match."""


class ClickAnnotatedParameterHandler(ParamHandler):
    """Allow entirely replacing with a given Parameter."""

    def get(self, info: ParamInfo) -> HandlerResult:
        ann, meta = unwrap_annotation(info.annotation, False, False)
        for elem in meta:
            if isinstance(elem, click.Parameter):
                # Name needs to match to pair up with variable name.
                # TODO: Should we just set the name?  Check if this is valid.
                if elem.name != info.name:
                    raise ParamNameMismatch("Annotated parameter does not match variable name")
                return HandlerResult(info, [elem])

        raise NotHandledException()
