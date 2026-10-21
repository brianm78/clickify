import click
import pytest
from click.testing import CliRunner

from clickify.click_compat import command, pass_context


# Check click annotations work even if unannotated.
def test_unannotated_clickarg(runner: CliRunner):

    # When handled by click, should be no warning even if lacking annotation
    # as we should use it directly.

    @command()
    @click.argument("arg", type=click.INT)
    def cmd(arg):  # type: ignore
        click.echo(f"Got: {arg}")

    # Unannotated should happen AFTER check for click params...
    res = runner.invoke(cmd, ["10"])
    assert res.output == "Got: 10\n"


def test_unannotated_click_ctx(runner: CliRunner):
    # For an unannotated context, we don't really have an external indication
    # (Wrapped function exposes original signature, but ctx gets injected by the wrapper function)
    #

    with pytest.warns():

        @command()
        @pass_context
        def ctx_cmd(ctx):  # type: ignore
            click.echo("Invoking")
            ctx.invoke(other, arg=42)

        # Works if give it a default.
        @command()
        @click.argument("arg")
        def other(arg):  # type: ignore
            click.echo(f"OTHER: {arg}")

    res = runner.invoke(ctx_cmd, [])

    assert res.exit_code == 0
    assert res.output == "Invoking\nOTHER: 42\n"


def test_annotated_click_ctx(runner: CliRunner):

    # When we annotate context, but also use click.pass_context
    # we're kind of passing a value for it multiple times.

    @command()
    @pass_context
    def ctx_cmd(ctx: click.Context):
        click.echo("Invoking")

    res = runner.invoke(ctx_cmd, [])

    assert res.exit_code == 0
    assert res.output == "Invoking\n"
