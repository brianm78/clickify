from clickify.application import CLIApplication
from clickify.func.paraminfo import ParamInfo
from clickify.handler.click_annotated import ClickOptions

app = CLIApplication()

# command/group decorators using default app
command = app.command

__all__ = ["CLIApplication", "command", "ClickOptions", "ParamInfo"]
