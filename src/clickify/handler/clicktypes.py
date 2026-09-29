import typing

import click
import click.types

from clickify.func.paraminfo import ParamInfo
from clickify.handler.base import HandlerResult, BaseParamHandler
from clickify.types import ClickOptions, TypeOptions
from clickify.typeutil import unwrap_annotation

# TODO: Allow TypeOptions annotation.  Eg. for Path(readable=False) etc.
# Eg. x : Annotated[Path, ClickOptions(redable=True, exists=True)] etc]


# TODO: Allow setting decls, is_argument etc, click class (eg. subclass of Argument/Option)
# Maybe also have add_decls=[] vs replace_decls=[]
# (Or short_decls / long_decls)


class ClickTypeHandler(BaseParamHandler):
    """Invoke a click.ParamType to handle the parameter.

    Note: May be annotated with TypeOptions / ClickOptions to pass custom options to the type/parameter
    Eg.
        Annotated[str, TypeOptions(case_sensitive=False)]
    """

    def __init__(
        self, click_type: type[click.ParamType], type_options: TypeOptions | None = None, **opts: typing.Any
    ) -> None:
        self.clicktype = click_type
        self.type_options: dict[str, typing.Any] = type_options if type_options is not None else {}
        self.opts = opts

    def __call__(self, info: ParamInfo) -> HandlerResult | None:
        ann, meta = unwrap_annotation(info.annotation)
        type_opts = dict(self.type_options)
        opts = dict(self.opts)
        for item in meta:
            if isinstance(item, TypeOptions):
                type_opts.update(item)
            elif isinstance(item, ClickOptions):
                opts.update(item)

        # Allow type argument to be overridden directly.
        if "type" not in opts:
            opts["type"] = self.clicktype(**type_opts)

        return HandlerResult(info, [info.to_click_parameter(**opts)])
