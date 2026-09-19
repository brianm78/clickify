import datetime
import typing
import uuid
from pathlib import Path

import click
import click.types

from clickify.func.paraminfo import ParamInfo
from clickify.handler.base import HandlerResult, ParamHandler
from clickify.handler.registry import HandlerRegistry


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


def register_click_types(reg: HandlerRegistry):
    reg.register_handler(ClickTypeHandler(click.BOOL, dict(is_flag=True)), annotation=bool)
    reg.register_handler(ClickTypeHandler(click.INT), annotation=int)
    reg.register_handler(ClickTypeHandler(click.FLOAT), annotation=float)
    reg.register_handler(ClickTypeHandler(click.STRING), annotation=str)
    reg.register_handler(ClickTypeHandler(click.UUID), annotation=uuid.UUID)
    reg.register_handler(ClickTypeHandler(click.Path()), annotation=Path)
    reg.register_handler(ClickTypeHandler(click.DateTime()), annotation=datetime.datetime)

    @reg.register()
    def context_handler() -> click.Context:
        return click.get_current_context()
