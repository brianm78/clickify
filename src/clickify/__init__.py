from clickify.application import CLIApplication
from clickify.func.paraminfo import ParamInfo
from clickify.handler.base import NotHandledException
from clickify.registry import HandlerRegistry
from clickify.types import ClickOptions, TypeOptions

app = CLIApplication()

# command/group decorators using default app
command = app.command

__all__ = [
    "CLIApplication",
    "command",
    "ClickOptions",
    "TypeOptions",
    "ParamInfo",
    "NotHandledException",
    "HandlerRegistry",
]
