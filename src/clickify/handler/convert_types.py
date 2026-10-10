"""
Handle type aliases / unknown annotations
"""

import inspect
import typing
from dataclasses import replace

from clickify.func.paraminfo import ParamInfo
from clickify.handler.base import FailedHandlerException, WrappingParamHandler
from clickify.handler.registry import HandlerRegistry
from clickify.typeutil import unwrap_annotation
from clickify.utils import AnnotationType

# Don't include string/bytes like objects in sequences
excluded_sequence_types = (str, bytes, bytearray)


class UnannotatedHandler(WrappingParamHandler):
    """If no annotation is provided, use the default type.
    If set to None, fail for unannotated types.
    """

    def __init__(self, registry: HandlerRegistry, type: AnnotationType):
        super().__init__(registry)
        self.type = type

    def convert_param(self, info: ParamInfo) -> ParamInfo | None:
        if info.annotation is inspect._empty:
            if self.type is None:
                raise FailedHandlerException(f"Parameter: {info.name} does not have an annotation")
            return replace(info, annotation=self.type)
        return None


class TypeAliasParamHandler(WrappingParamHandler):
    """If the annotation is a type alias, try again with it resolved."""

    def convert_param(self, info: ParamInfo) -> ParamInfo | None:
        if isinstance(info.annotation, typing.TypeAliasType):
            ann, _meta = unwrap_annotation(
                info.annotation, resolve_annotated=False, resolve_alias=True, resolve_generic=False
            )
            return replace(info, annotation=ann)
