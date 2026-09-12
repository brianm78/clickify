import typing

import click
from click.testing import CliRunner

from clickify import CLIApplication, ParamInfo
from clickify.handler.base import HandlerResult, ParamHandler

type mytype = int


class TimesTenHandler(ParamHandler):
    def get(self, info: ParamInfo):
        def callback(args: dict[str, typing.Any]):
            return args[info.name] * 10

        return HandlerResult(info, [info.to_click_parameter(type=click.INT)], callback)


def test_custom_handler():
    """Test custom handler end to end"""
    app = CLIApplication()

    @app.registry.register_annotation(mytype)
    def handler(paraminfo: ParamInfo):
        return paraminfo.to_click_parameter(type=click.IntRange(0, 10))

    @app.command()
    def func(arg: mytype):
        print(arg)

    runner = CliRunner()
    res = runner.invoke(func, ["5"])
    assert res.exit_code == 0
    assert res.output == "5\n"

    # Should fail when out of bounds
    runner = CliRunner()
    res = runner.invoke(func, ["20"])
    assert res.exit_code != 0


def test_custom_handler_class():

    app = CLIApplication()

    app.registry.register_annotation(mytype, TimesTenHandler())

    @app.command()
    def func(arg: mytype):
        print(arg)

    runner = CliRunner()
    res = runner.invoke(func, ["5"])
    assert res.exit_code == 0
    assert res.output == "50\n"
