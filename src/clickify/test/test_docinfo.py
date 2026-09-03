import typing
from collections.abc import Callable

import pytest

from clickify.docinfo import DocInfo


@pytest.fixture
def docfunc() -> typing.Iterator[Callable[..., None]]:
    """Sample func with docstring"""

    def func() -> None:
        """Docstring

        Second line of docstring

        Arguments:
            noopts: Text without shortcut
            shortonly: [-s] With shortcut
            longonly: [--long-opt] longonly text
            mixed: [-M --mixed --another]
                Text on newline
            switch: [--yes/--no -y/-n]
                Switch option
                multiple lines
        """

    yield func


def test_doc(docfunc: typing.Callable[..., None]) -> None:
    docinfo = DocInfo.from_obj(docfunc)

    assert docinfo.description == "Docstring\n\nSecond line of docstring"
    assert len(docinfo.params) == 5

    noopts = docinfo.params["noopts"]
    assert noopts.name == "noopts"
    assert noopts.long_opts == []
    assert noopts.short_opts == []
    assert noopts.description == "Text without shortcut"

    shortonly = docinfo.params["shortonly"]
    assert shortonly.name == "shortonly"
    assert shortonly.long_opts == []
    assert shortonly.short_opts == ["-s"]
    assert shortonly.description == "With shortcut"

    longonly = docinfo.params["longonly"]
    assert longonly.name == "longonly"
    assert longonly.long_opts == ["--long-opt"]
    assert longonly.description == "longonly text"

    mixed = docinfo.params["mixed"]
    assert mixed.name == "mixed"
    assert mixed.long_opts == ["--mixed", "--another"]
    assert mixed.short_opts == ["-M"]
    assert mixed.description == "Text on newline"

    switch = docinfo.params["switch"]
    assert switch.name == "switch"
    assert switch.long_opts == ["--yes/--no"]
    assert switch.short_opts == ["-y/-n"]
    assert switch.description == "Switch option\nmultiple lines"


def test_chars():
    """Check corner cases (digits, underscores etc)"""
    doc = """description
    Arguments:
        a: [-a --foo123 -0 --a_b-c]
    """
    docinfo = DocInfo.from_doc(doc)
    param = docinfo.params["a"]
    assert param.short_opts == ["-a", "-0"]
    assert param.long_opts == ["--foo123", "--a_b-c"]


def test_malformed_docstring() -> None:
    doc = """Docstring with invalid option names

        Arguments:
            foo: [{0}] docstring
        """

    # TODO: Maybe allow metavar here too.
    with pytest.raises(Exception, match="Malformed option in docstring"):
        DocInfo.from_doc(doc.format("badopt"))
    with pytest.raises(Exception, match="Malformed option in docstring"):
        DocInfo.from_doc(doc.format("-long_opt_with_single_hyphen"))
    with pytest.raises(Exception, match="Malformed option in docstring"):
        DocInfo.from_doc(doc.format("-ab"))
    with pytest.raises(Exception, match="Malformed option in docstring"):
        DocInfo.from_doc(doc.format("--"))
    with pytest.raises(Exception, match="Malformed option in docstring"):
        DocInfo.from_doc(doc.format("-"))
