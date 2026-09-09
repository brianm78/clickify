from collections.abc import Callable

import click

from clickify.func.paraminfo import ParamInfo
from clickify.handler.base import (
    NotHandled,
    ParamHandler,
    ParamPredicate,
    SimpleHandlerFunction,
    SimpleParamHandler,
)
from clickify.typeutil import unwrap_annotation
from clickify.utils import AnnotationType


class UnhandledAnnotationException(Exception):
    """Raised if no handlers handle the parameter type."""

    pass


def match_annotation(annotation: AnnotationType, ignore_annotated: bool = True) -> Callable[[ParamInfo], bool]:
    """Does the annotation exactly match the registered type (ignoring Annotated[])"""
    if ignore_annotated:
        annotation, _meta = unwrap_annotation(annotation, resolve_alias=False, resolve_generic=False)

    def match(info: ParamInfo) -> bool:
        # Require exact match.
        return info.annotation == annotation

    return match


def always_check(info: ParamInfo) -> bool:
    return True


# TOOD: Want layered checks here.
# Eg. Annotations take priority, then exact match, then others etc.
# Maybe chain registries?  Have list of checks at a given priority?
# Just have flat list of checks instead of using dict etc.
class HandlerRegistry:
    """Allow registering handlers for converting argument definition into click.Parameter(s).

    Handlers are checked in sequence in order of registration.
    They may be registered with either:
        register_annotation:
            Associates an exact annotation

    Handlers may be looked up as:
        - exact match of annotation (highest priority)
        - a predicate that determines
    """

    def __init__(self):
        # TODO: Specify priority?
        self.handlers: list[tuple[ParamPredicate, ParamHandler]] = []

    def register_annotation(self, annotation: AnnotationType, handler: ParamHandler | SimpleHandlerFunction):
        """Register a handler for an exact match of the given annotation, ignoring only Annoated[] .

        Ie. register_annotation(list[int]) will not match `list` `list[Any]` or `list[bool]`, but will match
        `Annotated[list[int], ...]`

        """
        if not isinstance(handler, ParamHandler):
            handler = SimpleParamHandler(handler)

        self.handlers.append((match_annotation(annotation), handler))

    def register_handler(self, handler: ParamHandler, predicate: ParamPredicate = always_check):
        """Register a general handler, optionally requiring a predicate to check before trying."""
        self.handlers.append((predicate, handler))

    def get_params(self, info: ParamInfo) -> list[click.Parameter]:
        """Convert paraminfo into click.Parameter(s)

        If no handlers found for the parameter, raise UnhandledAnnotationException
        """
        for pred, handler in self.handlers:
            if pred(info):
                try:
                    res = list(handler.get_params(info))
                    return res
                except NotHandled:
                    pass

        # Nothing handled it.
        raise UnhandledAnnotationException(f"No handlers for param {info.name} of type {info.annotation}")
