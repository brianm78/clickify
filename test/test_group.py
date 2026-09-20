import click
from click.testing import CliRunner

from clickify.application import CLIApplication
from clickify.group import ClickifyGroup


def test_group():
    app = CLIApplication()

    # NOT INVOKING CALLBACK
    @app.group()
    def grp(flag: bool = False):
        print(flag)

    assert isinstance(grp, ClickifyGroup)

    @grp.command()
    def cmd(arg: str):
        print(arg)

    assert isinstance(cmd, click.Command)

    @grp.command()
    def cmd2(arg: str, flag2: bool = False):
        print(arg, flag2)

    # TODO: Not invoking group callback.
    runner = CliRunner()
    res = runner.invoke(app, ["grp", "cmd", "foo"])
    assert res.output == "False\nfoo\n"
