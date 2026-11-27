# clickify

## Overview

A wrapper around click to allow quickly constructing a CLI just from type annotations and docstrings.
Supoports registering more complex types requesting further parameters.

Ideally, correctly annotated functions should be exposable as CLI commands just by adding the decorator.

Current Status:
Still in fairly early stages - everything should work, but still may be changing the basic interface.

### Simple Example

    @clickify.command()
    def func(arg: str, *others: str, flag: bool=False, opt: int=0):
        """Sample Func

          Arguments:
              arg: Required argument
              args: Additional args
              flag: [-f --myflag]  Flag variable
              opt: [-o] Optional int arg
        """

Will produce the equivalent of:

    @click.command()
    @click.argument("arg")
    @click.argument("args", nargs=-1)
    @click.option("flag", "--myflag", "-f", default=False, help="Flag variable", is_flag=True)
    @click.option("opt", "--opt", "-o", default=0, help="Optional int arg")
    def func(arg: str, others: list[str], flag: bool=False, opt: int=0): ...

## Features

- Convert standard python type declarations to appropriate click ParamTypes
- Converts positional-only / keyword-only and varargs args to appropriate parameters
- Parses docstring to get help and parameter decls
- Can register custom types which can be expanded into multiple parameters
- Dataclasses will be expanded into multiple parameters and constructed from them.
- Further customisation through annotations

## To-do

- Write docs
- More testing
