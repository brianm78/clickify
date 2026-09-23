import typing

import click
import click.types

from clickify.func.paraminfo import ParamInfo
from clickify.handler.base import HandlerResult, ParamHandler

# TODO: Allow TypeOptions annotation.  Eg. for Path(readable=False) etc.


class ClickTypeHandler(ParamHandler):
    def __init__(
        self, click_type: click.ParamType, option_specific_opts: dict[str, typing.Any] | None = None, **opts: typing.Any
    ) -> None:
        self.clicktype = click_type
        self.option_opts = self.opts = opts

        # Allow options that only apply on Option type (eg. flag=True on bool optionss, but not arguments)
        if option_specific_opts is not None:
            self.option_opts = opts | option_specific_opts

    def get(self, info: ParamInfo) -> HandlerResult:
        opts = self.opts if info.is_argument else self.option_opts
        return HandlerResult(info, [info.to_click_parameter(type=self.clicktype, **opts)])
