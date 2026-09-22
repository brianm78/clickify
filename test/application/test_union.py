import click
from click.testing import CliRunner

from clickify import CLIApplication


def test_nullable():
    app = CLIApplication()

    @app.command()
    def testunion(arg: str | None = None, /, opt: int | None = None):
        click.echo(f"{arg} {opt}")

    runner = CliRunner()

    res = runner.invoke(testunion, [])
    assert res.output == "None None\n"

    res = runner.invoke(testunion, ["foo"])
    assert res.output == "foo None\n"

    res = runner.invoke(testunion, ["--opt", "1"])
    assert res.output == "None 1\n"
