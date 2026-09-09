import types
import typing
from collections.abc import Sequence
from dataclasses import replace

import click

from clickify.func.paraminfo import ParamInfo
from clickify.handler.base import NotHandled, ParamHandler
from clickify.handler.registry import HandlerRegistry
from clickify.typeutil import unwrap_annotation
from clickify.utils import AnnotationType

# Don't include string/bytes like objects in sequences
excluded_sequence_types = (str, bytes, bytearray)


class SequenceParamHandler(ParamHandler):
    def __init__(self, registry: HandlerRegistry) -> None:
        self.registry = registry

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

    def get_params(self, info: ParamInfo) -> list[click.Parameter]:
        basetype, args = self._get_seq_type(info.annotation)
        nargs = -1
        if basetype is None:
            raise NotHandled(f"Annotation {info.annotation} is not a sequence")

        if not args:
            raise NotHandled(f"No type specified for generic params: {info.annotation}")

        elif basetype is tuple:
            # Special case:
            #     tuple[T, T, T]  -> nargs=3
            #     tuple[T, ...]   -> nargs=-1
            #     Otherwise, raise NotHandled
            if not (len(args) == 2 and args[1] is ...):
                # Not [T, ...] : Check all types are the same.
                if any(arg != args[0] for arg in args):
                    raise NotHandled(f"tuples with differently typed arguments not supported: {info.annotation}")
                nargs = len(args)

            argtype = args[0]
        elif len(args) == 1:
            argtype = args[0]

        elif len(args) != 1:
            raise NotHandled(f"Unexpected number of generic arguments for: {info.annotation}")

        # Replace with a multi-arg version of underlying type and handle paramtype.
        info = replace(info, annotation=argtype, nargs=nargs)
        # Delegate to handler for arg type, but with nargs set.
        res = self.registry.get_params(info)
        return res
