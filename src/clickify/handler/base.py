import typing
from abc import abstractmethod
from collections.abc import Callable

import click

from clickify.funcinfo import ParamInfo

type ParamPredicate = Callable[[ParamInfo], bool]
type SimpleHandlerFunction = Callable[[ParamInfo], click.Parameter]


class NotHandled(Exception):
    """Raise if handler doesn't handle the given type"""


class ParamHandler:
    """Handle converting a ParamInfo object into (potentially multiple) click.Parameters,
    and taking the click provided values and producing the final type.
    """

    def is_handled(self, info: ParamInfo) -> bool:
        """Does this handler handle the given parameter"""
        return True

    @abstractmethod
    def get_params(self, info: ParamInfo) -> list[click.Parameter]:
        """Convert function paramdef to click Parameter(s)

        If param cannot be handled, raise NotHandled.
        Otherwise, return iterable of click.Parameters produced.
        """

    @abstractmethod
    def get_value(self, info: ParamInfo, args: dict[str, typing.Any]):
        """Get value from args"""


class SimpleParamHandler(ParamHandler):
    """Simple case where implemented by simple function producing a single click.Parameter"""

    def __init__(self, func: SimpleHandlerFunction):
        self.func = func

    def get_params(self, info: ParamInfo) -> list[click.Parameter]:
        return [self.func(info)]

    def get_value(self, info: ParamInfo, args: dict[str, typing.Any]):
        return args.get(info.name)
