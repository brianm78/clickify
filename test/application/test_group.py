import click
from click.testing import CliRunner

from clickify.application import CLIApplication
from clickify.group import ClickifyGroup


def test_group(app: CLIApplication, runner: CliRunner):

    @app.group()
    def grp(flag: bool = False):
        click.echo(flag)

    assert isinstance(grp, ClickifyGroup)

    @app.command()
    def toplevel(val: int):
        click.echo(val)

    @grp.command()
    def cmd(arg: str):
        click.echo(arg)

    assert isinstance(cmd, click.Command)

    @grp.command()
    def cmd2(arg: str, flag2: bool = False):
        click.echo(f"{arg} {flag2}")

    assert grp.callback is not None
    grp.callback(flag=True)

    # TODO: Not invoking group callback.
    res = runner.invoke(app, ["grp", "cmd", "foo"])
    assert res.output == "False\nfoo\n"

    res = runner.invoke(app, ["toplevel", "12"])
    assert res.output == "12\n"
