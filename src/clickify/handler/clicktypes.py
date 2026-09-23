import typing

import click
import click.types

from clickify.func.paraminfo import ParamInfo
from clickify.handler.base import HandlerResult, ParamHandler

# TODO: Allow TypeOptions annotation.  Eg. for Path(readable=False) etc.
# Eg. x : Annotated[Path, ClickOptions(redable=True, exists=True)] etc]


class ClickTypeHandler(ParamHandler):
    def __init__(self, click_type: click.ParamType, **opts: typing.Any) -> None:
        self.clicktype = click_type
        self.opts = opts

    def get(self, info: ParamInfo) -> HandlerResult:
        return HandlerResult(info, [info.to_click_parameter(type=self.clicktype, **self.opts)])
