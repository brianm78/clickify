from clickify import CLIApplication


@CLIApplication.with_callback()
def app():
    print("Toplevel callback")


# @app
# def toplevel_callback():
#     print("TOPLEVEL")


@app.group()
def foo(flag: bool = False):
    print(flag)


@foo.command()
def bar(arg: str):
    print("bar", arg)


print(type(foo))
print(foo.registry)
print(foo.callback)  # NONE!
app()
