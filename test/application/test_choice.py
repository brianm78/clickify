import typing
from enum import Enum, StrEnum, auto

import click
import pytest
from click.testing import CliRunner

from clickify.application import CLIApplication


class Color(Enum):
    red = auto()
    green = auto()
    blue = auto()


type AliasedColor = Color
type AliasedLiteral = typing.Literal["yes", "no"]


@pytest.mark.parametrize("aliased", [True, False])
def test_enum(app: CLIApplication, runner: CliRunner, aliased: bool):

    if aliased:

        @app.command()
        def test(color: AliasedColor, opt: AliasedColor = Color.red):
            assert isinstance(color, Color)
            assert isinstance(opt, Color)
            click.echo(f"{color} {opt}")
    else:

        @app.command()
        def test(color: Color, opt: Color = Color.red):
            assert isinstance(color, Color)
            assert isinstance(opt, Color)
            click.echo(f"{color} {opt}")

    res = runner.invoke(test, ["red"])
    assert res.exit_code == 0
    assert res.output == "Color.red Color.red\n"

    res = runner.invoke(test, ["red", "--opt", "blue"])
    assert res.exit_code == 0
    assert res.output == "Color.red Color.blue\n"

    res = runner.invoke(test, ["invalid"])
    assert res.exit_code != 0

    res = runner.invoke(test, ["red", "--opt", "invalid"])
    assert res.exit_code != 0


@pytest.mark.parametrize("aliased", [True, False])
def test_enum_nullable(aliased: bool, runner: CliRunner, app: CLIApplication):

    if aliased:

        @app.command()
        def test(color: AliasedColor | None, opt: AliasedColor | None = None):
            assert color is None or isinstance(color, Color)
            assert opt is None or isinstance(opt, Color)
            click.echo(f"{color} {opt}")
    else:

        @app.command()
        def test(color: Color | None, opt: Color | None = None):
            assert color is None or isinstance(color, Color)
            assert opt is None or isinstance(opt, Color)
            click.echo(f"{color} {opt}")

    res = runner.invoke(test, ["red"])
    assert res.exit_code == 0
    assert res.output == "Color.red None\n"

    res = runner.invoke(test, ["red", "--opt", "blue"])
    assert res.exit_code == 0
    assert res.output == "Color.red Color.blue\n"

    res = runner.invoke(test, ["invalid"])
    assert res.exit_code != 0

    res = runner.invoke(test, ["red", "--opt", "invalid"])
    assert res.exit_code != 0


@pytest.mark.parametrize("aliased", [True, False])
def test_literal(app: CLIApplication, runner: CliRunner, aliased: bool):

    if aliased:

        @app.command()
        def test(val: AliasedLiteral, opt: AliasedLiteral = "no"):
            assert isinstance(val, str)
            click.echo(f"{val} {opt}")
    else:

        @app.command()
        def test(val: typing.Literal["yes", "no"], opt: typing.Literal["yes", "no"] = "no"):
            assert isinstance(val, str)
            click.echo(f"{val} {opt}")

    res = runner.invoke(test, ["yes"])
    assert res.exit_code == 0
    assert res.output == "yes no\n"

    res = runner.invoke(test, ["yes", "--opt", "yes"])
    assert res.exit_code == 0
    assert res.output == "yes yes\n"

    res = runner.invoke(test, ["invalid"])
    assert res.exit_code != 0

    res = runner.invoke(test, ["yes", "--opt", "invalid"])
    assert res.exit_code != 0


def test_strenum_mixed_names(app: CLIApplication, runner: CliRunner):
    """Test unlikely corner case where StrEnum used with names corresponding to other values"""

    class Test(StrEnum):
        foo = "bar"
        bar = "foo"

    @app.command()
    def cmd(val: Test = Test.foo, opt: Test = Test.bar):
        assert isinstance(val, Test) and isinstance(opt, Test)
        click.echo(f"{val.name} {opt.name}")

    res = runner.invoke(cmd, [])
    assert res.exit_code == 0
    assert res.output == "foo bar\n"
