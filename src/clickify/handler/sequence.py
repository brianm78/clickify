import types
import typing
from collections.abc import Sequence
from dataclasses import replace

from clickify.func.paraminfo import ParamInfo
from clickify.handler.base import NotHandledException, WrappingParamHandler
from clickify.typeutil import unwrap_annotation
from clickify.utils import AnnotationType

# Don't include string/bytes like objects in sequences
excluded_sequence_types = (str, bytes, bytearray)


class SequenceParamHandler(WrappingParamHandler):
    def _get_seq_type(self, annotation: AnnotationType) -> tuple[AnnotationType | None, tuple[AnnotationType, ...]]:
        """Return basetype, args"""
        basetype, meta = unwrap_annotation(annotation, resolve_generic=False)
        args = ()
        if isinstance(basetype, types.GenericAlias):
            args = typing.get_args(basetype)
            basetype = typing.get_origin(basetype)

        if (
            isinstance(basetype, type)
            and issubclass(basetype, Sequence)
            and not issubclass(basetype, excluded_sequence_types)
        ):
            return basetype, args

        return None, ()

    def convert_param(self, info: ParamInfo) -> ParamInfo | None:

        basetype, args = self._get_seq_type(info.annotation)

        nargs = -1
        argtype: AnnotationType = None
        if basetype is None:
            raise NotHandledException(f"Annotation {info.annotation} is not a sequence")

        if not args:
            raise NotHandledException(f"No type specified for generic params: {info.annotation}")

        elif basetype is tuple:
            # Special case:
            #     tuple[T, T, T]  -> nargs=3
            #     tuple[T, ...]   -> nargs=-1
            #     Otherwise, raise NotHandled
            if not (len(args) == 2 and args[1] is ...):
                # Not [T, ...] : Check all types are the same.
                if any(arg != args[0] for arg in args):
                    raise NotHandledException(
                        f"tuples with differently typed arguments not supported: {info.annotation}"
                    )
                nargs = len(args)

            argtype = args[0]
        elif len(args) == 1:
            argtype = args[0]

        elif len(args) != 1:
            raise NotHandledException(f"Unexpected number of generic arguments for: {info.annotation}")

        # Replace with an argument using the underlying type, but nargs/multiple set.
        info = replace(info, annotation=argtype)

        if info.is_argument or nargs != -1:
            # Argument or fixed-length tuple option: use nargs
            info = info.with_click_defaults(nargs=nargs)
        else:
            # For options, treat sequence as specify multiple
            info = info.with_click_defaults(multiple=True)

        # Delegate to handler for arg type, but with nargs set.
        return info
