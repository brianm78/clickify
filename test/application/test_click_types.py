"""
Check basic click types work.
(Choice covered in test_choice)
"""

import typing
import uuid
from datetime import datetime
from pathlib import Path

import click
import pytest
from click.testing import CliRunner

from clickify import CLIApplication
from clickify.types import (
    AnyCallable,
    FileBinaryRead,
    FileBinaryWrite,
    FileText,
    FileTextWrite,
    FloatRange,
    IntRange,
    TypeOptions,
)

type IntRange_0_10 = typing.Annotated[IntRange, TypeOptions(min=0, max=10)]
type FloatRange_0_10 = typing.Annotated[FloatRange, TypeOptions(min=0.0, max=10.0)]


# TODO: Test File
def bool_func(arg: bool = False, /, opt: bool = False):
    assert isinstance(arg, bool)
    assert isinstance(opt, bool)
    click.echo(f"{arg} {opt}")


def int_func(arg: int = 0, /, opt: int = 1):
    assert isinstance(arg, int)
    assert isinstance(opt, int)
    click.echo(f"{arg} {opt}")


def intrange_func(arg: IntRange_0_10 = 0, /, opt: IntRange_0_10 = 1):
    assert isinstance(arg, int)
    assert isinstance(opt, int)
    click.echo(f"{arg} {opt}")


def float_func(arg: float = 0.0, /, opt: float = 1.0):
    assert isinstance(arg, float)
    assert isinstance(opt, float)
    click.echo(f"{arg} {opt}")


def floatrange_func(arg: FloatRange_0_10 = 0.0, /, opt: FloatRange_0_10 = 1.0):
    assert isinstance(arg, float)
    assert isinstance(opt, float)
    click.echo(f"{arg} {opt}")


def str_func(arg: str = "a", /, opt: str = "b"):
    assert isinstance(arg, str)
    assert isinstance(opt, str)
    click.echo(f"{arg} {opt}")


def path_func(arg: Path = Path("/tmp/a"), /, opt: Path = Path("/tmp/b")):
    assert isinstance(arg, Path)
    assert isinstance(opt, Path)
    click.echo(f"{arg.name} {opt.name}")


def datetime_func(arg: datetime = datetime(2000, 1, 1), /, opt: datetime = datetime(2001, 1, 1)):
    assert isinstance(arg, datetime)
    assert isinstance(opt, datetime)
    click.echo(f"{arg.year} {opt.year}")


default_uuid1, default_uuid2, uuid3, uuid4 = uuid.uuid4(), uuid.uuid4(), uuid.uuid4(), uuid.uuid4()


def uuid_func(arg: uuid.UUID = default_uuid1, /, opt: uuid.UUID = default_uuid2):
    click.echo(f"{arg.hex} {opt.hex}")


