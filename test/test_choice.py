import typing
from enum import Enum, auto

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
def test_enum(aliased: bool):
    app = CLIApplication()

    if aliased:

        @app.command()
        def test(color: AliasedColor):
            assert isinstance(color, Color)
            print(color)
    else:

        @app.command()
        def test(color: Color):
            assert isinstance(color, Color)
            print(color)

    runner = CliRunner()
    res = runner.invoke(test, ["red"])
    print(res.output)
    assert res.exit_code == 0
    assert res.output == "Color.red\n"

    res = runner.invoke(test, ["invalid"])
    assert res.exit_code != 0


@pytest.mark.parametrize("aliased", [True, False])
def test_literal(aliased: bool):
    app = CLIApplication()

    if aliased:

        @app.command()
        def test(val: AliasedLiteral):
            assert isinstance(val, str)
            print(val)
    else:

        @app.command()
        def test(val: typing.Literal["yes", "no"]):
            assert isinstance(val, str)
            print(val)

    runner = CliRunner()
    res = runner.invoke(test, ["yes"])
    print(res.output)
    assert res.exit_code == 0
    assert res.output == "yes\n"

    res = runner.invoke(test, ["invalid"])
    assert res.exit_code != 0
