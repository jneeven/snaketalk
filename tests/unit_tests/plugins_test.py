import asyncio
import re
from unittest import mock

from snaketalk import ExamplePlugin, Function, Plugin, listen_to
from snaketalk.driver import Driver

from .message_handler_test import create_message


class TestFunction:
    def test_listen_to(self):
        pattern = "test_regexp"

        def original_function():
            pass

        wrapped_function = listen_to(pattern, re.IGNORECASE)(original_function)

        assert isinstance(wrapped_function, Function)
        # Verify that both the regexp and its flags are correct
        assert wrapped_function.matcher == re.compile(pattern, re.IGNORECASE)
        assert wrapped_function.function == original_function

    def test_is_coroutine(self):
        @listen_to("")
        async def coroutine():
            pass

        assert coroutine.is_coroutine

        @listen_to("")
        def not_a_coroutine():
            pass

        assert not not_a_coroutine.is_coroutine

    def test_wrap_function(self):  # noqa
        def wrapped(instance, message, arg1, arg2):
            return arg1, arg2

        f = Function(wrapped, matcher=re.compile(""))
        # Verify that the arguments are passed and returned correctly
        assert f(create_message(), "yes", "no") == ("yes", "no")

        # Verify that wrapping an already wrapped function also works
        new_f = Function(f, matcher=re.compile("a"))
        assert new_f.function is wrapped
        assert new_f.matcher.pattern == "a"

    @mock.patch("snaketalk.driver.Driver.user_id", "qmw86q7qsjriura9jos75i4why")
    def test_needs_mention(self):  # noqa
        wrapped = mock.MagicMock()
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
        wrapped = mock.MagicMock()
        wrapped.__qualname__ = "wrapped"
        f = listen_to("", direct_only=True)(wrapped)

        # A mention is not a direct message, so shouldn't trigger
        f(create_message(mentions=["qmw86q7qsjriura9jos75i4why"], channel_type="O"))
        wrapped.assert_not_called()

        f(create_message(mentions=[], channel_type="D"))
        wrapped.assert_called_once()

    def test_allowed_users(self):
        wrapped = mock.MagicMock()
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
    def my_function(self, message):
        pass

    @listen_to("async_pattern")
    async def my_async_function(self, message):
        pass


class TestPlugin:
    def test_initialize(self):
        p = FakePlugin().initialize(Driver())
        # Simply test whether the function was registered properly
        assert p.listeners[FakePlugin.my_function.matcher] == [FakePlugin.my_function]

    @mock.patch("snaketalk.driver.ThreadPool.add_task")
    def test_call_function(self, add_task):
        driver = Driver()
        p = FakePlugin().initialize(driver)

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
        p.my_async_function.function = mock.Mock(wraps=p.my_async_function.function)
        asyncio.run(p.call_function(FakePlugin.my_async_function, message, groups=[]))
        p.my_async_function.function.assert_called_once_with(p, message)
