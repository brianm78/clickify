"""
Test types with special click arg handling (eg. count, Prompt)
"""

import click
from click.testing import CliRunner

from clickify.application import CLIApplication
from clickify.types import Count, Prompt


def test_count(app: CLIApplication, runner: CliRunner):

    @app.command()
    def test(count: Count = 0):
        click.echo(count)

    res = runner.invoke(test, [])
    assert res.exit_code == 0
    assert res.output == "0\n"

    res = runner.invoke(test, ["--count"])
    assert res.exit_code == 0
    assert res.output == "1\n"

    res = runner.invoke(test, ["--count", "--count", "--count"])
    assert res.exit_code == 0
    assert res.output == "3\n"


def test_prompt(app: CLIApplication, runner: CliRunner):

    @app.command()
    def test(val: Prompt[int] = 0):
        click.echo(f"Got: {val}")

    # Normal arg
    res = runner.invoke(test, ["--val", "1"])
    assert res.exit_code == 0
    assert res.output == "Got: 1\n"

    # Read value from stdin
    res = runner.invoke(test, [], input="123\n")
    assert res.exit_code == 0
    assert res.output == "Val [0]: 123\nGot: 123\n"

    # Ensure default works OK
    res = runner.invoke(test, [], input="\n")
    assert res.exit_code == 0
    assert res.output == "Val [0]: \nGot: 0\n"
