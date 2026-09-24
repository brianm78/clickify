import datetime
import uuid
from pathlib import Path

import click

from clickify.handler.choice import ChoiceTypeHandler
from clickify.handler.click_annotated import ClickAnnotatedOptionsHandler, ClickAnnotatedParameterHandler
from clickify.handler.clicktypes import ClickTypeHandler
from clickify.handler.dataclass import DataclassParamHandler
from clickify.handler.registry import HandlerRegistry
from clickify.handler.sequence import SequenceParamHandler
from clickify.handler.union import UnionParamHandler
from clickify.types import FileBinaryRead, FileBinaryWrite, FileText, FileTextWrite


def get_default_registry() -> HandlerRegistry:
    default_registry = HandlerRegistry()

    # Check for explicit Annotated[T, click.Option()] style declarations first.
    default_registry.register_handler(ClickAnnotatedParameterHandler())
    default_registry.register_handler(ClickAnnotatedOptionsHandler(default_registry))

    # Builtin click types.
    default_registry.register_handler(ChoiceTypeHandler())  # Literal / Enum
    # Use is_flag=True only when bool being used as option.
    default_registry.register_handler(ClickTypeHandler(click.BOOL, is_flag=True), annotation=bool, is_argument=False)
    default_registry.register_handler(ClickTypeHandler(click.BOOL), annotation=bool, is_argument=True)
    default_registry.register_handler(ClickTypeHandler(click.INT), annotation=int)
    default_registry.register_handler(ClickTypeHandler(click.FLOAT), annotation=float)
    default_registry.register_handler(ClickTypeHandler(click.STRING), annotation=str)
    default_registry.register_handler(ClickTypeHandler(click.UUID), annotation=uuid.UUID)
    default_registry.register_handler(ClickTypeHandler(click.Path(path_type=Path)), annotation=Path)
    default_registry.register_handler(ClickTypeHandler(click.DateTime()), annotation=datetime.datetime)
    default_registry.register_handler(ClickTypeHandler(click.File("r")), annotation=FileText)
    default_registry.register_handler(ClickTypeHandler(click.File("rb")), annotation=FileBinaryRead)
    default_registry.register_handler(ClickTypeHandler(click.File("w")), annotation=FileTextWrite)
    default_registry.register_handler(ClickTypeHandler(click.File("wb")), annotation=FileBinaryWrite)

    # Sequence[T] / T | None / dataclasses
    default_registry.register_handler(SequenceParamHandler(default_registry))
    default_registry.register_handler(UnionParamHandler(default_registry))
    default_registry.register_handler(DataclassParamHandler(default_registry))

    # click.Context
    @default_registry.register()
    def context_handler() -> click.Context:
        return click.get_current_context()

    return default_registry
