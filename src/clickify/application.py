import typing
from collections.abc import Callable

from clickify.func.paraminfo import ParamInfo
from clickify.group import ClickifyGroup
from clickify.handler.default_registry import get_default_registry
from clickify.handler.function import FunctionHandler
from clickify.handler.registry import HandlerRegistry
from clickify.types import AnyCallable


class CLIApplication(ClickifyGroup):
    """Hold registry of handled types and other app settings."""

    def __init__(self, registry: HandlerRegistry | None = None, invoke_direct: bool = True, **kwargs: typing.Any):
        """Create new toplevel CLI application.
        Additional keyword arguments will be passed through to the click.Group constructor.

        Arguments:
            registry:  Handler registry to use.  If omitted, a default registry is created.
            invoke_direct:
                Mirror Typer behaviour where directly invoking the root application when only
                a single command is registered will invoke that command directly.
        """
        if registry is None:
            registry = get_default_registry()
        super().__init__(registry=registry, **kwargs)
        self.group_class = ClickifyGroup
        self.invoke_direct = invoke_direct

        self.register = registry.register

    def __call__(self, *args: typing.Any, **kwargs: typing.Any):
        if self.invoke_direct and len(self.commands) == 1:
            (cmd,) = self.commands.values()
            return cmd(*args, **kwargs)
        return super().__call__(*args, **kwargs)

    # TODO: Has issue that registering etc may happen after create func handler.
    # Maybe just implement by having a toplevel group.
    # Ie. @app.group(...)
    #     def toplevel(): ...
    @classmethod
    def with_callback(
        cls,
        registry: HandlerRegistry | None = None,
        name: str | None = None,
        help: str | None = None,
        **kwargs: typing.Any,
    ) -> Callable[[AnyCallable], CLIApplication]:
        """Register a top-level callback.

        Eg.
            @CLIApplication.with_callback()
            def cli():
                ...

            @cli.command()
            def cmd(): ...

        """
        if registry is None:
            registry = get_default_registry()

        def decorator(func: AnyCallable) -> CLIApplication:
            toplevel_paraminfo = ParamInfo("<toplevel>", object)
            funchandler = FunctionHandler(registry, func, True)
            handlerresult = funchandler(toplevel_paraminfo)
            if handlerresult is None:
                raise Exception("Failure in constructing toplevel function handler")

            funchandler = FunctionHandler(registry, func, multi_arg=True)
            helpstr = funchandler.funcinfo.docinfo.description if help is None else help
            cmdname = getattr(func, "__name__", None) if name is None else name
            app = cls(
                callback=handlerresult.callback,
                params=handlerresult.params,
                registry=registry,
                name=cmdname,
                help=helpstr,
                **kwargs,
            )
            return app

        return decorator
