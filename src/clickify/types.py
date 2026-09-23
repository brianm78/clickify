import io
import typing
from collections.abc import Callable
from enum import Enum, auto

type AnyCallable = Callable[..., typing.Any]
type Decorator[T: AnyCallable] = Callable[[T], T]

# Using same names as Typer for convenience
type FileText = typing.TextIO
type FileTextWrite = typing.TextIO
type FileBinaryRead = typing.BinaryIO
type FileBinaryWrite = typing.BinaryIO


@typing.final
class Inferred(Enum):
    value = auto()


@typing.final
class Unspecified(Enum):
    value = auto()
