"""
Handle type aliases / unknown annotations
"""

import typing
from dataclasses import replace

from clickify.func.paraminfo import ParamInfo
from clickify.handler.base import WrappingParamHandler
from clickify.typeutil import unwrap_annotation


class TypeAliasParamHandler(WrappingParamHandler):
    """If the annotation is a type alias, try again with it resolved."""

    def convert_param(self, info: ParamInfo) -> ParamInfo | None:
        if isinstance(info.annotation, typing.TypeAliasType):
            ann, _meta = unwrap_annotation(
                info.annotation, resolve_annotated=False, resolve_alias=True, resolve_generic=False
            )
            return replace(info, annotation=ann)
