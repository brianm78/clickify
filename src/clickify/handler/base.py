import typing
from abc import abstractmethod
from collections.abc import Callable

import click

from clickify.func.paraminfo import ParamInfo

if typing.TYPE_CHECKING:
    from clickify.handler.registry import HandlerRegistry

type ParamPredicate = Callable[[ParamInfo], bool]
type SimpleHandlerFunction = Callable[[ParamInfo], click.Parameter]


class NotHandled(Exception):
    """Raise if handler doesn't handle the given type"""


class ParamHandler:
    """Handle converting a ParamInfo object into (potentially multiple) click.Parameters,
    and taking the click provided values and producing the final type.
    """

    @abstractmethod
    def get_params(self, info: ParamInfo) -> list[click.Parameter]:
        """Convert function paramdef to click Parameter(s)

        If param cannot be handled, raise NotHandled.
        Otherwise, return iterable of click.Parameters produced.
        """

    # TODO: This is kind of clunky, and redoes work.
    # Need to
    def get_value(self, info: ParamInfo, args: dict[str, typing.Any]) -> typing.Any:
        """Get value from args"""
        return args.get(info.name)


class SimpleParamHandler(ParamHandler):
    """Simple case where implemented by simple function producing a single click.Parameter"""

    def __init__(self, func: SimpleHandlerFunction):
        self.func = func

    def get_params(self, info: ParamInfo) -> list[click.Parameter]:
        """Construct potentially multiple click parameters"""
        return [self.func(info)]


class WrappingParamHandler(ParamHandler):
    """Wrap by modifying ParamInfo and re-looking up the annotation."""

    def __init__(self, registry: HandlerRegistry):
        self.registry = registry

    @abstractmethod
    def convert_param(self, info: ParamInfo) -> ParamInfo | None:
        """Implement in subclass to convert ParamInfo to another version.
        Returns None or raise NotHandled() if not handled.
        """

    def get_params(self, info: ParamInfo) -> list[click.Parameter]:
        converted_info = self.convert_param(info)
        if converted_info is None:
            raise NotHandled()
        return self.registry.get_params(converted_info)

    def get_value(self, info: ParamInfo, args: dict[str, typing.Any]) -> typing.Any:
        converted_info = self.convert_param(info)
        if converted_info is None:
            raise NotHandled()
        return self.registry.get_param_value(converted_info, args)
