import inspect
import typing
from dataclasses import _MISSING_TYPE, Field, dataclass, field, replace

import click
from click._utils import UNSET

from clickify import utils
from clickify.func.docinfo import DocInfo


class UnsupportedParameterType(Exception):
    pass


@dataclass
class ParamInfo:
    """Argument info obtained from function signature"""

    name: str
    annotation: object

    is_argument: bool = False

    # Note: is_positional indicates passed positionally in the function.  Not neccessarily Argument vs Option
    is_positional: bool = False
    is_varargs: bool = False

    default: typing.Any = UNSET

    short_decls: list[str] = field(default_factory=list)
    long_decls: list[str] = field(default_factory=list)

    # Default options.
    click_defaults: dict[str, typing.Any] = field(default_factory=dict)

    def with_click_defaults(self, **opts: typing.Any):
        return replace(self, click_defaults=self.click_defaults | opts)

    @property
    def decls(self):
        decls = [self.name]
        # Create a default long option if none defined.
        if not self.is_argument and not self.long_decls:
            decls.append(utils.click_option_name(self.name))
        decls += self.long_decls
        decls += self.short_decls
        return decls

    @classmethod
    def from_click_param(cls, param: click.Parameter) -> typing.Self:
        is_arg = False
        short_decls, long_decls = [], []
        if isinstance(param, click.Option):
            is_arg = True
            short_decls = param.secondary_opts
            long_decls = param.opts

        return cls(
            name=param.name,
            annotation=object,
            is_argument=is_arg,
            is_varargs=False,
            default=param.default,
            short_decls=short_decls,
            long_decls=long_decls,
            click_defaults={},
        )

    @classmethod
    def from_dataclass_field(cls, field: Field, docinfo: DocInfo) -> typing.Self:
        """Construct from dataclass field.

        All items treated as Options
        """

        arginfo = cls(name=field.name, annotation=field.type)

        if isinstance(field.default, _MISSING_TYPE):
            if isinstance(field.default_factory, _MISSING_TYPE):
                arginfo.click_defaults["required"] = True
            else:
                arginfo.default = field.default_factory()
        else:
            arginfo.default = field.default

        param_doc = docinfo.params.get(field.name)
        if param_doc is not None:
            arginfo.click_defaults["help"] = param_doc.description
            arginfo.long_decls = param_doc.long_opts
            arginfo.short_decls = param_doc.short_opts
        return arginfo

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
        )

        if param.default is inspect._empty:
            arginfo.click_defaults["required"] = True
            arginfo.is_argument = False
        else:
            arginfo.default = param.default
            arginfo.is_argument = True

        match param.kind:
            case inspect.Parameter.VAR_KEYWORD:
                raise UnsupportedParameterType("**kwargs not supported")

            case inspect.Parameter.VAR_POSITIONAL:
                arginfo.is_varargs = True
                arginfo.is_positional = True
                arginfo.is_argument = True
                arginfo.click_defaults["required"] = False
                arginfo.click_defaults["nargs"] = -1
                arginfo.annotation = list[arginfo.annotation]  # type: ignore
                assert param.default is inspect._empty

            case inspect.Parameter.POSITIONAL_ONLY:
                # Params before *args don't get marked as POSITIONAL_ONLY, even though they effectively are.
                arginfo.is_positional = True
                arginfo.is_argument = True

            case _ if before_varargs:
                arginfo.is_positional = True
                arginfo.is_argument = True

            case inspect.Parameter.POSITIONAL_OR_KEYWORD:
                # Default to option unless no default
                arginfo.is_argument = param.default is inspect._empty

            case inspect.Parameter.KEYWORD_ONLY:
                arginfo.is_argument = False

        param_doc = docinfo.params.get(param.name)
        if param_doc is not None:
            arginfo.click_defaults["help"] = param_doc.description
            arginfo.long_decls = param_doc.long_opts
            arginfo.short_decls = param_doc.short_opts

        return arginfo

    def to_click_parameter(
        self,
        **kwargs: typing.Any,
    ):
        """Create a click parameter from this arg, with additional options provided.
        Note: Specified options may be overridden if click_overrides is set."""
        cls: type[click.Parameter] = click.Argument if self.is_argument else click.Option

        cls = click.Argument if self.is_argument else click.Option
        opts = self.click_defaults | {"default": self.default}
        opts.update(kwargs)
        return cls(self.decls, **opts)
