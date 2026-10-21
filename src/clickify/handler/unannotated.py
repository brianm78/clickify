import inspect
import typing
import warnings

from clickify.func.paraminfo import ParamInfo
from clickify.handler.base import BaseParamHandler, FailedHandlerException, HandlerResult, IgnoreParameterException

# Don't include string/bytes like objects in sequences
excluded_sequence_types = (str, bytes, bytearray)


class UnannotatedHandler(BaseParamHandler):
    """If no annotation is provided, we either ignore the annotation, or fail.
    Note: Ignoring may be needed for some cases when using as a drop-in replacement for
    click.  Eg.

        @click.pass_context()
        def func(ctx, ...): ...

    Would fail on the `ctx` being unannotated, but click will provide this with a wrapper function,
    which does still expose the "ctx" as a param (since using functools.update_wrapper)

    Note: This should be lower priority than things like click annotations, so that
        @click.option("foo", ...)
        def cmd(foo): ...
    will work

    """

    def __init__(
        self,
        warn: bool = True,
        fail: bool = False,
    ):
        self.warn = warn
        self.fail = fail

    def __call__(self, info: ParamInfo) -> HandlerResult[typing.Any] | None:
        if info.annotation is inspect._empty:
            if self.fail:
                raise FailedHandlerException(f"Parameter: {info.name} does not have an annotation")
            if self.warn:
                warnings.warn(f"Parameter: {info.name} has no provided annotation - it will be ignored")

            # Note: The parameter should be completely ignored.
            # (Can't just pass an empty param list since will still try to pass
            # the result of the callback to the function)
            raise IgnoreParameterException()

        return None
