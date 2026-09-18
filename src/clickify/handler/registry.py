import inspect
import typing
from collections.abc import Callable

from clickify.func.paraminfo import ParamInfo
from clickify.handler.base import HandlerResult, NotHandledException, ParamHandler, ParamPredicate
from clickify.handler.function import FunctionHandler
from clickify.types import Inferred
from clickify.typeutil import unwrap_annotation
from clickify.utils import AnnotationType

type HandlerDecorator[T: Callable[..., typing.Any]] = Callable[[T], T]


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

    @typing.overload
    def register(
        self, *, annotation: AnnotationType | Inferred = Inferred.value, multi_arg: bool | Inferred = Inferred.value
    ) -> HandlerDecorator: ...

    @typing.overload
    def register(
        self,
        func: typing.Callable[..., typing.Any],
        *,
        annotation: AnnotationType | Inferred = Inferred.value,
        multi_arg: bool | Inferred = Inferred.value,
    ) -> None: ...

    def register(
        self,
        func: typing.Callable[..., typing.Any] | None = None,
        *,
        annotation: AnnotationType | Inferred = Inferred.value,
        multi_arg: bool | Inferred = Inferred.value,
        # predicate
    ) -> HandlerDecorator | None:
        """Decorator to register a function that will handle a particular annotation.

        The handler function will lookup the type of any parameters, invoke the function,
        and return the result of its value.

        If the function takes only a single parameter, it will use the decls, helptext and name
        taken from where it is used.
        Otherwise, the function signature and docstring will be used to add new parameters
        in any CLI function that uses them.  These parameters may not be renamed / modified by
        that caller.  Pass multi_arg = True to force this mode to be used even for single
        parameter functions.


        Arguments:
            func: The function to use
            annotation:
                The annotation to register.
                If not provided, will be inferred from the return type of the function.
            mult_iarg:
                Force multiargument / simple mode
                If not provided, will be inferred based on whether the function takes a single argument.
        """

        def decorator[T: Callable[..., typing.Any]](func: T) -> T:
            handler = FunctionHandler(self, func, multi_arg)
            handled_annotation = handler.funcinfo.return_annotation if isinstance(annotation, Inferred) else annotation

            if handled_annotation is inspect._empty:
                raise Exception("No annotation specified, and function does not provide a return annotation")

            self.register_handler(handler, predicate=match_annotation(handled_annotation))
            return func

        if func is not None:
            decorator(func)
            return None

        return decorator

    def register_handler(self, handler: ParamHandler, predicate: ParamPredicate = always_check) -> None:
        """Register a general handler, optionally requiring a predicate to check before trying.

        Arguments:
            handler:
                The handler
            predicate:
                Optionally a check on the parameter as to whether this handler applies.
                If omitted, will always try the handler, skipping only if it raises NotHandled
        """
        self.handlers.append((predicate, handler))

    def register_handler_by_annotation(self, annotation: AnnotationType, handler: ParamHandler):
        self.register_handler(handler, predicate=match_annotation(annotation))

    def handle_param(self, info: ParamInfo) -> HandlerResult:
        """Find handler for parameter, and return result.

        If not found, raises NotHandledException
        """
        for pred, handler in self.handlers:
            if pred(info):
                try:
                    res = handler.get(info)
                    if res is not None:
                        return res
                except NotHandledException:
                    pass

        raise NotHandledException(f"No handler for param: {info} found in registry.")
