import itertools
import typing
from collections.abc import Callable

from clickify.func import FuncInfo, ParamInfo
from clickify.handler.base import HandlerResult
from clickify.handler.registry import HandlerRegistry, ParamHandler


class FunctionHandler[T](ParamHandler):
    """Provide args derived from function signature, and use to construct result.

    Note: paraminfo is ignored: will create new parameters based on function signature
    """

    def __init__(self, registry: HandlerRegistry, func: Callable[..., T]) -> None:
        self.registry = registry
        self.funcinfo = FuncInfo.from_func(func)

    def get(self, info: ParamInfo) -> HandlerResult | None:
        """We ignore paraminfo, and create a new set of parameters here."""

        # NOTE: This means we ignore stuff like nargs=-1 etc.
        # So using in *args, ot list[Type] will fail...

        params = []
        # TODO: allow prefixing opts with paraminfo argname?
        #
        handler_res = [self.registry.handle_param(paraminfo) for paraminfo in self.funcinfo.params]
        if any(x is None for x in handler_res):
            return None

        handler_results: list[HandlerResult] = typing.cast(list[HandlerResult], handler_res)

        def callback(opts: dict[str, typing.Any]) -> T:
            resolved_params: dict[str, typing.Any] = {}
            for h in handler_results:
                resolved_params[h.paraminfo.name] = h.callback(**opts)
            return self.funcinfo.invoke(**resolved_params)

        params = list(itertools.chain.from_iterable(h.params for h in handler_results))

        return HandlerResult(info, params, callback)

    # def get_value(self, info: ParamInfo | None, args: dict[str, typing.Any]) -> T:
    #     resolved_args = {}
    #     for paraminfo in self.funcinfo.params:
    #         try:
    #             resolved_args[paraminfo.name] = self.registry.get_param_value(paraminfo, args)
    #         except Exception as ex:
    #             print(ex)

    #     return self.funcinfo.invoke(**resolved_args)
