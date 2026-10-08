"""Argument validation for every operation, so a direct call is checked as strictly as a schema-validated one."""

import functools
import inspect
from collections.abc import Awaitable, Callable

from pydantic import ConfigDict, ValidationError, validate_call

from wflow_api.errors import WflowError


def _problems(error: ValidationError) -> str:
    return "; ".join(f"{'.'.join(map(str, e['loc']))}: {e['msg']}" if e["loc"] else e["msg"] for e in error.errors())


def operation[**P, R](fn: Callable[P, Awaitable[R]]) -> Callable[P, Awaitable[R]]:
    def start(*args: P.args, **kwargs: P.kwargs) -> Awaitable[R]:
        return fn(*args, **kwargs)

    functools.update_wrapper(start, fn)

    @functools.cache
    def validator() -> tuple[inspect.Signature, Callable[..., Awaitable[R]]]:
        return inspect.signature(fn), validate_call(config=ConfigDict(arbitrary_types_allowed=True))(start)

    @functools.wraps(fn)
    async def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        signature, validated = validator()
        try:
            pending = validated(**signature.bind(*args, **kwargs).arguments)
        except TypeError as error:
            raise WflowError(f"{fn.__name__}: invalid arguments. {error}") from None
        except ValidationError as error:
            raise WflowError(f"{fn.__name__}: invalid arguments. {_problems(error)}") from None
        try:
            return await pending
        except ValidationError as error:
            raise WflowError(f"{fn.__name__}: wflow answered in an unexpected shape. {_problems(error)}") from error

    return wrapper
