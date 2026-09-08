import datetime
import typing
import uuid
from collections.abc import Generator, Sequence
from pathlib import Path

import click.types
import pytest

from clickify.funcinfo import ParamInfo
from clickify.handler.default_registry import get_default
from clickify.handler.registry import HandlerRegistry, UnhandledAnnotationException

# annotation, expected click type, argument_props, option_props
TEST_CASES: list[tuple[object, type[click.types.ParamType], dict[str, typing.Any], dict[str, typing.Any]]] = [
    (str, click.types.StringParamType, {}, {}),
    (int, click.types.IntParamType, {}, {}),
    (float, click.types.FloatParamType, {}, {}),
    (bool, click.types.BoolParamType, {}, dict(is_flag=True)),
    (Path, click.types.Path, {}, {}),
    (uuid.UUID, click.types.UUIDParameterType, {}, {}),
    (datetime.datetime, click.types.DateTime, {}, {}),
    (list[int], click.types.IntParamType, dict(nargs=-1), dict(multiple=True)),
    (tuple[int, ...], click.types.IntParamType, dict(nargs=-1), dict(multiple=True)),
    (tuple[int, int, int], click.types.IntParamType, dict(nargs=3), dict(nargs=3)),
    (tuple[int], click.types.IntParamType, dict(nargs=1), dict(nargs=1)),
    (Sequence[int], click.types.IntParamType, dict(nargs=-1), dict(multiple=True)),
]

# Cases expected to be rejected
FAILURE_CASES: list[object] = [
    tuple[int, float],
    complex,
]


@pytest.fixture
def registry() -> Generator[HandlerRegistry]:
    yield get_default()


@pytest.mark.parametrize("annotation,expected,expected_arg_props,expected_opt_props", TEST_CASES)
@pytest.mark.parametrize("is_arg", [True, False])
def test_args(
    registry: HandlerRegistry,
    annotation: object,
    expected: type[click.types.ParamType],
    expected_arg_props: dict[str, typing.Any],
    expected_opt_props: dict[str, typing.Any],
    is_arg: bool,
):
    """Test basic lookups: annotation -> parameter type"""
    info = ParamInfo("test", annotation, is_argument=is_arg)
    params = list(registry.get_params(info))
    assert len(params) == 1
    assert isinstance(params[0].type, expected)
    prop_dict = expected_arg_props if is_arg else expected_opt_props
    for prop, val in prop_dict.items():
        assert getattr(params[0], prop) == val


@pytest.mark.parametrize("annotation", FAILURE_CASES)
@pytest.mark.parametrize("is_arg", [True, False])
def test_failures(registry: HandlerRegistry, annotation: object, is_arg: bool) -> None:
    info = ParamInfo("test", annotation, is_argument=is_arg)
    with pytest.raises(UnhandledAnnotationException):
        _ = registry.get_params(info)


def test_annotated(registry: HandlerRegistry):
    """Annotation should override param.  Note: Even includes stuff like name"""

    annotation = typing.Annotated[str, click.Option(["--foo"], type=click.types.BOOL)]
    info = ParamInfo("test", annotation, is_argument=True)
    params = registry.get_params(info)
    assert len(params) == 1
    param = params[0]
    assert isinstance(param, click.Option)
    assert param.name == "foo"
    assert isinstance(param.type, click.types.BoolParamType)
