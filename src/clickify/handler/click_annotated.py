"""
Handle an Annotated[T, click.Option()] style annotation as using the given parameter
"""

import typing
from dataclasses import replace

import click
import click.types

from clickify.func.paraminfo import ParamInfo
from clickify.handler.base import HandlerResult, NotHandledException, ParamHandler, WrappingParamHandler
from clickify.handler.registry import HandlerRegistry
from clickify.typeutil import unwrap_annotation


class ParamNameMismatch(Exception):
    """Raised where a parameter and the assigned name don't match."""


# TODO: Allow setting decls, is_argument etc, click class (eg. subclass of Argument/Option)
# Maybe also have add_decls=[] vs replace_decls=[]
# (Or short_decls / long_decls)
class ClickOptions:
    def __init__(self, **kwargs: typing.Any):
        """Augment the parameter to always pass the provided click options.
        Only valid for builtin click option types.
        Eg.

            val: Annotated[int, ClickOpts(type=IntRange(0, 20)] = 0
        """
        # TODO: Allow overriding is_argument / decls / others?
        self.opts = kwargs


class ClickAnnotatedOptionsHandler(WrappingParamHandler):
    """Allow specifying options that override the default handler"""

    def __init__(self, registry: HandlerRegistry):
        self.registry = registry

    def convert_param(self, info: ParamInfo) -> ParamInfo | None:
        ann, meta = unwrap_annotation(info.annotation, False, False)
        for elem in meta:
            if isinstance(elem, ClickOptions):
                return replace(info, annotation=ann).with_click_overrides(**elem.opts)

        return None


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
