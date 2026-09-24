import itertools
import typing
from collections.abc import Callable
from dataclasses import replace

import click

from clickify.func import FuncInfo, ParamInfo
from clickify.handler.base import HandlerResult, ParamHandler
from clickify.types import Inferred

if typing.TYPE_CHECKING:
    from clickify.handler.registry import HandlerRegistry


class FunctionHandler[T](ParamHandler):
    """Provide args derived from a function signature, then call the function with them to construct result.

    There are two modes of operation:

        1. Simple: Accepts only a single parameter.  Only the type of this parameter is retained
           when being handled, with the rest(decls, help, argtype etc) coming from where it is used.

        2. Multi-argument.  Accepts multiple parameters, but ignores the context where the
           parameter is used, and creates a new set of parameters based on the handler function signature
           and docstring.  These parameters are looked up by type as normal.
    """

    def __init__(
        self,
        registry: HandlerRegistry,
        func: Callable[..., T],
        multi_arg: bool | Inferred = Inferred.value,
        override_params: dict[str, click.Parameter] | None = None,
    ) -> None:
        self.registry = registry
        self.funcinfo = FuncInfo.from_func(func)
        self.multi_arg = len(self.funcinfo.params) != 1 if isinstance(multi_arg, Inferred) else multi_arg

        # Get click decorator annotations:
        decorator_params = getattr(func, "__click_params__", [])
        if decorator_params:
            self.override_params = {p.name: p for p in decorator_params}
        else:
            self.override_params = {}

        if override_params:
            # Passed in parameters take priority over decorator annotation
            self.override_params.update(override_params)

    def _handle_param(self, info: ParamInfo) -> HandlerResult:
        # Allow arguments / click annotations to override signature.
        if info.name in self.override_params:
            return HandlerResult(info, [self.override_params[info.name]])

        return self.registry.handle_param(info)

    def get(self, info: ParamInfo) -> HandlerResult | None:
        """We ignore paraminfo, and create a new set of parameters here."""

        # TODO: allow prefixing opts with paraminfo argname?
        if self.multi_arg:
            handler_results = [self._handle_param(paraminfo) for paraminfo in self.funcinfo.params]

        else:
            # The function annotation only provides the type.  The rest comes from the signature of the command
            # function (ie. name, decls, default etc)
            paraminfo = replace(info, annotation=self.funcinfo.params[0].annotation)
            handler_results = [self._handle_param(paraminfo)]

        def callback(opts: dict[str, typing.Any]) -> T:
            resolved_params: dict[str, typing.Any] = {}
            for h in handler_results:
                resolved_params[h.paraminfo.name] = h.callback(**opts)
            return self.funcinfo.invoke(**resolved_params)

        params = list(itertools.chain.from_iterable(h.params for h in handler_results))

        return HandlerResult(info, params, callback)
