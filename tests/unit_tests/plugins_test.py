import asyncio
import re
from unittest import mock

import click
import pytest

from snaketalk import ExamplePlugin, Function, Plugin, listen_to
from snaketalk.driver import Driver

from .message_handler_test import create_message


def example_listener(self, message):
    # Used to copy the arg specs to mock.Mock functions.
    pass


class TestFunction:
    def test_listen_to(self):
        pattern = "test_regexp"

        def original_function(self, message):
            pass

        wrapped_function = listen_to(pattern, re.IGNORECASE)(original_function)

        assert isinstance(wrapped_function, Function)
        # Verify that both the regexp and its flags are correct
        assert wrapped_function.matcher == re.compile(pattern, re.IGNORECASE)
        assert wrapped_function.function == original_function

    def test_arguments(self):
        # This function misses the `message` argument
        def function1(self, arg):
            pass

        with pytest.raises(TypeError):
            Function(function1, matcher=re.compile(""))

        # This function has the correct arguments, but not in the correct order
        def function2(self, arg, message):
            pass

        with pytest.raises(TypeError):
            Function(function2, matcher=re.compile(""))

        # This function should work just fine
        def function3(self, message):
            pass

        Function(function3, matcher=re.compile(""))

    def test_is_coroutine(self):
        @listen_to("")
        async def coroutine(self, message):
            pass

        assert coroutine.is_coroutine

        @listen_to("")
        def not_a_coroutine(self, message):
            pass

        assert not not_a_coroutine.is_coroutine

    def test_click_coroutine(self):
        with pytest.raises(
            ValueError,
            match="Combining click functions and coroutines is currently not supported",
        ):

            @listen_to("")
            @click.command()
            async def coroutine(self, message):
                pass

    def test_wrap_function(self):  # noqa
        def wrapped(self, message, arg1, arg2):
            return arg1, arg2

        f = Function(wrapped, matcher=re.compile(""))
        # Verify that the arguments are passed and returned correctly
        assert f(create_message(), "yes", "no") == ("yes", "no")

        # Verify that wrapping an already wrapped function also works
        new_f = Function(f, matcher=re.compile("a"))
        assert new_f.function is wrapped
        assert new_f.matcher.pattern == "a"
        assert f in new_f.siblings

    def test_click_function(self):
        @click.command()
        @click.option("--arg1", type=str, default="nothing")
        @click.option("--arg2", type=str, default="nothing either")
        @click.option("-f", "--flag", is_flag=True)
        def wrapped(self, message, arg1, arg2, flag):
            return arg1, arg2, flag

        f = Function(wrapped, matcher=re.compile(""))
        # Verify that the arguments are passed and returned correctly
        assert f(create_message(), "--arg1=yes --arg2=no") == ("yes", "no", False)
        assert f(create_message(), "-f --arg2=no") == ("nothing", "no", True)

        # If an incorrect argument is passed, the error and help string should be returned.
        def mocked_reply(message, response):
            assert "no such option: --nonexistent-arg" in response
            assert f.docstring in response

        f.plugin = ExamplePlugin().initialize(Driver())
        with mock.patch.object(
            f.plugin.driver, "reply_to", wraps=mocked_reply
        ) as mock_function:
            f(create_message(), "-f --arg2=no --nonexistent-arg")
            mock_function.assert_called_once()

    @mock.patch("snaketalk.driver.Driver.user_id", "qmw86q7qsjriura9jos75i4why")
    def test_needs_mention(self):  # noqa
        wrapped = mock.create_autospec(example_listener)
        wrapped.__qualname__ = "wrapped"
        f = listen_to("", needs_mention=True)(wrapped)
        f.plugin = ExamplePlugin().initialize(Driver())

        # The default message mentions the specified user ID, so should be called
        f(create_message(mentions=["qmw86q7qsjriura9jos75i4why"]))
        wrapped.assert_called_once()
        wrapped.reset_mock()

        # No mention, so the function should still only have been called once in total
        f(create_message(mentions=[]))
        wrapped.assert_not_called()

        # But if this is a direct message, we do want to trigger
        f(create_message(mentions=[], channel_type="D"))
        wrapped.assert_called_once()

    @mock.patch("snaketalk.driver.Driver.user_id", "qmw86q7qsjriura9jos75i4why")
    def test_direct_only(self):
        wrapped = mock.create_autospec(example_listener)
        wrapped.__qualname__ = "wrapped"
        f = listen_to("", direct_only=True)(wrapped)

        # A mention is not a direct message, so shouldn't trigger
        f(create_message(mentions=["qmw86q7qsjriura9jos75i4why"], channel_type="O"))
        wrapped.assert_not_called()

        f(create_message(mentions=[], channel_type="D"))
        wrapped.assert_called_once()

    def test_allowed_users(self):
        wrapped = mock.create_autospec(example_listener)
        wrapped.__qualname__ = "wrapped"
        # Create a driver with a mocked reply function
        driver = Driver()

        def fake_reply(message, text):
            assert "you do not have permission" in text.lower()

        driver.reply_to = mock.Mock(wraps=fake_reply)

        f = listen_to("", allowed_users=["Betty"])(wrapped)
        f.plugin = ExamplePlugin().initialize(driver)

        # This is fine, the names are not caps sensitive
        f(create_message(sender_name="betty"))
        wrapped.assert_called_once()
        wrapped.reset_mock()

        # This is not fine, and we expect the fake reply to be called.
        f(create_message(sender_name="not_betty"))
        wrapped.assert_not_called()
        driver.reply_to.assert_called_once()


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
