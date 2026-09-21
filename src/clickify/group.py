import typing
from collections.abc import Callable, Sequence

import click

from clickify.func.paraminfo import ParamInfo
from clickify.handler.base import HandlerResult
from clickify.handler.function import FunctionHandler
from clickify.handler.registry import HandlerRegistry
from clickify.types import AnyCallable


class ClickifyGroup(click.Group):
    """Subclass of click.Group with associated registry."""

    def __init__(
        self,
        registry: HandlerRegistry,
        **kwargs: typing.Any,
    ) -> None:
        super().__init__(**kwargs)
        self.registry = registry

    def _make_command_decorator[TCmd: click.Command](
        self, cls: type[TCmd], name: str | None = None, **attrs: typing.Any
    ) -> Callable[[AnyCallable], TCmd]:
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
            # TODO: Implement
            attr_params = attrs.pop("params", [])
            decorator_params = getattr(func, "__click_params__", [])
            param_dict = {p.name: p for p in attr_params}
            param_dict.update({p.name: p for p in decorator_params})

            # TODO: Override if click params specified.

            # Dummy toplevel paraminfo (not actually used, except in debug output)
            toplevel_paraminfo = ParamInfo("<toplevel>", object)
            funchandler = FunctionHandler(self.registry, func, multi_arg=True)

            handlerresult = funchandler.get(toplevel_paraminfo)
            if handlerresult is None:
                raise Exception("Failure in constructing toplevel function handler")

            # If help specified, override docstring description
            help = attrs.pop("help", None)
            if help is None:
                help = funchandler.funcinfo.docinfo.description

            cmdname = getattr(func, "__name__", None) if name is None else name
            if cmdname is None:
                raise Exception("No name provided for function")

            cmd = cls(
                name=cmdname,
                callback=handlerresult.callback,
                params=handlerresult.params,
                help=help,
                **attrs,
            )

            self.add_command(cmd)

            # TODO: Should we return the function instead of the command?
            # It'd be breaking with click, but allows the function to be called normally, and we
            # can invoke it from the group object anyway.
            #  - maybe annotate with an attribute pointing at the command.
            # (Or have two modes / an argument to @command() / seperate method @function_command()?
            # Eg. @command(replace=False)
            # What about @group though?
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
        """
        if callable(name):
            # Used as decorator with no args - decorate directly as a Command

            assert cls is None, "Use 'command(cls=cls)(callable)' to specify a class."
            assert not attrs, "Use 'command(args=..., ...)(callable)' to provide arguments."
            decorator = self._make_command_decorator(click.Command)
            return decorator(name)

        if cls is None:
            return self._make_command_decorator(click.Command, name, **attrs)
        else:
            return self._make_command_decorator(cls, name, **attrs)

    @typing.overload
    def group(self, __func: Callable[..., typing.Any]) -> ClickifyGroup: ...

    @typing.overload
    def group(
        self, *args: typing.Any, **kwargs: typing.Any
    ) -> Callable[[Callable[..., typing.Any]], ClickifyGroup]: ...

    def group(self, *args: typing.Any, **kwargs: typing.Any) -> Callable[[AnyCallable], ClickifyGroup] | ClickifyGroup:
        """Wrap click's group to pass through type registry."""
        # NOTE: duplicating click's logic here, since need to
        # pass through registry and invoke custom .command logic

        func: AnyCallable | None = None

        if args and callable(args[0]):
            assert len(args) == 1 and not kwargs, "Use 'group(**kwargs)(callable)' to provide arguments."
            (func,) = args
            args = ()

        if kwargs.get("cls") is None:
            if self.group_class is not None:
                if self.group_class is type:
                    kwargs["cls"] = type(self)
                else:
                    kwargs["cls"] = self.group_class
            else:
                kwargs["cls"] = ClickifyGroup

        if not issubclass(kwargs["cls"], ClickifyGroup):
            # TODO: Should we allow this (eg. for attaching regular click groups?)
            raise TypeError("cls must be an subclass of ClickifyGroup")

        def decorator(f: AnyCallable) -> ClickifyGroup:
            # click originally calls the click.group decorator here, which just invokes
            # command.  We need to decorate, and pass registry, so just directly calling
            # self.command
            cmd: ClickifyGroup = self.command(*args, registry=self.registry, **kwargs)(f)
            # self.add_command(cmd)
            return cmd

        if func is not None:
            return decorator(func)

        return decorator
