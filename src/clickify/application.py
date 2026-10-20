import typing

from clickify.group import ClickifyGroup
from clickify.handler.registry import HandlerRegistry


class CLIApplication(ClickifyGroup):
    """Hold registry of handled types and other app settings."""

    def __init__(
        self,
        *args: typing.Any,
        registry: HandlerRegistry | None = None,
        invoke_direct: bool = True,
        **kwargs: typing.Any,
    ):
        """Create new toplevel CLI application.
        Additional keyword arguments will be passed through to the click.Group constructor.

        Arguments:
            registry:  Handler registry to use.  If omitted, a default registry is created.
            invoke_direct:
                Mirror Typer behaviour where directly invoking the root application when only
                a single command is registered will invoke that command directly.
        """
        super().__init__(*args, registry=registry, **kwargs)
        self.group_class = ClickifyGroup
        self.invoke_direct = invoke_direct

        self.register = self.registry.register

    def __call__(self, *args: typing.Any, **kwargs: typing.Any):
        if self.invoke_direct and len(self.commands) == 1:
            (cmd,) = self.commands.values()
            return cmd(*args, **kwargs)
        return super().__call__(*args, **kwargs)
