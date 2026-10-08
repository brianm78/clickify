import typing
from dataclasses import replace

from clickify.func.paraminfo import ParamInfo
from clickify.handler.base import WrappingParamHandler
from clickify.types import Prompt
from clickify.typeutil import unwrap_annotation

# Don't include string/bytes like objects in sequences
excluded_sequence_types = (str, bytes, bytearray)


class PromptParamHandler(WrappingParamHandler):
    """Allow Promot[T] to be handled as click.Prompt"""

    def convert_param(self, info: ParamInfo) -> ParamInfo | None:
        ann, meta = unwrap_annotation(info.annotation, resolve_alias=True, resolve_generic=False)
        if typing.get_origin(ann) is Prompt:
            # Replace with underlying type, but set prompt=True
            (realtype,) = typing.get_args(ann)
            param_realtype = replace(info, annotation=realtype).with_click_defaults(prompt=True)
            return param_realtype
        else:
            return None
