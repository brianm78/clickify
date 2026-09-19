import datetime
import typing
import uuid
from collections.abc import Generator, Sequence
from enum import Enum
from pathlib import Path

import click.types
import pytest

from clickify import ClickOptions
from clickify.func.paraminfo import ParamInfo
from clickify.handler.base import NotHandledException
from clickify.handler.click_annotated import ParamNameMismatch
from clickify.handler.default_registry import get_default_registry
from clickify.handler.registry import HandlerRegistry

enumtype = Enum("enumtype", "a b c")

# annotation, expected click type, argument_props, option_props
TEST_CASES: list[tuple[object, type[click.types.ParamType], dict[str, typing.Any], dict[str, typing.Any]]] = [
    (str, click.types.StringParamType, {}, {}),
    (int, click.types.IntParamType, {}, {}),
    (float, click.types.FloatParamType, {}, {}),
    (bool, click.types.BoolParamType, {}, dict(is_flag=True)),
    (Path, click.types.Path, {}, {}),
    (uuid.UUID, click.types.UUIDParameterType, {}, {}),
    (datetime.datetime, click.types.DateTime, {}, {}),
    # Sequence tests:
    (list[int], click.types.IntParamType, dict(nargs=-1), dict(multiple=True)),
    (tuple[int, ...], click.types.IntParamType, dict(nargs=-1), dict(multiple=True)),
    (tuple[int, int, int], click.types.IntParamType, dict(nargs=3), dict(nargs=3)),
    (tuple[int], click.types.IntParamType, dict(nargs=1), dict(nargs=1)),
    (Sequence[int], click.types.IntParamType, dict(nargs=-1), dict(multiple=True)),
    # Annotation tests: Options replace options, while annotating with parameter should replace it entirely.
    (typing.Annotated[int, ClickOptions(type=str)], click.types.StringParamType, {}, {}),
    (typing.Annotated[str, click.Option(["test", "--foo"], type=click.types.BOOL)], click.types.BoolParamType, {}, {}),
    #
    (typing.Literal["a", "b"], click.types.Choice, {}, {}),
    (enumtype, click.types.Choice, {}, {}),
]

# Cases expected to be rejected
FAILURE_CASES: list[object] = [
    tuple[int, float],  # We don't support mixed types
    complex,  # Unregistered type
]


@pytest.fixture
def registry() -> Generator[HandlerRegistry]:
    yield get_default_registry()


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
    handler = registry.handle_param(info)
    assert handler is not None
    assert len(handler.params) == 1
    assert isinstance(handler.params[0].type, expected)
    prop_dict = expected_arg_props if is_arg else expected_opt_props
    for prop, val in prop_dict.items():
        assert getattr(handler.params[0], prop) == val


@pytest.mark.parametrize("annotation", FAILURE_CASES)
@pytest.mark.parametrize("is_arg", [True, False])
def test_failures(registry: HandlerRegistry, annotation: object, is_arg: bool) -> None:
    info = ParamInfo("test", annotation, is_argument=is_arg)
    with pytest.raises(NotHandledException):
        _ = registry.handle_param(info)


def test_annotated_wrongname(registry: HandlerRegistry):
    """Annotated arg must match name of param"""

    annotation = typing.Annotated[str, click.Option(["--bar"], type=click.types.BOOL)]
    info = ParamInfo("foo", annotation, is_argument=True)
    with pytest.raises(ParamNameMismatch):
        _ = registry.handle_param(info)

    annotation = typing.Annotated[str, click.Option(["foo", "--bar"], type=click.types.BOOL)]
    info = ParamInfo("foo", annotation, is_argument=True)
    _ = registry.handle_param(info)
