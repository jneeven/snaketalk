from __future__ import annotations

import logging
import re
from abc import ABC
from collections import defaultdict
from typing import Dict, Sequence

from snaketalk.driver import Driver
from snaketalk.function import Function, MessageFunction, listen_to
from snaketalk.settings import Settings
from snaketalk.wrappers import EventWrapper, Message


class Plugin(ABC):
    """A Plugin is a self-contained class that defines what functions should be executed
    given different inputs.

    It will be called by the MessageHandler whenever one of its listeners is triggered,
    but execution of the corresponding function is handled by the plugin itself. This
    way, you can implement multithreading or multiprocessing as desired.
    """

    def __init__(self):
        self.driver = None
        self.settings = None
        self.message_listeners: Dict[
            re.Pattern, Sequence[MessageFunction]
        ] = defaultdict(list)

    def initialize(self, driver: Driver, settings: Settings = Settings()):
        self.driver = driver
        self.settings = settings

        # Register listeners for any listener functions we might have
        for attribute in dir(self):
            attribute = getattr(self, attribute)
            if isinstance(attribute, MessageFunction):
                # Register this function and any potential siblings
                for function in [attribute] + attribute.siblings:
                    function.plugin = self
                    self.message_listeners[function.matcher].append(function)

        return self

    def on_start(self):
        """Will be called after initialization.

        Can be overridden on the subclass if desired.
        """
        logging.debug(f"Plugin {self.__class__.__name__} started!")
        return self

    def on_stop(self):
        """Will be called when the bot is shut down manually.

        Can be overridden on the subclass if desired.
        """
        logging.debug(f"Plugin {self.__class__.__name__} stopped!")
        return self

    async def call_function(
        self, function: Function, event: EventWrapper, groups: Sequence[str]
    ):
        if function.is_coroutine:
            await function(event, *groups)  # type:ignore
        else:
            # By default, we use the global threadpool of the driver, but we could use
            # a plugin-specific thread or process pool if we wanted.
            self.driver.threadpool.add_task(function, event, *groups)

    def get_help_string(self):
        string = f"Plugin {self.__class__.__name__} has the following functions:\n"
        string += "----\n"
        for functions in self.message_listeners.values():
            for function in functions:
                string += f"- {function.get_help_string()}"
            string += "----\n"

        return string

    @listen_to("^help$", needs_mention=True)
    @listen_to("^!help$")
    async def help(self, message: Message):
        """Prints the list of functions registered on every active plugin."""
        self.driver.reply_to(message, self.get_help_string())
