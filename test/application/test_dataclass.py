from collections.abc import Sequence
from dataclasses import dataclass, field

import click
from click.testing import CliRunner

from clickify import CLIApplication


@dataclass
class Args:
    """Bundled args as dataclass
    Arguments:
        nodef: [-y/-n --yes/--no] No default
        default1: [-d --def] Has default
        default2: [-x --def2] Default factory
    """

    nodef: bool

    default1: str = "default"
    default2: Sequence[int] = field(default_factory=tuple)


def test_dataclass():
    app = CLIApplication()

    @app.command()
    def cmd(obj: Args):
        click.echo(obj)

    print(cmd.params)

    runner = CliRunner()
    res = runner.invoke(cmd, [])
    assert res.exit_code != 0

    res = runner.invoke(cmd, ["-y"])
    assert res.exit_code == 0
    assert res.output == "Args(nodef=True, default1='default', default2=())\n"

    res = runner.invoke(cmd, ["-n", "-d", "foo", "-x", "1"])
    assert res.exit_code == 0
    assert res.output == "Args(nodef=False, default1='foo', default2=(1,))\n"

    res = runner.invoke(cmd, ["-n", "-d", "", "-x", "1", "-x", "2", "-x", "3"])
    assert res.exit_code == 0
    assert res.output == "Args(nodef=False, default1='', default2=(1, 2, 3))\n"
