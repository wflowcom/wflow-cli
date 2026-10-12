"""One module per API area. operations() lists every operation those modules define."""

import inspect
import pkgutil
from collections.abc import Awaitable, Callable
from importlib import import_module
from typing import Any

Operation = Callable[..., Awaitable[Any]]


def operations() -> list[tuple[str, Operation]]:
    found: list[tuple[str, Operation]] = []
    for info in sorted(pkgutil.iter_modules(__path__), key=lambda module: module.name):
        module = import_module(f"{__name__}.{info.name}")
        for name, value in sorted(vars(module).items()):
            if name.startswith("_") or not inspect.iscoroutinefunction(value):
                continue
            if value.__module__ == module.__name__:
                found.append((info.name, value))
    return found
