import typing
from collections.abc import Callable

import click

from clickify.func.paraminfo import ParamInfo
from clickify.handler.default_registry import get_default_registry
from clickify.handler.function import FunctionHandler
from clickify.handler.registry import HandlerRegistry
from clickify.types import AnyCallable, Decorator

type CommandDecotator[TCmd] = Callable[[AnyCallable], TCmd]


class ClickifyGroup(click.Group):
    """Subclass of click.Group with associated registry."""

    def __init__(
        self,
        *args: typing.Any,
        registry: HandlerRegistry | None = None,
        **kwargs: typing.Any,
    ) -> None:
        super().__init__(**kwargs)
        if registry is None:
            registry = get_default_registry()

        self.registry = registry

    def _make_command[TCmd: click.Command](
        self, func: AnyCallable, cls: type[TCmd], name: str | None = None, **attrs: typing.Any
    ) -> TCmd:
        """Construct click.Command type from function.

        Keyword arguments are passed to the command class.
        May contain a params arg that will override any parameter definitions with the provided
        click.Parameter, and will likewise respect any explicitly annotated args (via @click.option/@click.argument)
        """

        if isinstance(func, click.Command):
            raise TypeError("Attempted to convert a callback into a command twice.")

        # Handle params specified by arg, or by click decorators.
        # These will override parameters inferred from type annotations.
        # TODO: Implement
        attr_params = attrs.pop("params", [])
        decorator_params = getattr(func, "__click_params__", [])
        param_dict: dict[str, click.Parameter] = {p.name: p for p in attr_params}
        param_dict.update({p.name: p for p in decorator_params})

        # TODO: Override if click params specified.

        # Dummy toplevel paraminfo (not actually used, except in debug output)
        toplevel_paraminfo = ParamInfo("<toplevel>", object)
        funchandler = FunctionHandler(self.registry, func, multi_arg=True, override_params=param_dict)

        handlerresult = funchandler(toplevel_paraminfo)
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

        # self.add_command(cmd)

        return cmd

    # Overloads for direct use without args vs  create a decorator
    @typing.overload
    def command(self, name: AnyCallable) -> click.Command: ...

    @typing.overload
    def command[TCmd: click.Command](
        self, name: str | None, cls: type[TCmd], **attrs: typing.Any
    ) -> Callable[[AnyCallable], TCmd]: ...

    @typing.overload
    def command[TCmd: click.Command](
        self,
        name: None = None,
        *,
        cls: type[TCmd],
        **attrs: typing.Any,
    ) -> Callable[[AnyCallable], TCmd]: ...

    # variant: with optional string name, no cls argument provided.
    @typing.overload
    def command(
        self, name: str | None = None, cls: None = None, **attrs: typing.Any
    ) -> Callable[[AnyCallable], click.Command]: ...

    def command[TCmd: click.Command](
        self,
        name: str | AnyCallable | None = None,
        cls: type[TCmd] | None = None,
        **attrs: typing.Any,
    ) -> click.Command | Callable[[AnyCallable], click.Command] | Callable[[AnyCallable], TCmd]:
        """Wrap the click.command decorator to also automatically infer types from
        type annotations.
        """

        if callable(name):
            # Used as decorator with no args - decorate directly as a Command

            assert cls is None, "Use 'command(cls=cls)(callable)' to specify a class."
            assert not attrs, "Use 'command(args=..., ...)(callable)' to provide arguments."
            cmd = self._make_command(name, click.Command)
            self.add_command(cmd)
            return cmd

        if cls is None:
            cls = typing.cast(type[TCmd], click.Command)

        def decorator(func: AnyCallable) -> TCmd:
            cmd = self._make_command(func, cls, name, **attrs)
            self.add_command(cmd)
            return cmd

        return decorator

    @typing.overload
    def cmd[T: AnyCallable](self, name: T) -> T: ...

    @typing.overload
    def cmd(
        self, name: str | None, cls: type[click.Command], add_annotation: bool = True, **attrs: typing.Any
    ) -> Decorator: ...

    @typing.overload
    def cmd(
        self,
        name: None = None,
        *,
        cls: type[click.Command] = click.Command,
        add_annotation: bool = True,
        **attrs: typing.Any,
    ) -> Decorator: ...

    @typing.overload
    def cmd(self, name: str | None = None, cls: None = None, **attrs: typing.Any) -> Decorator: ...

    def cmd[TFunc: AnyCallable](
        self,
        name: str | TFunc | None = None,
        cls: type[click.Command] | None = None,
        add_annotation: bool = True,
        **attrs: typing.Any,
    ) -> TFunc | Decorator:
        """Equivalent to @command, but with the one difference that the function is not replaced with the Command
        object created.
        It can be invoked through the group / CLIApplication it is added to, or  add_annotation is True, by calling
        func.cmd().  Otherwise, the function remaing unchanged and usable as-is.

        Arguments:
            cls:
                The click.Command subclass to use
            add_annotation:
                Annotate the function with a "cmd" attribute corresponding to the click.Command object created from it.
            attrs:
                Further arguments are passed through to the Command class
        """

        if callable(name):
            # Used as decorator with no args - decorate directly as a Command

            assert cls is None, "Use 'command(cls=cls)(callable)' to specify a class."
            assert not attrs, "Use 'command(args=..., ...)(callable)' to provide arguments."
            cmd = self._make_command(name, click.Command)
            self.add_command(cmd)
            return cmd

        if cls is None:
            cls = click.Command

        def decorator[T: AnyCallable](func: T) -> T:
            cmd = self._make_command(func, cls, name, **attrs)
            self.add_command(cmd)
            if add_annotation:
                setattr(func, "cmd", cmd)
            return func

        return decorator

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
