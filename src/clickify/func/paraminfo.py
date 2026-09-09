import inspect
import typing
from dataclasses import dataclass, field

import click
from click._utils import UNSET

from clickify import utils
from clickify.func.docinfo import DocInfo


@dataclass
class ParamInfo:
    """Argument info obtained from function signature"""

    name: str
    annotation: object

    # Set to true if positional-only, or may be positional, but no default.
    is_argument: bool = False
    is_positional: bool = False
    is_varargs: bool = False
    is_required: bool = False

    # nargs: A value of -1 should be converted to multiple=True for options.
    nargs: int | None = None

    default: typing.Any | typing.Literal[UNSET] = UNSET
    help: str | None = None
    short_decls: list[str] = field(default_factory=list)
    long_decls: list[str] = field(default_factory=list)

    @property
    def decls(self):
        decls = [self.name]
        # Create a default long option if none defined.
        if not self.is_argument and not self.long_decls and not self.short_decls:
            decls.append(utils.click_option_name(self.name))
        decls += self.long_decls
        decls += self.short_decls
        return decls

    @classmethod
    def from_param(
        cls,
        param: inspect.Parameter,
        docinfo: DocInfo,
        before_varargs: bool = False,
    ) -> typing.Self:
        """Construct arginfo from parameter definition + docstring

        Arguments:
            param:
                parameter to introspect
            docinfo:
                DocInfo object for parsed docstring of function.
            before_varargs:
                Parameters before a *args parameter are implicitly positional,
                but don't get set to VAR_POSITIONAL.
                Pass True if this parameter occurs before such an arg to ensure it is
                treated as such.
        """

        arginfo = cls(
            name=param.name,
            annotation=param.annotation,
            default=UNSET if param.default is inspect._empty else param.default,
            is_required=param.default is inspect._empty,
        )

        match param.kind:
            case inspect.Parameter.VAR_KEYWORD:
                raise Exception("**kwargs not supported")

            case inspect.Parameter.VAR_POSITIONAL:
                arginfo.is_varargs = True  # Needed?
                arginfo.is_positional = True
                arginfo.is_argument = True
                arginfo.is_required = False
                arginfo.annotation = list[arginfo.annotation]  # type: ignore
                arginfo.nargs = -1
                assert arginfo.default is UNSET
            case inspect.Parameter.POSITIONAL_ONLY:
                # Params before *args don't get marked as POSITIONAL_ONLY, even though they effectively are.
                arginfo.is_positional = True
                arginfo.is_argument = True

            case _ if before_varargs:
                arginfo.is_positional = True
                arginfo.is_argument = True

            case inspect.Parameter.POSITIONAL_OR_KEYWORD:
                # Default to option unless no default
                arginfo.is_argument = arginfo.default is UNSET
            case inspect.Parameter.KEYWORD_ONLY:
                arginfo.is_argument = False

        param_doc = docinfo.params.get(param.name)
        if param_doc is not None:
            arginfo.help = param_doc.description
            arginfo.long_decls = param_doc.long_opts
            arginfo.short_decls = param_doc.short_opts

        return arginfo

    def to_click_parameter(
        self,
        click_type: click.ParamType,
        option_specific_opts: dict[str, typing.Any] | None = None,
        **kwargs: typing.Any,
    ):
        """Create a click parameter from this arg, with potential overrides

        Arguments:
            click_type:  The click.ParamType to use
            option_specific_opts:
                And extra parameters, to be used only when this is a click.Option, rather than argument
            kwargs:
                Any other parameters are passed to the click.Option/Argument constructor, and will
                override any defaults set on the ParamInfo object.
        """
        cls: type[click.Parameter] = click.Argument if self.is_argument else click.Option
        opts: dict[str, typing.Any] = {"required": self.is_required, "help": self.help}

        if self.is_argument:
            cls = click.Argument
            if self.nargs is not None:
                opts["nargs"] = self.nargs
        else:
            cls = click.Option

            if self.nargs is not None:
                if self.nargs == -1:
                    opts["multiple"] = True
                else:
                    opts["nargs"] = self.nargs
            if option_specific_opts:
                opts.update(option_specific_opts)

        opts.update(kwargs)
        return cls(self.decls, type=click_type, **opts)
