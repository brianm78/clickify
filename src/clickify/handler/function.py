import typing
from collections.abc import Callable

import click

from clickify.funcinfo import FuncInfo, ParamInfo
from clickify.handler.registry import HandlerRegistry


class FunctionHandler[T]:
    def __init__(self, registry: HandlerRegistry, func: Callable[..., T]) -> None:
        self.registry = registry
        self.funcinfo = FuncInfo.from_func(func)

    def get_params(self, paraminfo: ParamInfo) -> list[click.Parameter]:
        """We ignore paraminfo, and create a new set of parameters here."""

        params = []
        # TODO: allow prefixing opts with paraminfo argname?
        for paraminfo in self.funcinfo.params:
            # Use corresponding handler for each type
            params += self.registry.get_params(paraminfo)

        # TODO: Validate duplicates here?
        return params

    def get_value(self, args: dict[str, typing.Any]) -> T:
        return self.funcinfo.invoke(**args)
