import asyncio
import inspect
import logging
import re
from abc import ABC
from collections import defaultdict
from typing import Callable, Dict, Sequence

import click

from snaketalk.driver import Driver
from snaketalk.message import Message


def listen_to(
    regexp: str,
    regexp_flag: int = 0,
    *,
    direct_only=False,
    needs_mention=False,
    allowed_users=[],
):
    """Wrap the given function in a Function class so we can register some
    properties."""

    def wrapped_func(func):
        reg = regexp
        if isinstance(func, click.Command):
            if "$" in regexp:
                raise ValueError(
                    f"Regexp of function {func.callback} contains a $, which is not"
                    " supported! The regexp should simply reflect the argument name, and"
                    " click will take care of the rest."
                )

            # Modify the regexp so that it won't try to match the individual arguments.
            # Click will take care of those. We also manually add the ^ if necessary,
            # so that the commands can't be inserted in the middle of a sentence.
            reg = f"^{reg.strip('^')} (.*)?"  # noqa

        pattern = re.compile(reg, regexp_flag)
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


def spaces(num: int):
    """Utility function to easily indent strings."""
    return " " * num


class Function:
    """Wrapper around a Plugin class method that should respond to certain Mattermost
    events."""

    def __init__(
        self,
        function: Callable,
        matcher: re.Pattern,
        direct_only: bool = False,
        needs_mention: bool = False,
        allowed_users: Sequence[str] = [],
    ):
        # If another Function was passed, keep track of all these siblings.
        # We later use them to register not only the outermost Function, but also any
        # stacked ones.
        self.siblings = []
        while isinstance(function, Function):
            self.siblings.append(function)
            function = function.function

        self.function = function
        self.is_click_function = isinstance(self.function, click.Command)
        self.is_coroutine = asyncio.iscoroutinefunction(function)
        self.matcher = matcher
        self.direct_only = direct_only
        self.needs_mention = needs_mention
        self.allowed_users = [user.lower() for user in allowed_users]

        if self.is_click_function and self.is_coroutine:
            raise ValueError(
                "Combining click functions and coroutines is currently not supported!"
                " Consider using a regular function, which will be threaded by default."
            )

        if self.is_click_function:
            with click.Context(
                function, info_name=self.matcher.pattern.strip("^").split(" (.*)?")[0]
            ) as ctx:
                # Get click help string and do some extra formatting
                self.docstring = function.get_help(ctx).replace("\n", f"\n{spaces(8)}")
            _function = function.callback
        else:
            self.docstring = function.__doc__
            _function = function

        self.name = _function.__qualname__

        argspec = list(inspect.signature(_function).parameters.keys())
        print(self.name, argspec)
        if not argspec[:2] == ["self", "message"]:
            raise TypeError(
                "Any listener function should at least have the positional arguments"
                f" `self` and `message`, but function {self.name} has arguments {argspec}."
            )

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

        if self.is_click_function:
            assert len(args) <= 1  # There is only one group, (.*)?
            if len(args) == 1:
                # Turn space-separated string into list
                args = args[0].strip(" ").split(" ")
            try:
                ctx = self.function.make_context(
                    info_name=self.plugin.__class__.__name__, args=list(args)
                )
                ctx.params.update({"self": self.plugin, "message": message})
                return self.function.invoke(ctx)
            # If there are any missing arguments or the function is otherwise called
            # incorrectly, send the click message back to the user and print help string.
            except click.exceptions.ClickException as e:
                return self.plugin.driver.reply_to(message, f"{e}\n{self.docstring}")

        return self.function(self.plugin, message, *args)

    def get_help_string(self):
        string = f"`{self.matcher.pattern}`:\n"
        # Add a docstring
        doc = self.docstring or "No description provided."
        string += f"{spaces(8)}{doc}\n"

        if any(
            [
                self.needs_mention,
                self.direct_only,
                self.allowed_users,
            ]
        ):
            # Print some information describing the usage settings.
            string += f"{spaces(4)}Additional information:\n"
            if self.needs_mention:
                string += (
                    f"{spaces(4)}- Needs to either mention @{self.plugin.driver.username}"
                    " or be a direct message.\n"
                )
            if self.direct_only:
                string += f"{spaces(4)}- Needs to be a direct message.\n"

            if self.allowed_users:
                string += f"{spaces(4)}- Restricted to certain users.\n"

        return string


class Plugin(ABC):
    """A Plugin is a self-contained class that defines what functions should be executed
    given different inputs.

    It will be called by the MessageHandler whenever one of its listeners is triggered,
    but execution of the corresponding function is handled by the plugin itself. This
    way, you can implement multithreading or multiprocessing as desired.
    """

    def __init__(self):
        self.driver = None
        self.listeners: Dict[re.Pattern, Sequence[Function]] = defaultdict(list)

    def initialize(self, driver: Driver):
        self.driver = driver

        # Register listeners for any listener functions we might have
        for attribute in dir(self):
            attribute = getattr(self, attribute)
            if isinstance(attribute, Function):
                # Register this function and any potential siblings
                for function in [attribute] + attribute.siblings:
                    function.plugin = self
                    self.listeners[function.matcher].append(function)

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
        self, function: Function, message: Message, groups: Sequence[str]
    ):
        if function.is_coroutine:
            await function(message, *groups)  # type:ignore
        else:
            # By default, we use the global threadpool of the driver, but we could use
            # a plugin-specific thread or process pool if we wanted.
            self.driver.threadpool.add_task(function, message, *groups)

    def get_help_string(self):
        string = f"Plugin {self.__class__.__name__} has the following functions:\n"
        string += "----\n"
        for functions in self.listeners.values():
            for function in functions:
                string += f"- {function.get_help_string()}"
            string += "----\n"

        return string

    @listen_to("^help$", needs_mention=True)
    @listen_to("^!help$")
    async def help(self, message: Message):
        """Prints the list of functions registered on every active plugin."""
        self.driver.reply_to(message, self.get_help_string())
