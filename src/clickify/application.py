import typing

from clickify.group import ClickifyGroup
from clickify.registry import HandlerRegistry


class CLIApplication(ClickifyGroup):
    """Hold registry of handled types and other app settings."""

    def __init__(
        self,
        *args: typing.Any,
        registry: HandlerRegistry | None = None,
        use_full_doc_description: bool = False,
        invoke_direct: bool = True,
        **kwargs: typing.Any,
    ):
        """Create new toplevel CLI application.
        Additional keyword arguments will be passed through to the click.Group constructor.

        Arguments:
            registry:
                Handler registry to use.  If omitted, a default registry is created.
            use_full_doc_description:
                If True, use full func.__doc__ as the help (if not provided)
                Otherwise, strips out the Arguments section (used to for the parameter help)
            invoke_direct:
                If only one command/group is defined, calling app() will invoke that command
                directly, rather than acting as a further group.
        """
        super().__init__(*args, registry=registry, use_full_doc_description=use_full_doc_description, **kwargs)
        self.group_class = ClickifyGroup

        self.register = self.registry.register
        self.invoke_direct = invoke_direct

    def __call__(self, *args: typing.Any, **kwargs: typing.Any):
        if self.invoke_direct and len(self.commands) == 1:
            (cmd,) = self.commands.values()
            return cmd(*args, **kwargs)
        return super().__call__(*args, **kwargs)
