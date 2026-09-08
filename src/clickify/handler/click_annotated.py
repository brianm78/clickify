"""
Handle an Annotated[T, click.Option()] style annotation as using the given parameter
"""

import click
import click.types

from clickify.funcinfo import ParamInfo
from clickify.handler.base import NotHandled, ParamHandler
from clickify.typeutil import unwrap_annotation


# TODO: Allow ClickOpts(...) to augment an existing item?
class ClickAnnotatedHandler(ParamHandler):
    def get_params(self, info: ParamInfo) -> list[click.Parameter]:
        ann, meta = unwrap_annotation(info.annotation, False, False)
        for elem in meta:
            if isinstance(elem, click.Parameter):
                return [elem]
        raise NotHandled()
