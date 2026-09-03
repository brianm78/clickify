from clickify.funcinfo import FuncInfo


def varargs_func(arg: str, *args: int, kw_nodef: bool, kwonly: float = True):
    """Test func

    Arguments:
        arg: default arg
        args: vararge args
        kw_nodef: [-k/-K] required keyword
        kwonly: [--kwonly -l] optional keyword
    """
    return arg, args, kw_nodef, kwonly


def test_varargs_args():
    func = FuncInfo.from_func(varargs_func)
    arg, args, kw_nodef, kwonly = func.params
    assert arg.is_positional
    assert not arg.is_varargs
    assert arg.is_required
    assert arg.is_argument
    assert arg.name == "arg"
    assert arg.annotation is str

    assert args.is_positional
    assert args.is_varargs
    assert not args.is_required
    assert args.is_argument
    assert args.name == "args"
    assert args.annotation == list[int]

    assert not kw_nodef.is_positional
    assert not kw_nodef.is_varargs
    assert kw_nodef.is_required
    assert not kw_nodef.is_argument
    assert kw_nodef.name == "kw_nodef"
    assert kw_nodef.annotation is bool
    assert kw_nodef.long_decls == []
    assert kw_nodef.short_decls == ["-k/-K"]

    assert not kwonly.is_positional
    assert not kwonly.is_varargs
    assert not kwonly.is_required
    assert not kwonly.is_argument
    assert kwonly.default is True
    assert kwonly.name == "kwonly"
    assert kwonly.annotation is float
    assert kwonly.long_decls == ["--kwonly"]
    assert kwonly.short_decls == ["-l"]


def test_varargs_wrapper():
    funcinfo = FuncInfo.from_func(varargs_func)
    res = funcinfo.invoke(
        kwonly=2.0,
        kw_nodef=False,
        args=[1, 2, 3],
        arg="foo",
    )
    assert res == ("foo", (1, 2, 3), False, 2.0)
