import typing
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

type HandlerDecorator[T: SimpleHandlerFunction | ParamHandler] = Callable[[T], T]


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

    # def register_annotation(self, annotation: AnnotationType, handler: ParamHandler | SimpleHandlerFunction):
    #     """Register a handler for an exact match of the given annotation, ignoring only Annoated[] .

    #     Ie. register_annotation(list[int]) will not match `list` `list[Any]` or `list[bool]`, but will match
    #     `Annotated[list[int], ...]`

    #     """
    #     if not isinstance(handler, ParamHandler):
    #         handler = SimpleParamHandler(handler)

    #     self.handlers.append((match_annotation(annotation), handler))

    @typing.overload
    def register_annotation(self, annotation: AnnotationType) -> HandlerDecorator: ...

    @typing.overload
    def register_annotation(
        self, annotation: AnnotationType, handler: ParamHandler | SimpleHandlerFunction
    ) -> None: ...

    def register_annotation(
        self, annotation: AnnotationType, handler: ParamHandler | SimpleHandlerFunction | None = None
    ) -> HandlerDecorator | None:
        """Decorator to register type handler.

        Handler will match on the *exact* type annotation provided.
        May be used as a decorator, or directly by specifying the handler.
        Eg.

            registry.register_annotation(int, MyHandler())

        or:

            @registry.register_annotation(int)
            def int_handler(param: ParamInfo) -> click.Parameter:
                return param.to_click_parameter(type=click.INT)
        """
        return self.register_handler(match_annotation(annotation), handler=handler)

    @typing.overload
    def register_handler(self, predicate: ParamPredicate = always_check, handler: None = None) -> HandlerDecorator: ...

    @typing.overload
    def register_handler(
        self, predicate: ParamPredicate = always_check, *, handler: ParamHandler | SimpleHandlerFunction
    ) -> None: ...

    @typing.overload
    def register_handler(self, predicate: ParamPredicate, handler: ParamHandler | SimpleHandlerFunction) -> None: ...

    def register_handler(
        self,
        predicate: ParamPredicate = always_check,
        handler: SimpleHandlerFunction | ParamHandler | None = None,
    ) -> HandlerDecorator | None:
        """Register a general handler, optionally requiring a predicate to check before trying.

        May be used as a decorator, or directly by providing the handler.  Eg.

            registry.register_handler(predicate_func, SomeHandler())

        Or:

            @registry.register_handler()
            def func(info: ParamInfo): ...

        Arguments:
            predicate:
                Optionally a check on the parameter as to whether this handler applies.
                If omitted, will always try the handler, skipping only if it raises NotHandled
            handler:
                The handler, or a function returning a Parameter.
        """

        def decorator[T: SimpleHandlerFunction | ParamHandler](func: T) -> T:
            handler = func if isinstance(func, ParamHandler) else SimpleParamHandler(func)
            self.handlers.append((predicate, handler))
            return func

        if handler is None:
            return decorator
        else:
            # Direct register
            decorator(handler)
            return None

    def get_param_value(self, info: ParamInfo, args: dict[str, typing.Any]) -> typing.Any:
        for pred, handler in self.handlers:
            if pred(info):
                try:
                    res = handler.get_value(info, args)
                    print(f"Resolved {info.name} to {res} using {handler}: {pred(info)}")
                    return res
                except NotHandled:
                    pass

        raise UnhandledAnnotationException(f"No handlers for param {info.name} of type {info.annotation}")

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
