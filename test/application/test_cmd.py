"""Test using cmd, which should preserve the function."""

import types

import click
from click.testing import CliRunner

from clickify import CLIApplication


def test_cmd():
    app = CLIApplication()

    @app.cmd()
    def foo(arg: str, opt: int = 0) -> tuple[str, int]:
        click.echo(f"{arg} {opt}")
        return arg, opt

    assert isinstance(foo, types.FunctionType)
    assert isinstance(foo.cmd, click.Command)
    # Should be callable
    assert foo("foo", 123) == ("foo", 123)

    runner = CliRunner()
    res = runner.invoke(foo.cmd, ["a", "--opt", "1"])
    assert res.exit_code == 0
    assert res.output == "a 1\n"


def test_group():
    app = CLIApplication()

    @app.group()
    def grp():
        pass

    @grp.cmd()
    def foo(arg: str, opt: int = 0) -> tuple[str, int]:
        click.echo(f"{arg} {opt}")
        return arg, opt

    assert isinstance(foo, types.FunctionType)
    assert isinstance(foo.cmd, click.Command)
    # Should be callable
    assert foo("foo", 123) == ("foo", 123)

    runner = CliRunner()
    res = runner.invoke(foo.cmd, ["a", "--opt", "1"])
    assert res.exit_code == 0
    assert res.output == "a 1\n"

    res = runner.invoke(grp, ["foo", "a", "--opt", "1"])
    assert res.exit_code == 0
    assert res.output == "a 1\n"
