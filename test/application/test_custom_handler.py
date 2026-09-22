from collections.abc import Generator

import click
import pytest
from click.testing import CliRunner

from clickify import CLIApplication, ParamInfo
from clickify.handler.base import HandlerResult, ParamHandler

type ComplexType = int
type SimpleType = int
type HandlerClassType = int
type ZeroArgsType = int


@pytest.fixture
def app() -> Generator[CLIApplication]:
    app = CLIApplication()

    @app.registry.register()
    def complex_handler(*args: int, flag: bool = False) -> ComplexType:
        """Complex handler
        Arguments:
            args: list of numbers
            flag: If True, always returns zero. Otherwise return sum.
        """
        if flag:
            return 0
        return sum(args, start=0)

    @app.registry.register()
    def simple_handler(arg: int) -> SimpleType:
        """Simple handler."""
        return arg * 10

    @app.registry.register()
    def ZeroArgHandler() -> ZeroArgsType:
        return 42

    class ClassBasedHandler(ParamHandler):
        def get(self, info: ParamInfo) -> HandlerResult:
            param = info.to_click_parameter(type=click.IntRange(0, 10))
            return HandlerResult(info, [param])

    app.registry.register_handler(ClassBasedHandler(), annotation=HandlerClassType)
    yield app


def test_simple(app: CLIApplication):

    @app.command()
    def func(arg: SimpleType = 0, other: bool = False):
        """test func
        Arguments:
            arg: [--foo -x] Arg info
            other: [-o] Flag
        """
        click.echo(f"{arg} {other}")

    runner = CliRunner()
    res = runner.invoke(func, ["--foo", "5"])
    assert res.exit_code == 0
    assert res.output == "50 False\n"

    res = runner.invoke(func, ["-x", "1", "-o"])
    assert res.exit_code == 0
    assert res.output == "10 True\n"


def test_no_args(app: CLIApplication):
    @app.command()
    def func(x: ZeroArgsType):
        click.echo(x)

    runner = CliRunner()
    res = runner.invoke(func)
    assert res.exit_code == 0
    assert res.output == "42\n"


def test_classbased(app: CLIApplication):

    @app.command()
    def func(arg: HandlerClassType):
        """test func
        Arguments:
            arg: arg
        """
        click.echo(arg)

    runner = CliRunner()
    res = runner.invoke(func, ["5"])
    assert res.exit_code == 0
    assert res.output == "5\n"

    # Should fail when out of bounds
    runner = CliRunner()
    res = runner.invoke(func, ["20"])
    assert res.exit_code != 0
