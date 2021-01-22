import asyncio
import re
from abc import ABC
from collections import defaultdict
from typing import Callable, Dict, Optional, Sequence

from snaketalk.driver import Driver
from snaketalk.message import Message


def listen_to(
    regexp: str,
    regexp_flag: int = 0,
    *,
    direct_only=False,
    needs_mention=False,
    allowed_users=None,
):
    """Wrap the given function in a Function class so we can register some
    properties."""

    def wrapped_func(func):
        pattern = re.compile(regexp, regexp_flag)
        return Function(
            func,
            matcher=pattern,
            direct_only=direct_only,
            needs_mention=needs_mention,
            allowed_users=allowed_users,
        )

    return wrapped_func


def _completed_future():
    # Utility function to create a stub Future object that asyncio can wait for.
    future = asyncio.Future()
    future.set_result(True)
    return future


class Function:
    """Wrapper around a Plugin class method that should respond to certain Mattermost
    events."""

    def __init__(
        self,
        function: Callable,
        matcher: re.Pattern,
        direct_only: bool,
        needs_mention: bool,
        allowed_users: Optional[Sequence] = None,
    ):
        self.function = function
        self.is_coroutine = asyncio.iscoroutinefunction(function)
        self.name = function.__qualname__

        self.matcher = matcher
        self.direct_only = direct_only
        self.needs_mention = needs_mention
        self.allowed_users = allowed_users

        self.plugin = None

    def __call__(self, message: Message, *args):
        # We need to return this so that if this Function was called with `await`,
        # asyncio doesn't crash.
        return_value = None if not self.is_coroutine else _completed_future()

        # Check if this message meets our requirements
        if self.direct_only and not message.is_direct_message:
            return return_value

        if self.needs_mention and not (
            message.is_direct_message or self.plugin.driver.user_id in message.mentions
        ):
            return return_value

        if self.allowed_users and message.sender_name not in self.allowed_users:
            self.plugin.driver.reply_to(
                message, "You do not have permission to perform this action!"
            )
            return return_value

        return self.function(self.plugin, message, *args)


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

    async def call_function(
        self, function: Function, message: Message, groups: Sequence[str]
    ):
        if function.is_coroutine:
            await function(message, *groups)
        else:
            # By default, we use the global threadpool of the driver, but we could use
            # a plugin-specific thread or process pool if we wanted.
            self.driver.threadpool.add_task(function, (message, *groups))

    def get_help_string(self):
        # TODO: implement help string
        return ""

    @listen_to("^!help$")
    async def help_request(self, message: Message):
        self.driver.reply_to(message, self.get_help_string())
