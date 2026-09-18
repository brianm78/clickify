from clickify.application import CLIApplication
from clickify.func.paraminfo import ParamInfo
from clickify.handler.base import NotHandledException
from clickify.handler.click_annotated import ClickOptions
from clickify.handler.registry import HandlerRegistry

app = CLIApplication()

# command/group decorators using default app
command = app.command

__all__ = ["CLIApplication", "command", "ClickOptions", "ParamInfo", "NotHandledException", "HandlerRegistry"]
