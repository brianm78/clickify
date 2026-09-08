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


def varargs_func(*vals: int, total: bool = False):
    """Varargs test

    Arguments:
        vals: list of ints
        total: [-t --total] Print sum of args
    """
    print(vals)
    if total:
        print(sum(vals))


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


def test_varargs():
    app = CLIApplication()

    test = app.command(varargs_func)
    runner = CliRunner()
    res = runner.invoke(test, ["1", "2", "3", "--total"])
    assert res.output == "(1, 2, 3)\n6\n"

    res = runner.invoke(test, [])
    assert res.output == "()\n"
