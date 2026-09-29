import bisect
import inspect
import operator
import typing
from collections.abc import Callable

from clickify.func.paraminfo import ParamInfo
from clickify.handler.base import HandlerResult, NotHandledException, ParamHandler, ParamPredicate
from clickify.handler.function import FunctionHandler
from clickify.types import AnyCallable, Decorator, Inferred
from clickify.typeutil import unwrap_annotation
from clickify.utils import AnnotationType

# User-added items will take priority over builtins.
# Otherwise, ordered by definition order (earliest tried first)
BUILTIN_PRIORITY = 100
DEFAULT_PRIORITY = 0


def match_annotation(
    annotation: AnnotationType,
    ignore_alias: bool = False,
    is_argument: bool | None = None,
    extra_predicate: ParamPredicate | None = None,
) -> ParamPredicate:
    """Construct a match predicate for an annotation.

    Will match if the annotation is equal (according to equality) with the registered annotation
    (ie. not a subclass check etc), but will not include Annotated[...] and optionally
    may ignore type aliasing.

    Arguments:
        annotation: Annotation to match
        ignore_alias:
            Don't treat a type alias as a different type from the aliased type.
            Ie. `type Foo = str` will match a `str` annotation.
        is_argument:
            If True/False, only match if the parameter is an argument.
            If None, matches either way.
        extra_predicate:
            Any extra predicate function taking the paraminfo object.

    """
    _orig = annotation
    annotation, _meta = unwrap_annotation(annotation, resolve_alias=ignore_alias, resolve_generic=False)

    def match(info: ParamInfo) -> bool:
        # Require exact match.
        if is_argument is not None and info.is_argument != is_argument:
            return False

        param_annotation, _meta = unwrap_annotation(info.annotation, resolve_alias=ignore_alias, resolve_generic=False)

        return (param_annotation == annotation) and ((extra_predicate is None) or extra_predicate(info))

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

    def __init__(self) -> None:
        # priority, predicate, handler
        self.handlers: list[tuple[int, ParamPredicate, ParamHandler]] = []

    @typing.overload
    def register(
        self,
        *,
        annotation: AnnotationType | Inferred = Inferred.value,
        is_argument: bool | None = None,
        multi_arg: bool | Inferred = Inferred.value,
        priority: int = DEFAULT_PRIORITY,
    ) -> Decorator: ...

    @typing.overload
    def register(
        self,
        func: AnyCallable,
        *,
        annotation: AnnotationType | Inferred = Inferred.value,
        is_argument: bool | None = None,
        multi_arg: bool | Inferred = Inferred.value,
        priority: int = DEFAULT_PRIORITY,
    ) -> None: ...

    def register(
        self,
        func: AnyCallable | None = None,
        *,
        annotation: AnnotationType | Inferred = Inferred.value,
        is_argument: bool | None = None,
        ignore_alias: bool = False,
        multi_arg: bool | Inferred = Inferred.value,
        priority: int = DEFAULT_PRIORITY,
        # predicate
    ) -> Decorator | None:
        """Decorator to register a function that will handle a particular annotation.

        The handler function will lookup the type of any parameters, invoke the function,
        and return the result of its value.  Use this for cases where a parameter can be transformed
        into one or more other handled parameter types.

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
            is_argument:
                If non-None, only match where the param is an Argument type (when True) or Option type (when False)
            ignore_alias:
                Treat an aliased type as equivalent to any type matching/aliased to the underlying type
            multi_arg:
                Specify whether multiargument mode is used.
                If not provided, will be inferred based on whether the function takes a single argument.
            priority:
                Determines whether this will be tried before or after other items.
                Lower values are tried first, only trying items with higher priority if these do not handle the item.
                For items with the same priority, items are tried in the order they were added.
        """

        def decorator[T: Callable[..., typing.Any]](func: T) -> T:
            handler = FunctionHandler(self, func, multi_arg)
            handled_annotation = handler.funcinfo.return_annotation if isinstance(annotation, Inferred) else annotation

            if handled_annotation is inspect._empty:
                raise Exception("No annotation specified, and function does not provide a return annotation")

            self.register_handler(
                handler,
                predicate=match_annotation(handled_annotation, is_argument=is_argument, ignore_alias=ignore_alias),
                priority=priority,
            )
            return func

        if func is not None:
            decorator(func)
            return None

        return decorator

    def register_handler(
        self,
        handler: ParamHandler,
        predicate: ParamPredicate = always_check,
        priority: int = DEFAULT_PRIORITY,
    ) -> None:
        """Register a ParamHandler, optionally requiring a predicate to check before trying.

        Arguments:
            handler:
                The handler
            predicate:
                Optionally a check on the parameter as to whether this handler applies.
                If omitted, will always try the handler, skipping only if it raises NotHandled
            priority:
                Determines order handlers are tried.  Lower values are tried first.
                Items with same priority are tried in order of definition.
        """
        bisect.insort_right(self.handlers, (priority, predicate, handler), key=operator.itemgetter(0))

    def handle_param(self, info: ParamInfo) -> HandlerResult:
        """Find handler for parameter, and return result.

        If not found, raises NotHandledException
        """
        for _pri, pred, handler in self.handlers:
            if pred(info):
                try:
                    res = handler.get(info)
                    if res is not None:
                        return res
                except NotHandledException:
                    pass

        raise NotHandledException(f"No handler for param: {info} found in registry.")
