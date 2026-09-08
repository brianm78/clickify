import datetime
import typing
import uuid
from pathlib import Path

import click
import click.types

from clickify.funcinfo import ParamInfo
from clickify.handler.base import ParamHandler
from clickify.handler.registry import HandlerRegistry


class ClickTypeHandler(ParamHandler):
    def __init__(
        self, click_type: click.ParamType, option_specific_opts: dict[str, typing.Any] | None = None, **opts: typing.Any
    ) -> None:
        self.clicktype = click_type
        self.option_specific_opts = option_specific_opts
        self.opts = opts

    def get_params(self, info: ParamInfo) -> list[click.Parameter]:
        return [
            info.to_click_parameter(
                click_type=self.clicktype, option_specific_opts=self.option_specific_opts, **self.opts
            )
        ]


def register_click_types(reg: HandlerRegistry):
    reg.register_annotation(bool, ClickTypeHandler(click.BOOL, dict(is_flag=True)))
    reg.register_annotation(int, ClickTypeHandler(click.INT))
    reg.register_annotation(float, ClickTypeHandler(click.FLOAT))
    reg.register_annotation(str, ClickTypeHandler(click.STRING))
    reg.register_annotation(uuid.UUID, ClickTypeHandler(click.UUID))
    reg.register_annotation(Path, ClickTypeHandler(click.Path()))
    reg.register_annotation(datetime.datetime, ClickTypeHandler(click.DateTime()))
