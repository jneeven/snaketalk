import asyncio
import re
from abc import ABC
from collections import defaultdict
from typing import Callable, Dict, Sequence

from snaketalk.driver import Driver
from snaketalk.message import Message


def listen_to(regexp: str, direct_only=False, needs_mention=False):
    """Wrap the given function in a Function class so we can register some
    properties."""

    def wrapped_func(func):
        return Function(
            func, regexp=regexp, direct_only=direct_only, needs_mention=needs_mention
        )

    return wrapped_func


def _completed_future():
    future = asyncio.Future()
    future.set_result(True)
    return future


class Function:
    """Wrapper around a Plugin class method that should respond to certain Mattermost
    events."""

    def __init__(
        self, function: Callable, regexp: str, direct_only: bool, needs_mention: bool
    ):
        self.function = function
        self.is_coroutine = asyncio.iscoroutinefunction(function)
        self.name = function.__qualname__

        self.matcher = re.compile(regexp)
        self.direct_only = direct_only
        self.needs_mention = needs_mention

        self.plugin = None

    def __call__(self, message: Message):
        # Check if this message meets our requirements
        if self.direct_only and not message.is_direct_message:
            # We need to return this so that if this Function was called with `await`,
            # asyncio doesn't crash.
            return _completed_future()

        if self.needs_mention and not (
            message.is_direct_message or self.plugin.driver.user_id in message.mentions
        ):
            return _completed_future()

        return self.function(self.plugin, message)


class Plugin(ABC):
    """A Plugin is a self-contained class that defines what functions should be executed
    given different inputs.

    It will be called by the MessageHandler whenever one of its listeners is triggered,
    but execution of the corresponding function is handled by the plugin itself. This
    way, you can implement multithreading or multiprocessing as desired.
    """

    listeners: Dict[re.Pattern, Sequence[Function]] = defaultdict(list)

    def __init__(self):
        self.driver = None

    def initialize(self, driver: Driver):
        self.driver = driver

        # Register listeners for any listener functions we might have
        for attribute in dir(self):
            attribute = getattr(self, attribute)
            if isinstance(attribute, Function):
                attribute.plugin = self
                self.listeners[attribute.matcher].append(attribute)

        self.on_start()

    def on_start(self):
        """Will be called after initialization.

        Can be overridden on the subclass if desired.
        """
        # TODO: make this a debug log
        print(f"{self.__class__.__name__}.on_start() called!")

    def on_stop(self):
        """Will be called when the bot is shut down manually.

        Can be overridden on the subclass if desired.
        """
        return

    async def call_function(self, function: Function, message: Message):
        if function.is_coroutine:
            await function(message)
        else:
            # By default, we use the global threadpool of the driver, but we could use
            # a plugin-specific thread or process pool if we wanted.
            self.driver.threadpool.add_task(function, (message,))
