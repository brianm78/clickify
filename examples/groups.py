import click

from clickify import CLIApplication


@CLIApplication.with_callback()
def app():
    click.echo("Toplevel callback")


@app.group()
def foo(flag: bool = False):
    click.echo(flag)


@foo.command()
def bar(arg: str):
    click.echo(f"bar {arg}")


app()
