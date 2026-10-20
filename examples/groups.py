import click

from clickify import CLIApplication

app = CLIApplication()


@app.group()
def root():
    click.echo("Toplevel callback")


@root.group()
def foo(flag: bool = False):
    click.echo(flag)


@root.command()
def bar(arg: str):
    click.echo(f"bar {arg}")


app()
