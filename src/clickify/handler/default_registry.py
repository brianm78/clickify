from functools import cache

from clickify.handler.click_annotated import ClickAnnotatedHandler
from clickify.handler.clicktypes import register_click_types
from clickify.handler.registry import HandlerRegistry
from clickify.handler.sequence import SequenceParamHandler


@cache
def get_default() -> HandlerRegistry:
    default_registry = HandlerRegistry()

    # Check for explicit Annotated[T, click.Option()] style declarations first.
    default_registry.register_handler(ClickAnnotatedHandler())
    register_click_types(default_registry)
    default_registry.register_handler(SequenceParamHandler(default_registry))
    return default_registry
