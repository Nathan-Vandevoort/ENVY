from pydantic import BaseModel
from abc import ABC, abstractmethod


class PluginData(BaseModel, ABC):
    """
    The base class for PluginData.

    Plugin data is an interface for storing arbitrary data a plugin
    would need to do it's job.
    """

    pass


class Plugin(ABC):
    """
    The base class for a plugin.

    A plugin is anything called by the envy client to do work.
    Every job will point to a plugin to process that job.
    """

    def __init__(self, name: str) -> None:
        self.name = name
        self.data: PluginData | None = None

    def set_plugin_data(self, data: PluginData) -> None:
        self.data = data

    @abstractmethod
    def start(self) -> None:
        if not self.data:
            raise AttributeError(f"PluginData was never provided. make sure call set_plugin_data before calling start.")

    @abstractmethod
    def stop(self) -> None: ...
