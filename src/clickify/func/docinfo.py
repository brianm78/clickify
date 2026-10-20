"""
Fetch parameter info from a docstring.
"""

import inspect
import re
import typing
from dataclasses import dataclass

import docstring_parser

# TODO: Also parse metavar.  Eg.  "[-s STRING]" / "[-s --string -y STRING]"

# Anything at the start of the string within "[", "]" pairs is considered a list of options.
_opt_group_re = re.compile(r"\s*\[([^\]]*)\](.*)", re.DOTALL)

# Either single char: "-x", "-0", or on/off format ("-x/-y")
_short_opt_re = re.compile(r"\-[a-zA-Z\d](?:/\-[a-zA-Z\d])?$")

# "--longopt" or "--yes/--no" style
# Allow alphanumerics and "-" from second char on
_long_opt_re = re.compile(r"\-\-[\w][\w\-]*(?:/\-\-[\w][\w\-]*)?$")


@dataclass
class ParameterDocInfo:
    name: str
    description: str
    short_opts: list[str]
    long_opts: list[str]

    @classmethod
    def from_doc_param(cls, param: docstring_parser.DocstringParam, ignore_errors: bool = False) -> typing.Self:
        """Parse docstring for parameter, seperating out long/short option decls.

        Arguments:
            param:
                Parameter to parse
            ignore_errors:
                If True, ignores malformed options
        """

        description = "" if param.description is None else param.description

        short_opts: list[str] = []
        long_opts: list[str] = []

        if m := _opt_group_re.match(description):
            # Options found
            opts, description = m.groups()
            for opt in opts.split():
                if _short_opt_re.match(opt):
                    short_opts.append(opt)
                elif m := _long_opt_re.match(opt):
                    long_opts.append(opt)
                elif not ignore_errors:
                    raise Exception(f"Malformed option in docstring: {opt!r}")

        return cls(
            name=param.arg_name,
            description=description.strip(),
            long_opts=long_opts,
            short_opts=short_opts,
        )


@dataclass
class DocInfo:
    description: str | None
    params: dict[str, ParameterDocInfo]

    @classmethod
    def from_doc(cls, docstring: str | None) -> typing.Self:
        """Parse function / class docstring into dict of parameter info, and remaining docstring."""
        if docstring is None:
            return cls(None, {})

        doc = docstring_parser.parse(docstring)
        return cls(
            doc.description,
            {p.arg_name: ParameterDocInfo.from_doc_param(p) for p in doc.params},
        )

    @classmethod
    def from_obj(cls, obj: typing.Callable[..., typing.Any] | type) -> typing.Self:
        """Parse function / class docstring into dict of parameter info, and remaining docstring."""
        return cls.from_doc(inspect.getdoc(obj))
