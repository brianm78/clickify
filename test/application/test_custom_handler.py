import typing
from collections.abc import Generator

import click
import pytest
from click.testing import CliRunner

from clickify import CLIApplication, ParamInfo
from clickify.handler.base import HandlerResult
from clickify.registry import match_annotation

type CombineType = int
type HandlerType = int
type ZeroArgsType = int


@pytest.fixture
def app() -> Generator[CLIApplication]:
    app = CLIApplication()

    @app.registry.register()
    def complex_handler(*args: int, only_odd: bool = False) -> CombineType:
        """Requests multiple args, returns their sum or product
        Arguments:
            args: list of numbers
            only_odd: [-o] If True, only sum odd values
        """
        if only_odd:
            args = tuple(a for a in args if a % 2 != 0)
        return sum(args, start=0)

    @app.registry.register()
    def ZeroArgHandler() -> ZeroArgsType:
        return 42

    def direct_handler(info: ParamInfo) -> HandlerResult[typing.Any] | None:
        param = info.to_click_parameter(type=click.IntRange(0, 10))
        return HandlerResult(info, [param])

    app.registry.add_handler(direct_handler, match_annotation(HandlerType))
    yield app


def test_extend(app: CLIApplication, runner: CliRunner):
    @app.command()
    def func(x: CombineType, extra_option: bool = False):
        """Test func

        Arguments:

            x: This docstring won't be used
            extra_option: [-x] Extra option
        """
        click.echo(f"{x} : {extra_option}")

    res = runner.invoke(func)
    from b.cli.test import runner_show_failures

    runner_show_failures(res)
    assert res.exit_code == 0
    assert res.output == "0 : False\n"

    res = runner.invoke(func, ["1", "2", "3"])
    assert res.exit_code == 0
    assert res.output == "6 : False\n"

    res = runner.invoke(func, ["1", "2", "3", "-o"])
    assert res.exit_code == 0
    assert res.output == "4 : False\n"

    res = runner.invoke(func, ["1", "2", "3", "-o", "-x"])
    assert res.exit_code == 0
    assert res.output == "4 : True\n"


def test_no_args(app: CLIApplication, runner: CliRunner):
    @app.command()
    def func(x: ZeroArgsType):
        click.echo(x)

    res = runner.invoke(func)
    assert res.exit_code == 0
    assert res.output == "42\n"


def test_directhandler(app: CLIApplication, runner: CliRunner):

    @app.command()
    def func(arg: HandlerType):
        """test func
        Arguments:
            arg: arg
        """
        click.echo(arg)

    res = runner.invoke(func, ["5"])
    assert res.exit_code == 0
    assert res.output == "5\n"

    # Should fail when out of bounds
    res = runner.invoke(func, ["20"])
    assert res.exit_code != 0
