"""
Handle parsing function signature and get information required to convert parameters
into click, and create a wrapper.
"""

import inspect
import typing
from dataclasses import dataclass

from clickify.func.docinfo import DocInfo
from clickify.func.paraminfo import ParamInfo
from clickify.utils import AnnotationType


@dataclass
class FuncInfo[T]:
    func: typing.Callable[..., T]
    params: list[ParamInfo]
    docinfo: DocInfo
    return_annotation: AnnotationType | type[inspect._empty]
    allow_unspecified_kwargs: bool = False

    @classmethod
    def from_func[U](cls, func: typing.Callable[..., U], ignore_unsupported: bool = True) -> FuncInfo[U]:
        docinfo = DocInfo.from_obj(func)

        sig = inspect.signature(func)
        before_varargs = any(param.kind == inspect.Parameter.VAR_POSITIONAL for param in sig.parameters.values())

        allow_unspecified_kwargs = False
        params: list[ParamInfo] = []
        for param in sig.parameters.values():
            # If **kwargs occurs, allow any args to be passed, but don't introspect it
            if param.kind == inspect.Parameter.VAR_KEYWORD:
                allow_unspecified_kwargs = True
                continue

            arginfo = ParamInfo.from_param(param, docinfo, before_varargs)
            if param.kind == inspect.Parameter.VAR_POSITIONAL:
                before_varargs = False

            params.append(arginfo)
        return cls(
            func=func,
            params=params,
            docinfo=docinfo,
            return_annotation=sig.return_annotation,
            allow_unspecified_kwargs=allow_unspecified_kwargs,
        )

    def invoke(self, **kwargs: typing.Any) -> typing.Any:
        """Wrapper that invokes func with required parameters after adapting
        to match signature.

        Expects all args to be passed by keyword.
        If not passed in kwargs, will not be provided to function.
        vararge params should be a single key with a sequence value, which will
        be passed as positional args to the function.
        """
        pos_args: list[typing.Any] = []
        keyword_args: dict[str, typing.Any] = {}
        for param in self.params:
            if param.name not in kwargs:
                continue

            val = kwargs.pop(param.name)

            if param.is_positional:
                if param.is_varargs:
                    pos_args += val  # flatten *args
                else:
                    pos_args.append(val)
            else:
                keyword_args[param.name] = val

        # If **kwargs present, pass remaining through directly.
        # Otherwise raise if anything is left
        if kwargs and not self.allow_unspecified_kwargs:
            raise Exception(f"Unexpected keyword arguments: {kwargs}")

        return self.func(*pos_args, **keyword_args, **kwargs)
