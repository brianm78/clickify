import datetime
import uuid
from pathlib import Path

import click

from clickify.handler.choice import ChoiceTypeHandler
from clickify.handler.click_annotated import ClickAnnotatedOptionsHandler, ClickAnnotatedParameterHandler
from clickify.handler.clicktypes import ClickTypeHandler
from clickify.handler.registry import HandlerRegistry
from clickify.handler.sequence import SequenceParamHandler


def get_default_registry() -> HandlerRegistry:
    default_registry = HandlerRegistry()

    # Check for explicit Annotated[T, click.Option()] style declarations first.
    default_registry.register_handler(ClickAnnotatedParameterHandler())
    default_registry.register_handler(ClickAnnotatedOptionsHandler(default_registry))
    default_registry.register_handler(ChoiceTypeHandler())

    default_registry.register_handler(ClickTypeHandler(click.BOOL, dict(is_flag=True)), annotation=bool)
    default_registry.register_handler(ClickTypeHandler(click.INT), annotation=int)
    default_registry.register_handler(ClickTypeHandler(click.FLOAT), annotation=float)
    default_registry.register_handler(ClickTypeHandler(click.STRING), annotation=str)
    default_registry.register_handler(ClickTypeHandler(click.UUID), annotation=uuid.UUID)
    default_registry.register_handler(ClickTypeHandler(click.Path()), annotation=Path)
    default_registry.register_handler(ClickTypeHandler(click.DateTime()), annotation=datetime.datetime)
    default_registry.register_handler(SequenceParamHandler(default_registry))
    return default_registry
