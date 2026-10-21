"""
A type handler takes a ParamInfo and returns a HandlerResult object,
containing the params and a conversion callback, or alternatively
returns None (or raises NotHandledException) to skip it and try next handler.

If it raises FailedHandlerException or another exception, the handling process
will fail and an error will be reported instead
(ie. use when the handler is the correct handler for the object, but something is wrong
Eg. a function handler where one of the params it uses is not handled.
"""

import typing
from abc import abstractmethod
from collections.abc import Callable

import click

from clickify.func.paraminfo import ParamInfo

if typing.TYPE_CHECKING:
    from clickify.handler.registry import HandlerRegistry

type ParamHandlerFunc = Callable[[ParamInfo], HandlerResult[typing.Any] | None]

type ParamPredicate = Callable[[ParamInfo], bool]


class NotHandledException(Exception):
    """Raised if handler doesn't handle the given type"""


class FailedHandlerException(Exception):
    """Raised if handler should handle the type, but an error occurs."""


class IgnoreParameterException(Exception):
    """Raised if the parameter should be ignored (ie. not provided at all to the callback)"""


class HandlerResult[T]:
    """Result of a handler lookup.

    Defines the click.Parameters, and a function that will retrieve and return the final result.
    Default behavior is to expect a single parameter with the paramname.

    NOTE: If overriding callback, bear in mind that the parameter provided may be the default
    value rather than a click-entered value.  In such cases, generally the value should not
    be modified, as it'll already be the final type.
    """

    def __init__(
        self,
        paraminfo: ParamInfo,
        params: list[click.Parameter],
        callback: Callable[[dict[str, typing.Any]], T] | None = None,
    ):
        self.paraminfo = paraminfo
        self.params = params
        self._callback = callback

    def callback(self, **opts: typing.Any) -> T:
        return self.callback_internal(opts)

    def callback_internal(self, opts: dict[str, typing.Any]) -> T:
        """Extract and options from the kwargs passed, and return new object created for the parameter.

        NOTE: In the case of a callback being provided, it is responsible for removing handled options.
        """
        if self._callback is not None:
            return self._callback(opts)
        if self.paraminfo.name not in opts:
            # There may be cases where a parameter isn't actually passed.
            # Eg. manually defined click parameters with expose_value=False
            # TODO: Should we do this selectively?  Ie. *only* for expose_value params,
            #  - any chance we could cover up bugs just by ignoring?
            raise IgnoreParameterException(f"Parameter not provided: {self.paraminfo.name}")
        return opts.pop(self.paraminfo.name)


# TODO: Simplify to just a callable?
class BaseParamHandler:
    """Handle converting a ParamInfo object into (potentially multiple) click.Parameters,
    and taking the click provided values and producing the final type.
    """

    @abstractmethod
    def __call__(self, info: ParamInfo) -> HandlerResult[typing.Any] | None:
        """Convert function paramdef to a HandlerResult with parameters and callback.

        If param cannot be handled, return None, or raise NotHandled.
        Otherwise, return HandlerResult
        """


class WrappingParamHandler(BaseParamHandler):
    """Wrap by modifying ParamInfo and re-looking up the modified annotation."""

    def __init__(self, registry: HandlerRegistry):
        self.registry = registry

    def __call__(self, info: ParamInfo) -> HandlerResult[typing.Any] | None:
        converted_info = self.convert_param(info)
        if converted_info is None:
            return None

        res = self.registry.handle_param(converted_info)
        return res

    @abstractmethod
    def convert_param(self, info: ParamInfo) -> ParamInfo | None:
        """Implement in subclass to convert ParamInfo to another version.
        Returns None or raise NotHandled() if not handled.
        """
