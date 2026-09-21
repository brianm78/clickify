from click.testing import CliRunner

from clickify.application import CLIApplication


def basic_func(strval: str, intval: int, flag: bool = False) -> None:
    """test func

    Arguments:
        strval: A string value
        intval: Integer argument
        flag: [-f --flag] Flag option
    """
    print(strval, intval, flag)


def posargs_func(optional_arg: str = "default", /, *, required_opt: int):
    """Test with optional arg and required option.
    Arguments:
        optional_arg: Optional argument
        required_opt: [-o --opt] Required option
    """
    print(optional_arg, required_opt)


def varargs_func(*vals: int, total: bool = False):
    """Varargs test

    Arguments:
        vals: list of ints
        total: [-t --total] Print sum of args
    """
    print(vals)
    if total:
        print(sum(vals))


def test_help():
    app = CLIApplication()
    runner = CliRunner()
    test = app.command(basic_func)
    res = runner.invoke(test, ["--help"])
    assert (
        res.output
        == """\
Usage: basic_func [OPTIONS] STRVAL INTVAL

  test func

Positional arguments:
  STRVAL  A string value
  INTVAL  Integer argument

Options:
  -f, --flag  Flag option
  --help      Show this message and exit.
"""
    )


def test_basic():
    app = CLIApplication()

    test = app.command(basic_func)
    runner = CliRunner()
    res = runner.invoke(test, ["foo", "42", "--flag"])
    assert res.output == "foo 42 True\n"

    res = runner.invoke(test, ["foo", "42", "-f"])
    assert res.output == "foo 42 True\n"

    res = runner.invoke(test, ["bar", "1"])
    assert res.output == "bar 1 False\n"

    res = runner.invoke(app, ["basic_func", "bar", "1"])
    assert res.output == "bar 1 False\n"


def test_posargs():
    app = CLIApplication()

    test = app.command(posargs_func)
    runner = CliRunner()
    res = runner.invoke(test, ["foo", "--opt", "1"])
    assert res.output == "foo 1\n"


def test_varargs():
    app = CLIApplication()

    test = app.command(varargs_func)
    runner = CliRunner()
    res = runner.invoke(test, ["1", "2", "3", "--total"])
    assert res.output == "(1, 2, 3)\n6\n"

    res = runner.invoke(test, [])
    assert res.output == "()\n"
