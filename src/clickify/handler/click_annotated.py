"""
Handle an Annotated[T, click.Argument()] style annotation as using the given parameter directly
"""

import click
import click.types

from clickify.func.paraminfo import ParamInfo
from clickify.handler.base import BaseParamHandler, FailedHandlerException, HandlerResult, NotHandledException
from clickify.typeutil import unwrap_annotation


class ParamNameMismatch(FailedHandlerException):
    """Raised where a parameter and the assigned name don't match."""


class ClickAnnotatedParameterHandler(BaseParamHandler):
    """Allow entirely replacing with a given Parameter."""

    def __call__(self, info: ParamInfo) -> HandlerResult:

        ann, meta = unwrap_annotation(info.annotation, resolve_alias=False, resolve_generic=False)
        for elem in meta:
            if isinstance(elem, click.Parameter):
                # Name needs to match to pair up with variable name.
                # TODO: Should we just set the name?  Check if this is valid.
                if elem.name != info.name:
                    raise ParamNameMismatch("Annotated parameter does not match variable name")
                return HandlerResult(info, [elem])

        raise NotHandledException()
