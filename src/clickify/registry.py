import bisect
import inspect
import operator
import typing
from collections.abc import Callable

from clickify.func.paraminfo import ParamInfo
from clickify.handler.base import HandlerResult, NotHandledException, ParamHandlerFunc, ParamPredicate
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
    resolve_alias: bool = False,
    resolve_generic: bool = False,
    is_argument: bool | None = None,
    extra_predicate: ParamPredicate | None = None,
    allow_subclass: bool = False,
) -> ParamPredicate:
    """Construct a match predicate for an annotation.

    Will match if the annotation is equal (according to equality) with the registered annotation
    (ie. not a subclass check etc), but will not include Annotated[...] and optionally
    may ignore type aliasing.
    If allow_subclass is set, will instead check issubclass (requires that the type is a class, rather
    than other typeform, after resolving alias etc.)

    Arguments:
        annotation: Annotation to match
        resolve_alias:
            Don't treat a type alias as a different type from the aliased type.
            Ie. `type Foo = str` will match a `str` annotation.
        resolve_generic:
            Resolve any generics to their base type before comparison.
            Ie. list[str] would match list[int] or list
        is_argument:
            If True/False, only match if the parameter is an argument.
            If None, matches either way.
        allow_subclass:
            Compare with issubclass(registered_type, func_type) rather than equality.
            (Ie. registering SubClass will match a function requesting BaseClass)
            Note: resolve_alias and resolve_generic should probably be True for this case,
            as typeform must be a type, rather than alias/other typeform to compare.
        extra_predicate:
            Any extra predicate function taking the paraminfo object.

    """
    _orig = annotation
    annotation, _meta = unwrap_annotation(annotation, resolve_alias=resolve_alias, resolve_generic=resolve_generic)

    def match(info: ParamInfo) -> bool:
        # Require exact match.
        if is_argument is not None and info.is_argument != is_argument:
            return False

        param_annotation, _meta = unwrap_annotation(
            info.annotation, resolve_alias=resolve_alias, resolve_generic=resolve_generic
        )

        if allow_subclass:
            match = (
                isinstance(param_annotation, type)
                and isinstance(annotation, type)
                and issubclass(annotation, param_annotation)
            )
        else:
            match = param_annotation == annotation

        return match and ((extra_predicate is None) or extra_predicate(info))

    return match


def always_check(info: ParamInfo) -> bool:
    return True


# TOOD: Want layered checks here.
# Eg. Annotations take priority, then exact match, then others etc.
# Maybe chain registries?  Have list of checks at a given priority?
# Just have flat list of checks instead of using dict etc.
class HandlerRegistry:
    """Allow registering handlers for converting argument definition into click.Parameter(s).

    Handlers are checked in sequence in order of priority, then registration.
    A predicate may be associated with each that determines whether to attempt it,
    otherwise the handler is called and if it returns a HandlerResult, used.
    If it returns None or raises NotHandledException, the next handler in the list is tried
    until one is successful, or raises FailedHandlerException (raised for a type it *should* handle,
    but has an error that prevents it)
    """

    def __init__(self) -> None:
        # priority, predicate, handler
        self.handlers: list[tuple[int, ParamPredicate, ParamHandlerFunc]] = []

    @typing.overload
    def register(
        self,
        *,
        annotation: AnnotationType | Inferred = Inferred.value,
        is_argument: bool | None = None,
        resolve_alias: bool = False,
        resolve_generic: bool = False,
        allow_subclass: bool = False,
        priority: int = DEFAULT_PRIORITY,
    ) -> Decorator[AnyCallable]: ...

    @typing.overload
    def register(
        self,
        func: AnyCallable,
        *,
        annotation: AnnotationType | Inferred = Inferred.value,
        is_argument: bool | None = None,
        resolve_alias: bool = False,
        resolve_generic: bool = False,
        allow_subclass: bool = False,
        priority: int = DEFAULT_PRIORITY,
    ) -> None: ...

    def register(
        self,
        func: AnyCallable | None = None,
        *,
        annotation: AnnotationType | Inferred = Inferred.value,
        is_argument: bool | None = None,
        resolve_alias: bool = False,
        resolve_generic: bool = False,
        allow_subclass: bool = False,
        priority: int = DEFAULT_PRIORITY,
        # predicate
    ) -> Decorator[AnyCallable] | None:
        """Decorator to register a function that will handle a particular annotation.

        When this annotation occurs in a command, the parameters of the function will be extended with any
        additional parameters defined by `func`.  These parameters will then be passed to the function,
        and the return value used as the value.

        Arguments:
            func: The function to use.
            annotation:
                The annotation to register.
                If not provided, will be inferred from the return type of the function.
            is_argument:
                If non-None, only match where the param is an Argument type (when True) or Option type (when False)
            resolve_alias:
                Treat an aliased type as equivalent to any type matching/aliased to the underlying type
            resolve_generic:
                Treat a generic type as equivalent to the origin type (ie. list[str] treated as list)
            allow_subclass:
                Match subclasses of the type (after resolve_alias/resolve_generic applied), rather than just equality.
            priority:
                Determines whether this will be tried before or after other items.
                Lower values are tried first, only trying items with higher priority if these do not handle the item.
                For items with the same priority, items are tried in the order they were added.
        """

        def decorator[T: Callable[..., typing.Any]](func: T) -> T:
            handler = FunctionHandler(self, func)
            handled_annotation = handler.funcinfo.return_annotation if isinstance(annotation, Inferred) else annotation

            if handled_annotation is inspect._empty:
                raise Exception("No annotation specified, and function does not provide a return annotation")

            self.add_handler(
                handler,
                predicate=match_annotation(
                    handled_annotation,
                    is_argument=is_argument,
                    resolve_alias=resolve_alias,
                    resolve_generic=resolve_generic,
                    allow_subclass=allow_subclass,
                ),
                priority=priority,
            )
            return func

        if func is not None:
            decorator(func)
            return None

        return decorator

    def add_handler(
        self,
        handler: ParamHandlerFunc,
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

    def handle_param(self, info: ParamInfo) -> HandlerResult[typing.Any]:
        """Find handler for parameter, and return result.

        If not found, raises NotHandledException
        """
        for _pri, pred, handler in self.handlers:
            if pred(info):
                try:
                    res = handler(info)
                    if res is not None:
                        return res
                except NotHandledException:
                    pass

        raise NotHandledException(f"No handler for param: {info} found in registry.")
