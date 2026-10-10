import datetime
import uuid
from pathlib import Path

import click
from click import types as clicktypes

from clickify.handler.choice import ChoiceTypeHandler
from clickify.handler.click_annotated import ClickAnnotatedParameterHandler
from clickify.handler.clicktypes import ClickTypeHandler
from clickify.handler.dataclass import DataclassParamHandler
from clickify.handler.prompt import PromptParamHandler
from clickify.handler.registry import BUILTIN_PRIORITY, HandlerRegistry, match_annotation
from clickify.handler.sequence import SequenceParamHandler
from clickify.handler.convert_types import TypeAliasParamHandler, UnannotatedHandler
from clickify.handler.union import UnionParamHandler
from clickify.types import FileBinaryRead, FileBinaryWrite, FileText, FileTextWrite, FloatRange, IntRange, TypeOptions


def get_default_registry() -> HandlerRegistry:
    reg = HandlerRegistry()

    # Note: The below are registered at a higher priority value than user-registered types,
    # so those will override them where overlapping.
    # They aslo match aliased types (to allow for things like:
    #    type CaseInsensitive = Annotated[str, ClickOptions(case_sensitive=False)]
    # Whereas user defined types default to exact matches.

    # Check for explicit Annotated[T, click.Option()] style declarations first.
    reg.add_handler(ClickAnnotatedParameterHandler(), priority=BUILTIN_PRIORITY)
    reg.add_handler(PromptParamHandler(reg), priority=BUILTIN_PRIORITY)

    # Builtin click types:

    reg.add_handler(ChoiceTypeHandler(), priority=BUILTIN_PRIORITY)  # Literal / Enum
    # Use is_flag=True only when bool being used as option.
    reg.add_handler(
        ClickTypeHandler(clicktypes.BoolParamType, is_flag=True),
        match_annotation(bool, is_argument=False),
        BUILTIN_PRIORITY,
    )
    reg.add_handler(
        ClickTypeHandler(clicktypes.BoolParamType), match_annotation(bool, is_argument=True), BUILTIN_PRIORITY
    )
    reg.add_handler(ClickTypeHandler(clicktypes.IntParamType), match_annotation(int), BUILTIN_PRIORITY)

    reg.add_handler(ClickTypeHandler(clicktypes.IntRange), match_annotation(IntRange), BUILTIN_PRIORITY)
    reg.add_handler(ClickTypeHandler(clicktypes.FloatParamType), match_annotation(float), BUILTIN_PRIORITY)
    reg.add_handler(ClickTypeHandler(clicktypes.FloatRange), match_annotation(FloatRange), BUILTIN_PRIORITY)
    reg.add_handler(ClickTypeHandler(clicktypes.StringParamType), match_annotation(str), priority=BUILTIN_PRIORITY)
    reg.add_handler(ClickTypeHandler(clicktypes.UUIDParameterType), match_annotation(uuid.UUID), BUILTIN_PRIORITY)
    reg.add_handler(
        ClickTypeHandler(clicktypes.Path, TypeOptions(path_type=Path)), match_annotation(Path), BUILTIN_PRIORITY
    )
    reg.add_handler(ClickTypeHandler(clicktypes.DateTime), match_annotation(datetime.datetime), BUILTIN_PRIORITY)
    reg.add_handler(
        ClickTypeHandler(clicktypes.File, TypeOptions(mode="r")), match_annotation(FileText), BUILTIN_PRIORITY
    )
    reg.add_handler(
        ClickTypeHandler(clicktypes.File, TypeOptions(mode="rb")), match_annotation(FileBinaryRead), BUILTIN_PRIORITY
    )
    reg.add_handler(
        ClickTypeHandler(clicktypes.File, TypeOptions(mode="w")), match_annotation(FileTextWrite), BUILTIN_PRIORITY
    )
    reg.add_handler(
        ClickTypeHandler(clicktypes.File, TypeOptions(mode="wb")), match_annotation(FileBinaryWrite), BUILTIN_PRIORITY
    )

    # Sequence[T] / T | None / dataclasses
    reg.add_handler(SequenceParamHandler(reg), priority=BUILTIN_PRIORITY)
    reg.add_handler(UnionParamHandler(reg), priority=BUILTIN_PRIORITY)
    reg.add_handler(DataclassParamHandler(reg), priority=BUILTIN_PRIORITY)

    # click.Context
    @reg.register(priority=BUILTIN_PRIORITY)
    def context_handler() -> click.Context:
        return click.get_current_context()

    # If there are no matches, resolve any type aliases and try again with unaliased type.
    # Eg. given type InsensitiveString = Annotated[str, ClickOptions(case_sensitive=False)],
    # will reissue search using `str` (but retaining the Annotated[] part)
    #
    reg.add_handler(TypeAliasParamHandler(reg), priority=BUILTIN_PRIORITY)

    # By default fail for unannotated types.
    # To override, add a higher priority handler, like UnannotatedHandler(reg, str)
    reg.add_handler(UnannotatedHandler(reg, None), priority=BUILTIN_PRIORITY)
    return reg