# Check each type as both arg and option
# Function, args, expected text
TESTCASES: list[tuple[AnyCallable, list[str], str]] = [
    # str
    (str_func, [], "a b\n"),
    (str_func, ["x"], "x b\n"),
    (str_func, ["--opt", "y"], "a y\n"),
    (str_func, ["x", "--opt", "y"], "x y\n"),
    # Bool: Used as flag for options, otherwise arg.
    (bool_func, [], "False False\n"),
    (bool_func, ["True"], "True False\n"),
    (bool_func, ["--opt"], "False True\n"),
    (bool_func, ["True", "--opt"], "True True\n"),
    # int
    (int_func, [], "0 1\n"),
    (int_func, ["2"], "2 1\n"),
    (int_func, ["--opt", "3"], "0 3\n"),
    (int_func, ["5", "--opt", "6"], "5 6\n"),
    # # Intrange
    (intrange_func, [], "0 1\n"),
    (intrange_func, ["2"], "2 1\n"),
    (intrange_func, ["--opt", "3"], "0 3\n"),
    (intrange_func, ["5", "--opt", "6"], "5 6\n"),
    # float
    (float_func, [], "0.0 1.0\n"),
    (float_func, ["2"], "2.0 1.0\n"),
    (float_func, ["--opt", "3.5"], "0.0 3.5\n"),
    (float_func, ["0.5", "--opt", "3"], "0.5 3.0\n"),
    # floatrange
    (floatrange_func, [], "0.0 1.0\n"),
    (floatrange_func, ["2"], "2.0 1.0\n"),
    (floatrange_func, ["--opt", "3.5"], "0.0 3.5\n"),
    (floatrange_func, ["0.5", "--opt", "3"], "0.5 3.0\n"),
    # path
    (path_func, [], "a b\n"),
    (path_func, ["/tmp/c"], "c b\n"),
    (path_func, ["--opt", "/tmp/d"], "a d\n"),
    (path_func, ["/tmp/c", "--opt", "/tmp/d"], "c d\n"),
    # datetime
    (datetime_func, [], "2000 2001\n"),
    (datetime_func, ["2010-02-03"], "2010 2001\n"),
    (datetime_func, ["--opt", "2020-02-03"], "2000 2020\n"),
    (datetime_func, ["2010-02-03", "--opt", "2020-02-03"], "2010 2020\n"),
    # uuid
    (uuid_func, [], f"{default_uuid1.hex} {default_uuid2.hex}\n"),
    (uuid_func, [uuid3.hex], f"{uuid3.hex} {default_uuid2.hex}\n"),
    (uuid_func, ["--opt", uuid4.hex], f"{default_uuid1.hex} {uuid4.hex}\n"),
    (uuid_func, [uuid3.hex, "--opt", uuid4.hex], f"{uuid3.hex} {uuid4.hex}\n"),
]

FAIL_CASES = [
    # Range values out of bounds
    (intrange_func, ["20"]),
    (intrange_func, ["--opt", "-5"]),
    (floatrange_func, ["20.0"]),
    (floatrange_func, ["--opt", "-5.0"]),
]


@pytest.mark.parametrize("func, args", FAIL_CASES)
def test_failcases(app: CLIApplication, runner: CliRunner, func: AnyCallable, args: list[str]):
    cmd = app.command(func)
    res = runner.invoke(cmd, args)
    assert res.exit_code != 0


@pytest.mark.parametrize("func, args, expected", TESTCASES)
def test_testcases(app: CLIApplication, runner: CliRunner, func: AnyCallable, args: list[str], expected: str):

    cmd = app.command(func)

    res = runner.invoke(cmd, args)
    assert res.exit_code == 0
    assert res.output == expected


def test_context(app: CLIApplication, runner: CliRunner):
    @app.command()
    def with_context(ctx: click.Context):
        print(isinstance(ctx, click.Context))

    res = runner.invoke(with_context, [])
    assert res.exit_code == 0
    assert res.output == "True\n"


def test_file_read_text(app: CLIApplication, runner: CliRunner, tmp_path: Path):

    @app.command()
    def file(f: FileText):
        click.echo(repr(f.read()))

    path = tmp_path / "file.txt"
    path.write_text("foo")

    res = runner.invoke(file, [str(path)])
    assert res.exit_code == 0
    assert res.output == "'foo'\n"


def test_file_write_text(app: CLIApplication, runner: CliRunner, tmp_path: Path):

    @app.command()
    def file(f: FileTextWrite):
        f.write("foo")

    path = tmp_path / "file.txt"

    res = runner.invoke(file, [str(path)])
    assert res.exit_code == 0
    assert path.exists()
    assert path.read_text() == "foo"


def test_file_read_binary(app: CLIApplication, runner: CliRunner, tmp_path: Path):

    @app.command()
    def file(f: FileBinaryRead):
        click.echo(repr(f.read()))

    path = tmp_path / "file.txt"
    path.write_bytes(b"foo")

    res = runner.invoke(file, [str(path)])
    assert res.exit_code == 0
    assert res.output == "b'foo'\n"


def test_file_write_binary(app: CLIApplication, runner: CliRunner, tmp_path: Path):

    @app.command()
    def file(f: FileBinaryWrite):
        f.write(b"foo")

    path = tmp_path / "file.txt"

    res = runner.invoke(file, [str(path)])
    assert res.exit_code == 0
    assert path.exists()
    assert path.read_bytes() == b"foo"
