"""
Handle parsing function signature and get information required to convert parameters
into click, and create a wrapper.
"""

import inspect
import typing
from dataclasses import dataclass

from clickify.func.docinfo import DocInfo
from clickify.func.paraminfo import ParamInfo, UnsupportedParameterType
from clickify.utils import AnnotationType


@dataclass
class FuncInfo[T]:
    func: typing.Callable[..., T]
    params: list[ParamInfo]
    docinfo: DocInfo
    return_annotation: AnnotationType | type[inspect._empty]

    @classmethod
    def from_func[U](cls, func: typing.Callable[..., U], ignore_unsupported: bool = True) -> FuncInfo[U]:
        docinfo = DocInfo.from_obj(func)

        sig = inspect.signature(func)
        before_varargs = any(param.kind == inspect.Parameter.VAR_POSITIONAL for param in sig.parameters.values())

        params: list[ParamInfo] = []
        for param in sig.parameters.values():
            try:
                arginfo = ParamInfo.from_param(param, docinfo, before_varargs)
            except UnsupportedParameterType:
                if not ignore_unsupported:
                    raise
                # If **kwargs occurs, just ignore it.
                continue

            if param.kind == inspect.Parameter.VAR_POSITIONAL:
                before_varargs = False

            params.append(arginfo)
        return cls(func=func, params=params, docinfo=docinfo, return_annotation=sig.return_annotation)

    def invoke(self, **kwargs: typing.Any) -> typing.Any:
        """Wrapper that invokes func with required parameters after adapting
        to match signature.

        Expects all args to be passed by keyword.
        If not passed in kwargs, will not be provided to function.
        vararge params should be a single key with a sequence value, which will
        be passed as positional args to the function.
        """
        pos_args = []
        keyword_args = {}
        for param in self.params:
            if param.name not in kwargs:
                continue

            val = kwargs[param.name]

            if param.is_positional:
                if param.is_varargs:
                    pos_args += val  # flatten *args
                else:
                    pos_args.append(val)
            else:
                keyword_args[param.name] = val

        return self.func(*pos_args, **keyword_args)
