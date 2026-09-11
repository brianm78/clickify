from clickify.handler.click_annotated import ClickAnnotatedOptionsHandler, ClickAnnotatedParameterHandler
from clickify.handler.clicktypes import register_click_types
from clickify.handler.registry import HandlerRegistry
from clickify.handler.sequence import SequenceParamHandler


def get_default_registry() -> HandlerRegistry:
    default_registry = HandlerRegistry()

    # Check for explicit Annotated[T, click.Option()] style declarations first.
    default_registry.register_handler(handler=ClickAnnotatedParameterHandler())
    default_registry.register_handler(handler=ClickAnnotatedOptionsHandler(default_registry))
    register_click_types(default_registry)
    default_registry.register_handler(handler=SequenceParamHandler(default_registry))
    return default_registry
