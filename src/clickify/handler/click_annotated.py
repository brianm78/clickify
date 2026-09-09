"""
Handle an Annotated[T, click.Option()] style annotation as using the given parameter
"""

import click
import click.types

from clickify.func.paraminfo import ParamInfo
from clickify.handler.base import NotHandled, ParamHandler
from clickify.typeutil import unwrap_annotation


class ClickOption:
    def __init__(self, **kwargs):
        """Augment the parameter to always pass the provided click options.
        Eg.

            val: Annotated[int, ClickOpts(min=0, max=20)] = 0
        """


# TODO: Allow ClickOpts(...) to augment an existing item?
# NOTE: If someone annotates with a different (or no) name, won't
# match with arg.  Should we force the same name?  Check and raise error?
class ClickAnnotatedHandler(ParamHandler):
    def get_params(self, info: ParamInfo) -> list[click.Parameter]:
        ann, meta = unwrap_annotation(info.annotation, False, False)
        for elem in meta:
            if isinstance(elem, click.Parameter):
                # TODO: Check name matches?
                return [elem]
        raise NotHandled()
