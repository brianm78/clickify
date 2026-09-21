import types
import typing
from collections.abc import Sequence
from dataclasses import replace

from clickify.func.paraminfo import ParamInfo
from clickify.handler.base import NotHandledException, WrappingParamHandler
from clickify.typeutil import unwrap_annotation
from clickify.utils import AnnotationType

# TODO: Could we support T | U by creating a click type
# that tries each handler in turn (in definition order), till one is successful?
# Eg. int | str tries parsing as int, but on exception, uses click.STRING


class NullableParamHandler(WrappingParamHandler):
    """
    Treat T | None as if it were just T
    """

    def convert_param(self, info: ParamInfo) -> ParamInfo | None:
        ann, meta = unwrap_annotation(info.annotation, resolve_generic=False)
        if typing.get_origin(ann) is not typing.Union:
            return None

        found_type: AnnotationType | None = None
        for union_type in typing.get_args(ann):
            print("UNIONTYPE", union_type)
            if union_type is not types.NoneType:
                if found_type is None:
                    found_type = union_type
                else:
                    return None  # Not supporting multiple non-None types.
        if found_type is not None:
            return replace(info, annotation=found_type)
        return None
