import dataclasses
import itertools
import typing

from clickify.func.docinfo import DocInfo
from clickify.func.paraminfo import ParamInfo
from clickify.handler.base import HandlerResult, ParamHandler
from clickify.handler.registry import HandlerRegistry
from clickify.typeutil import unwrap_annotation


class DataclassParamHandler(ParamHandler):
    """Construct a dataclass from its members, using docstring similarly to function docstring"""

    def __init__(self, registry: HandlerRegistry):
        self.registry = registry

    def get(self, info: ParamInfo) -> HandlerResult | None:
        dataclass_cls, meta = unwrap_annotation(info.annotation, resolve_alias=True, resolve_generic=False)
        if not dataclasses.is_dataclass(dataclass_cls):
            return None

        docinfo = DocInfo.from_doc(dataclass_cls.__doc__)

        handler_results = [
            self.registry.handle_param(ParamInfo.from_dataclass_field(field, docinfo))
            for field in dataclasses.fields(dataclass_cls)
        ]

        def callback(opts: dict[str, typing.Any]) -> typing.Any:
            resolved_params: dict[str, typing.Any] = {}
            for h in handler_results:
                resolved_params[h.paraminfo.name] = h.callback(**opts)

            return dataclass_cls(**resolved_params)  # type: ignore

        params = list(itertools.chain.from_iterable(h.params for h in handler_results))

        return HandlerResult(info, params, callback)
