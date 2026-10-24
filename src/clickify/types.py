import typing
from collections.abc import Callable
from enum import Enum, auto

type AnyCallable = Callable[..., typing.Any]
type Decorator[T: AnyCallable] = Callable[[T], T]


class TypeOptions(dict[str, typing.Any]):
    """Annotation to control how a click.type is constructed.
    May be used as an annotation to augment the value.
    Eg.
        Annotated[str, TypeOptions(case_sensitive=True)]
    """


# TODO: Allow setting decls, is_argument etc, click class (eg. subclass of Argument/Option)
# Maybe also have add_decls=[] vs replace_decls=[]
# (Or short_decls / long_decls)
class ClickOptions(dict[str, typing.Any]):
    """Augment the parameter to always pass the provided click options to the click
    Argument / Option created.
    Only valid for types handled by the builtin click option types.
    Eg.
        val: Annotated[int, ClickOpts(type=click.IntRange), TypeOptions(min=0, max=20)] = 0
    """


# File types
# Using same names as Typer for convenience
type FileText = typing.TextIO
type FileTextWrite = typing.TextIO
type FileBinaryRead = typing.BinaryIO
type FileBinaryWrite = typing.BinaryIO

# Note: Must further annotate with TypeOptions(min=??, max=??) to limit range.
type IntRange = int
type FloatRange = float
type Count = typing.Annotated[int, ClickOptions(count=True)]
# Common usecases

type Prompt[T] = T


@typing.final
class Inferred(Enum):
    value = auto()


@typing.final
class Unspecified(Enum):
    value = auto()
