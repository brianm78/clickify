"""
CLIApplication:
    - holds registered types, and allows defining commands / groups
    - app.run() will invoke the defined command, or if multiple defined,
      act as a group.
    - handlers may be simple or complex

TODO: Should we have .run_single() vs run()?

"""

import typing
from collections.abc import Callable

import click

from clickify.funcinfo import FuncInfo
from clickify.handler.registry import HandlerRegistry

type Predicate = Callable[[typing.Any], bool]
type AnyCallable = Callable[..., typing.Any]


class CLIApplication:
    """Hold registry of handled types and other app settings."""

    def __init__(self, registry: HandlerRegistry | None = None):
        if registry is None:
            registry = HandlerRegistry()
            # TODO: Setup defaults
        self.registry = registry
        self.commands: list[click.Command] = []
        self.groups: list[click.Group] = []

    def _make_command_decorator[TCmd: click.Command](
        self, cls: type[TCmd], name: str | None = None, **attrs: typing.Any
    ) -> typing.Callable[[AnyCallable], TCmd]:
        """Return decorator that creates a click.Command from the function.

        Keyword arguments are passed to the command class.
        May contain a params arg that will override any parameter definitions with the provided
        click.Parameter, and will likewise respect any explicitly annotated args (via @click.option/@click.argument)
        """

        def decorator(func: AnyCallable) -> TCmd:
            if isinstance(func, click.Command):
                raise TypeError("Attempted to convert a callback into a command twice.")

            # Handle params specified by arg, or by click decorators.
            # These will override parameters inferred from type annotations.
            attr_params = attrs.pop("params", [])
            decorator_params = getattr(func, "__click_params__", [])
            param_dict = {p.name: p for p in attr_params}
            param_dict.update({p.name: p for p in decorator_params})

            funcinfo = FuncInfo.from_func(func)

            params: list[click.Parameter] = []
            for paraminfo in funcinfo.params:
                # Use corresponding handler for each type
                params += list(self.registry.get_params(paraminfo))

            # If help specified, override docstring description
            help = attrs.pop("help", None)
            if help is None:
                help = funcinfo.docinfo.description

            cmdname = getattr(func, "__name__", None) if name is None else name
            if cmdname is None:
                raise Exception("No name provided for function")

            cmd = cls(
                name=cmdname,
                callback=funcinfo.invoke,
                params=params,
                help=help,
                **attrs,
            )

            self.commands.append(cmd)
            return cmd

        return decorator

    # Overloads for direct use without args vs  create a decorator
    @typing.overload
    def command(self, name: AnyCallable) -> click.Command: ...

    @typing.overload
    def command[TCmd: click.Command](
        self, name: str | None, cls: type[TCmd], **attrs: typing.Any
    ) -> typing.Callable[[AnyCallable], TCmd]: ...

    @typing.overload
    def command[TCmd: click.Command](
        self,
        name: None = None,
        *,
        cls: type[TCmd],
        **attrs: typing.Any,
    ) -> typing.Callable[[AnyCallable], TCmd]: ...

    # variant: with optional string name, no cls argument provided.
    @typing.overload
    def command(
        self, name: str | None = None, cls: None = None, **attrs: typing.Any
    ) -> typing.Callable[[AnyCallable], click.Command]: ...

    def command[TCmd: click.Command](
        self,
        name: str | AnyCallable | None = None,
        cls: type[TCmd] | None = None,
        **attrs: typing.Any,
    ) -> click.Command | typing.Callable[[AnyCallable], click.Command] | typing.Callable[[AnyCallable], TCmd]:
        """Wrap the click.command decorator to also automatically infer types from
        type annotations.

        Accepts a type registry which will be used to lookup annotations and convert
        to one or more params.
        """

        if callable(name):
            # Used as decorator with no args - ecorate directly

            assert cls is None, "Use 'command(cls=cls)(callable)' to specify a class."
            assert not attrs, "Use 'command(args=..., ...)(callable)' to provide arguments."
            decorator = self._make_command_decorator(click.Command)
            return decorator(name)

        if cls is None:
            return self._make_command_decorator(click.Command, name, **attrs)
        else:
            decorator = self._make_command_decorator(cls, name, **attrs)
            return decorator

    # # Overloads for direct use without args vs  create a decorator
    # @typing.overload
    # def group(self, name: AnyCallable) -> AutoclickGroup: ...

    # @typing.overload
    # def group[TGrp: AutoclickGroup](
    #     self, name: str | None, cls: type[TGrp], **attrs: typing.Any
    # ) -> typing.Callable[[AnyCallable], TGrp]: ...

    # @typing.overload
    # def group[TGrp: AutoclickGroup](
    #     self,
    #     name: None = None,
    #     *,
    #     cls: type[TGrp],
    #     **attrs: typing.Any,
    # ) -> typing.Callable[[AnyCallable], TGrp]: ...

    # # variant: with optional string name, no cls argument provided.
    # @typing.overload
    # def group(
    #     self, name: str | None = ..., cls: None = None, **attrs: typing.Any
    # ) -> typing.Callable[[AnyCallable], AutoclickGroup]: ...

    # def group[TGrp: AutoclickGroup](
    #     self,
    #     name: str | AnyCallable | None = None,
    #     cls: type[TGrp] | type[AutoclickGroup] | None = None,
    #     **attrs: typing.Any,
    # ) -> AutoclickGroup | typing.Callable[[AnyCallable], AutoclickGroup | TGrp]:
    #     """Wrap the group decorator, returning a modified group."""
    #     if cls is None:
    #         cls = AutoclickGroup

    #     if callable(name):
    #         return self.command(cls=cls, **attrs)(name)

    #     return self.command(name, cls, **attrs)
