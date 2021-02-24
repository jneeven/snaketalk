import asyncio
import re
from unittest import mock

import click

from snaketalk import Plugin, listen_to
from snaketalk.driver import Driver

from .message_handler_test import create_message


# Used in the plugin tests below
class FakePlugin(Plugin):
    @listen_to("pattern")
    def my_function(self, message, needs_mention=True):
        """This is the docstring of my_function."""
        pass

    @listen_to("direct_pattern", direct_only=True, allowed_users=["admin"])
    def direct_function(self, message):
        pass

    @listen_to("async_pattern")
    @listen_to("another_async_pattern", direct_only=True)
    async def my_async_function(self, message):
        """Async function docstring."""
        pass

    @listen_to("click_command")
    @click.command(help="Help string for the entire function.")
    @click.option(
        "--option", type=int, default=0, help="Help string for the optional argument."
    )
    def click_commmand(self, message, option):
        """Ignored docstring.

        Just for code readability.
        """
        pass


class TestPlugin:
    def test_initialize(self):
        p = FakePlugin().initialize(Driver())
        # Test whether the function was registered properly
        assert p.listeners[re.compile("pattern")] == [
            FakePlugin.my_function,
        ]

        # This function should be registered twice, once for each listener
        assert len(p.listeners[re.compile("async_pattern")]) == 1
        assert (
            p.listeners[re.compile("async_pattern")][0].function
            == FakePlugin.my_async_function.function
        )

        assert len(p.listeners[re.compile("another_async_pattern")]) == 1
        assert (
            p.listeners[re.compile("another_async_pattern")][0].function
            == FakePlugin.my_async_function.function
        )

    @mock.patch("snaketalk.driver.ThreadPool.add_task")
    def test_call_function(self, add_task):
        p = FakePlugin().initialize(Driver())

        # Since this is not an async function, a task should be added to the threadpool
        message = create_message(text="pattern")
        asyncio.run(
            p.call_function(FakePlugin.my_function, message, groups=["test", "another"])
        )
        add_task.assert_called_once_with(
            FakePlugin.my_function, message, "test", "another"
        )

        # Since this is an async function, it should be called directly through asyncio.
        message = create_message(text="async_pattern")
        with mock.patch.object(p.my_async_function, "function") as mock_function:
            asyncio.run(
                p.call_function(FakePlugin.my_async_function, message, groups=[])
            )
            mock_function.assert_called_once_with(p, message)

    def test_help_string(self, snapshot):
        p = FakePlugin().initialize(Driver())
        # Compare the help string with the snapshotted version.
        snapshot.assert_match(p.get_help_string())
