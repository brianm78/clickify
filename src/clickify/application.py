from clickify.group import ClickifyGroup
from clickify.handler.default_registry import get_default_registry
from clickify.handler.registry import HandlerRegistry


class CLIApplication(ClickifyGroup):
    """Hold registry of handled types and other app settings."""

    def __init__(self, registry: HandlerRegistry | None = None):
        if registry is None:
            registry = get_default_registry()
            # TODO: Setup defaults
        super().__init__(registry=registry)

        self.register = registry.register
