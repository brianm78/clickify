"""
Test mixing click code with clickify
"""

import click
from click.testing import CliRunner

from clickify import CLIApplication


def test_annotation(app: CLIApplication, runner: CliRunner):
    """Check purely click annotations"""

    @app.command()
    @click.argument("arg")
    @click.option("flag", "--flag", "-f", type=click.BOOL, default=False, is_flag=True)
    def cmd(arg: str, flag: bool):
        click.echo(f"{arg} {flag}")

    res = runner.invoke(cmd, ["foo"])
    assert res.exit_code == 0
    assert res.output == "foo False\n"


def test_mix(app: CLIApplication, runner: CliRunner):
    """Check mix of click and signature based annotation"""

    @app.command()
    @click.argument("arg", type=click.INT)
    @click.option("flag", "--flag", "-f", type=click.BOOL, default=False, is_flag=True)
    def cmd(arg: str, flag: bool, nonclick: int = 12):
        """Test

        Arguments:
            arg: Overridden by click
            flag: [-x] Overridden by click
            nonclick: [-n] Non-click param
        """
        assert isinstance(arg, int)
        click.echo(f"{arg} {flag} {nonclick}")

    res = runner.invoke(cmd, ["42"])
    assert res.exit_code == 0
    assert res.output == "42 False 12\n"

    # Should NOT pick up decls for overridden params
    res = runner.invoke(cmd, ["1", "-x"])
    assert res.exit_code != 0

    # But should for non-overridden
    res = runner.invoke(cmd, ["1", "-n", "2"])
    assert res.exit_code == 0
    assert res.output == "1 False 2\n"
