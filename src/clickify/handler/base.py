import typing
from abc import abstractmethod
from collections.abc import Callable

import click

from clickify.func.paraminfo import ParamInfo

if typing.TYPE_CHECKING:
    from clickify.handler.registry import HandlerRegistry

type ParamPredicate = Callable[[ParamInfo], bool]
type SimpleHandlerFunction = Callable[[ParamInfo], click.Parameter | None]


class NotHandledException(Exception):
    """Raise if handler doesn't handle the given type"""


class HandlerResult[T]:
    """Result of a handler lookup.

    Defines the click.Parameters, and a function that will retrieve and return the final result.
    Default behavior is to expect a single parameter with the paramname.
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
        if self._callback is not None:
            return self._callback(opts)
        return opts[self.paraminfo.name]


class ParamHandler:
    """Handle converting a ParamInfo object into (potentially multiple) click.Parameters,
    and taking the click provided values and producing the final type.
    """

    @abstractmethod
    def get(self, info: ParamInfo) -> HandlerResult | None:
        """Convert function paramdef to a HandlerResult with parameters and callback.

        If param cannot be handled, return None, or raise NotHandled.
        Otherwise, return HandlerResult
        """


class SimpleParamHandler(ParamHandler):
    """Simple case where implemented by simple callback function producing a single click.Parameter"""

    def __init__(self, func: SimpleHandlerFunction):
        self.func = func

    def get(self, info: ParamInfo) -> HandlerResult | None:
        # TODO: Add .check?
        param = self.func(info)
        # TODO: Allow it to return HandlerResult directly?
        if param is not None:
            return HandlerResult(info, [param])
        return None


class WrappingParamHandler(ParamHandler):
    """Wrap by modifying ParamInfo and re-looking up the annotation."""

    def __init__(self, registry: HandlerRegistry):
        self.registry = registry

    def get(self, info: ParamInfo) -> HandlerResult | None:
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
