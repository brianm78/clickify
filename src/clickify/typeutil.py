import types
import typing

from clickify.utils import AnnotationType


def unwrap_annotation(
    annotation: AnnotationType,
    resolve_alias: bool = True,
    resolve_generic: bool = True,
    max_depth: int = 100,
) -> tuple[object, list[typing.Any]]:
    """Strip Annotated[], and optionally TypeAlias and GenericAliases and return the underlying type.

    Arguments:
        resolve_alias:
            If True, aliases will be converted to the aliased type.
            Otherwise will return the first alias we reach.
        resolve_generic:
            If True generic arguments are ignored, and the origin type is resolved.
            Eg. list[str] becomes just list.
            If False, returns the generic alias
        max_depth:
            Recursive types have the potential to trigger an infinite loop when resolving.
            To prevent this, a limit on how many resolutions are performed is added, which
            may be altered if there are overly deep type aliasing.  A value of -1 will remove
            this limit and recurse as deep as neccessary.

    Returns:
        The resolved type/annotation, and any metadata found on Annotated[] annotations.
    """
    original = annotation
    metadata = []
    for i in range(max_depth):
        if typing.get_origin(annotation) is typing.Annotated:
            annotation, *metadata = typing.get_args(annotation)

        elif resolve_alias and isinstance(annotation, typing.TypeAliasType):
            annotation = annotation.__value__

        elif resolve_generic and isinstance(annotation, types.GenericAlias):
            annotation = typing.get_origin(annotation)
        else:
            break
    else:
        # Potentially recursive type definition
        # Eg. type T = U; type U = T
        raise Exception(f"Maximum limit on type recursion exceeded: Possibly a recursive type: {original}")
    return annotation, metadata
