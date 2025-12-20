from __future__ import annotations

import importlib
import inspect
import logging
import pkgutil
from typing import TypeVar
from types import ModuleType

logger = logging.getLogger(__name__)


def get_module_names(package_name: str) -> tuple[str, ...]:
    try:
        package = importlib.import_module(package_name)
        modules = pkgutil.iter_modules(package.__path__)
        return tuple(f'{package_name}.{module.name}' for module in modules)
    except ModuleNotFoundError:
        return ()


T = TypeVar('T', bound=type)


def get_classes(module: str | ModuleType, parent_class: T | None = None) -> tuple[T, ...]:
    if not isinstance(module, ModuleType):
        try:
            module = importlib.import_module(module)
        except ModuleNotFoundError:
            return ()

    classes = []
    for name, value in inspect.getmembers(module, inspect.isclass):
        if value.__module__ != module.__name__:
            continue
        if parent_class and not issubclass(value, parent_class):
            continue
        classes.append(value)
    return tuple(classes)
