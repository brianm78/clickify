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

    @app.command()
    def toplevel(val: int):
        print(val)

    @grp.command()
    def cmd(arg: str):
        print(arg)

    assert isinstance(cmd, click.Command)

    @grp.command()
    def cmd2(arg: str, flag2: bool = False):
        print(arg, flag2)

    assert grp.callback is not None
    grp.callback(flag=True)

    # TODO: Not invoking group callback.
    runner = CliRunner()
    res = runner.invoke(app, ["grp", "cmd", "foo"])
    assert res.output == "False\nfoo\n"

    res = runner.invoke(app, ["toplevel", "12"])
    assert res.output == "12\n"


def test_toplevel_callback():
    @CLIApplication.with_callback()
    def grp(flag: bool = False):
        print("Callback:", flag)

    @grp.command()
    def cmd1(arg: str):
        print(arg)

    @grp.command()
    def cmd2(arg: int):
        print(arg)

    assert isinstance(grp, CLIApplication)

    runner = CliRunner()

    res = runner.invoke(grp, ["cmd1", "foo"])
    print(res.output)
    assert res.output == "Callback: False\nfoo\n"

    res = runner.invoke(grp, ["--flag", "cmd2", "123"])
    print(res.output)
    assert res.output == "Callback: True\n123\n"
