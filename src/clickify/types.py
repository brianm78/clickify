import typing
from collections.abc import Callable
from enum import Enum, auto

type AnyCallable = Callable[..., typing.Any]
type Decorator[T: AnyCallable] = Callable[[T], T]


@typing.final
class Inferred(Enum):
    value = auto()


@typing.final
class Unspecified(Enum):
    value = auto()
