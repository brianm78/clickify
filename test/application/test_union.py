import click
from click.testing import CliRunner

from clickify import CLIApplication


def test_union():
    app = CLIApplication()

    @app.command()
    def cmd(arg: int | float, opt: int | str):
        click.echo(f"{arg!r} {opt!r}")

    runner = CliRunner()

    res = runner.invoke(cmd, ["1", "2"])
    assert res.exit_code == 0
    assert res.output == "1 2\n"

    res = runner.invoke(cmd, ["1.0", "foo"])
    assert res.exit_code == 0
    assert res.output == "1.0 'foo'\n"


def test_union_reverseorder():
    app = CLIApplication()

    # Will use first type that parses,
    # so changing order affects result where inputs
    # are valid for both
    @app.command()
    def cmd(arg: float | int, opt: str | int):
        click.echo(f"{arg!r} {opt!r}")

    runner = CliRunner()

    res = runner.invoke(cmd, ["1", "2"])
    assert res.exit_code == 0
    assert res.output == "1.0 '2'\n"


def test_nullable():
    app = CLIApplication()

    @app.command()
    def cmd(arg: str | None = None, /, opt: int | None = None):
        click.echo(f"{arg} {opt}")

    runner = CliRunner()

    res = runner.invoke(cmd, [])
    assert res.output == "None None\n"

    res = runner.invoke(cmd, ["foo"])
    assert res.output == "foo None\n"

    res = runner.invoke(cmd, ["--opt", "1"])
    assert res.output == "None 1\n"
