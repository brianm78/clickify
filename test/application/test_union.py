import click
from click.testing import CliRunner

from clickify import CLIApplication


def test_union(app: CLIApplication, runner: CliRunner):

    @app.command()
    def cmd(arg: int | float, opt: int | str):
        click.echo(f"{arg!r} {opt!r}")

    res = runner.invoke(cmd, ["1", "2"])
    assert res.exit_code == 0
    assert res.output == "1 2\n"

    res = runner.invoke(cmd, ["1.0", "foo"])
    assert res.exit_code == 0
    assert res.output == "1.0 'foo'\n"


def test_union_reverseorder(app: CLIApplication, runner: CliRunner):

    # Will use first type that parses,
    # so changing order affects result where inputs
    # are valid for both
    @app.command()
    def cmd(arg: float | int, opt: str | int):
        click.echo(f"{arg!r} {opt!r}")

    res = runner.invoke(cmd, ["1", "2"])
    assert res.exit_code == 0
    assert res.output == "1.0 '2'\n"


def test_defaults(app: CLIApplication, runner: CliRunner):
    """Unions are a bit awkward with defaults.
    Eg.  foo : int | str = '4'
    should give the string default when no default provided, but `4` if
    "4" is given as a CLI option.
    """

    @app.command()
    def cmd(opt: int | str = "4"):
        click.echo(f"{repr(opt)}")

    res = runner.invoke(cmd, [])
    assert res.output == "'4'\n"

    res = runner.invoke(cmd, ["--opt", "foo"])
    assert res.output == "'foo'\n"

    res = runner.invoke(cmd, ["--opt", "4"])
    assert res.output == "4\n"


def test_nullable(app: CLIApplication, runner: CliRunner):

    @app.command()
    def cmd(arg: str | None = None, /, opt: int | None = None):
        click.echo(f"{arg} {opt}")

    res = runner.invoke(cmd, [])
    assert res.output == "None None\n"

    res = runner.invoke(cmd, ["foo"])
    assert res.output == "foo None\n"

    res = runner.invoke(cmd, ["--opt", "1"])
    assert res.output == "None 1\n"


def test_unhandled(app: CLIApplication, runner: CliRunner):
    """Test union with non-handled type (just used as default)"""

    from b.cli.test import runner_show_failures

    class Unhandled:
        def __repr__(self):
            return "unhandled"

    @app.command()
    def cmd(arg: str | Unhandled = Unhandled(), /, opt: int | Unhandled = Unhandled()):
        click.echo(f"{arg} {opt}")

    res = runner.invoke(cmd, [])
    runner_show_failures(res)
    assert res.output == "unhandled unhandled\n"

    res = runner.invoke(cmd, ["foo"])
    assert res.output == "foo unhandled\n"

    res = runner.invoke(cmd, ["--opt", "1"])
    assert res.output == "unhandled 1\n"
