"""
Defines versions of @command and @group that should be maximally compatible with click,
and so usable as drop-in replacements.

These behave mostly similar to the default CLIApplication.command / group decorators,
but with the following differences:

    - A handler for click.Context is NOT registered.
        This is so that functions using @click.pass_context will not end up getting passed the
        context arg twice (once from us, and once from the wrapper click creates)
        There isn't really a way to reliably detect this otherwise

    - Unannotated parameters are ignored.  Again, this allows click to handle click.context etc
    in the case where it has no annotation.
    The default behaviour is to raise an exception for this case.

"""

import inspect
import typing
from collections.abc import Callable
from functools import update_wrapper

import click

from clickify.application import CLIApplication
from clickify.handler.default_registry import get_default_registry

if typing.TYPE_CHECKING:
    import typing_extensions

reg = get_default_registry(fail_on_unannotated=False)
app = CLIApplication(registry=reg)

command = app.command
group = app.group


def pass_context[**P, R](f: Callable[typing_extensions.Concatenate[click.Context, P], R]) -> Callable[P, R]:
    """Note: We need to override click.pass_context too, as click's version will partially apply
    the function as-is, but leaves the Context parameter in the signature.

    This will cause us to try to pass a value, resulting in it being passed twice.
    Handle this case by filtering out the one we add, and just using the version from pass_context
    """

    sig = inspect.signature(f)

    first_param = next(iter(sig.parameters.values()))
    paramname = first_param.name

    # An alternative might be to filter the parameter out of the signature
    # but that seems kind of tricky to do.

    def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        assert not args
        if paramname in kwargs:
            del kwargs[paramname]
        return f(click.get_current_context(), *args, **kwargs)

    return update_wrapper(wrapper, f)
