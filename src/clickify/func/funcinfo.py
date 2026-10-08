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

    @classmethod
    def from_func(cls, func: typing.Callable[..., T]) -> FuncInfo:
        docinfo = DocInfo.from_obj(func)

        sig = inspect.signature(func)
        before_varargs = any(param.kind == inspect.Parameter.VAR_POSITIONAL for param in sig.parameters.values())

        params: list[ParamInfo] = []
        for param in sig.parameters.values():
            if param.annotation is inspect._empty:
                raise Exception(f"Unnannotated parameter in function {func}: {param.name}")

            arginfo = ParamInfo.from_param(param, docinfo, before_varargs)

            if param.kind == inspect.Parameter.VAR_POSITIONAL:
                before_varargs = False

            params.append(arginfo)
        return cls(func=func, params=params, docinfo=docinfo, return_annotation=sig.return_annotation)

    def invoke(self, **kwargs: typing.Any) -> typing.Any:
        """Wrapper that invokes func with required parameters after adapting
        to match signature.

        Expects all args to be passed by keyword.
        vararge params should be a single key with a sequence value, which will
        be passed as positional args to the function.
        """
        pos_args = []
        keyword_args = {}
        for param in self.params:
            # TODO: allow missing params?
            val = kwargs[param.name]

            if param.is_positional:
                if param.is_varargs:
                    pos_args += val  # flatten *args
                else:
                    pos_args.append(val)
            else:
                keyword_args[param.name] = val

        return self.func(*pos_args, **keyword_args)
