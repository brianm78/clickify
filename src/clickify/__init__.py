from clickify.application import CLIApplication

app = CLIApplication()

# command/group decorators using default app
command = app.command

__all__ = [
    "CLIApplication",
    "command",
]
