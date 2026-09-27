import datetime
import uuid
from pathlib import Path

import click
from click import types as clicktypes

from clickify.handler.choice import ChoiceTypeHandler
from clickify.handler.click_annotated import ClickAnnotatedParameterHandler
from clickify.handler.clicktypes import ClickTypeHandler
from clickify.handler.dataclass import DataclassParamHandler
from clickify.handler.registry import HandlerRegistry
from clickify.handler.sequence import SequenceParamHandler
from clickify.handler.union import UnionParamHandler
from clickify.types import FileBinaryRead, FileBinaryWrite, FileText, FileTextWrite, IntRange, TypeOptions


def get_default_registry() -> HandlerRegistry:
    default_registry = HandlerRegistry()

    # Check for explicit Annotated[T, click.Option()] style declarations first.
    default_registry.register_handler(ClickAnnotatedParameterHandler())

    # Builtin click types.
    default_registry.register_handler(ChoiceTypeHandler())  # Literal / Enum
    # Use is_flag=True only when bool being used as option.
    default_registry.register_handler(
        ClickTypeHandler(clicktypes.BoolParamType, is_flag=True), annotation=bool, is_argument=False
    )
    default_registry.register_handler(ClickTypeHandler(clicktypes.BoolParamType), annotation=bool, is_argument=True)
    default_registry.register_handler(ClickTypeHandler(clicktypes.IntParamType), annotation=int)
    default_registry.register_handler(ClickTypeHandler(clicktypes.IntRange), annotation=IntRange)
    # TODO: FloatRange
    default_registry.register_handler(ClickTypeHandler(clicktypes.FloatParamType), annotation=float)
    default_registry.register_handler(ClickTypeHandler(clicktypes.StringParamType), annotation=str)
    default_registry.register_handler(ClickTypeHandler(clicktypes.UUIDParameterType), annotation=uuid.UUID)
    default_registry.register_handler(ClickTypeHandler(clicktypes.Path, TypeOptions(path_type=Path)), annotation=Path)
    default_registry.register_handler(ClickTypeHandler(clicktypes.DateTime), annotation=datetime.datetime)
    default_registry.register_handler(ClickTypeHandler(clicktypes.File, TypeOptions(mode="r")), annotation=FileText)
    default_registry.register_handler(
        ClickTypeHandler(clicktypes.File, TypeOptions(mode="rb")), annotation=FileBinaryRead
    )
    default_registry.register_handler(
        ClickTypeHandler(clicktypes.File, TypeOptions(mode="w")), annotation=FileTextWrite
    )
    default_registry.register_handler(
        ClickTypeHandler(clicktypes.File, TypeOptions(mode="wb")), annotation=FileBinaryWrite
    )

    # Sequence[T] / T | None / dataclasses
    default_registry.register_handler(SequenceParamHandler(default_registry))
    default_registry.register_handler(UnionParamHandler(default_registry))
    default_registry.register_handler(DataclassParamHandler(default_registry))

    # click.Context
    @default_registry.register()
    def context_handler() -> click.Context:
        return click.get_current_context()

    return default_registry
