import asyncio
import json
from unittest import mock

import pytest

from snaketalk import Message, Settings
from snaketalk.driver import Driver
from snaketalk.message_handler import MessageHandler
from snaketalk.plugins.default import ExamplePlugin


@pytest.fixture(scope="function")
def message():
    return Message(
        {
            "event": "posted",
            "data": {
                "channel_display_name": "Off-Topic",
                "channel_name": "off-topic",
                "channel_type": "O",
                "mentions": ["qmw86q7qsjriura9jos75i4why"],
                "post": {
                    "id": "wqpuawcw3iym3pq63s5xi1776r",
                    "create_at": 1533085458236,
                    "update_at": 1533085458236,
                    "edit_at": 0,
                    "delete_at": 0,
                    "is_pinned": "False",
                    "user_id": "131gkd5thbdxiq141b3514bgjh",
                    "channel_id": "4fgt3n51f7ftpff91gk1iy1zow",
                    "root_id": "",
                    "parent_id": "",
                    "original_id": "",
                    "message": "my_username sleep 5",
                    "type": "",
                    "props": {},
                    "hashtags": "",
                    "pending_post_id": "",
                },
                "sender_name": "betty",
                "team_id": "au64gza3iint3r31e7ewbrrasw",
            },
            "broadcast": {
                "omit_users": "None",
                "user_id": "",
                "channel_id": "4fgt3n51f7ftpff91gk1iy1zow",
                "team_id": "",
            },
            "seq": 29,
        }
    )


class TestMessageHandler:
    @mock.patch("snaketalk.driver.Driver.username", new="my_username")
    def test_init(self):
        handler = MessageHandler(Driver(), Settings(), plugins=[ExamplePlugin()])
        # Test the name matcher regexp
        assert handler._name_matcher.match("@my_username are you there?")
        assert not handler._name_matcher.match("@other_username are you there?")

        # Test that all listeners from the individual plugins are now registered on
        # the handler
        for plugin in handler.plugins:
            for pattern, listener in plugin.listeners.items():
                assert listener in handler.listeners[pattern]

        # And vice versa, check that any listeners on the handler come from the
        # registered plugins
        for pattern, listeners in handler.listeners.items():
            for listener in listeners:
                assert any(
                    [
                        pattern in plugin.listeners
                        and listener in plugin.listeners[pattern]
                        for plugin in handler.plugins
                    ]
                )

    @mock.patch("snaketalk.driver.Driver.username", new="my_username")
    def test_should_ignore(self, message):
        handler = MessageHandler(
            Driver(), Settings(IGNORE_USERS=["ignore_me"]), plugins=[]
        )
        # We shouldn't ignore a message from betty, since she is not listed
        assert not handler._should_ignore(message)

        message = Message(message.body)
        message.body["data"]["sender_name"] = "ignore_me"
        assert handler._should_ignore(message)

        # We ignore our own messages by default
        message = Message(message.body)
        message.body["data"]["sender_name"] = "my_username"
        assert handler._should_ignore(message)

        # But shouldn't do so if this is explicitly requested
        handler = MessageHandler(
            Driver(),
            Settings(IGNORE_USERS=["ignore_me"]),
            plugins=[],
            ignore_own_messages=False,
        )
        assert not handler._should_ignore(message)

    @mock.patch("snaketalk.message_handler.MessageHandler._handle_post")
    def test_handle_event(self, handle_post, message):
        handler = MessageHandler(Driver(), Settings(), plugins=[])
        # This event should trigger _handle_post
        asyncio.run(handler.handle_event(json.dumps(message.body)))
        # This event should not
        asyncio.run(handler.handle_event(json.dumps({"event": "some_other_event"})))

        handle_post.assert_called_once_with(message.body)

    @mock.patch("snaketalk.driver.Driver.username", new="my_username")
    def test_handle_post(self, message):
        # Create an initialized plugin so its listeners are registered
        plugin = ExamplePlugin()
        driver = Driver()
        plugin.initialize(driver)
        # Construct a handler with it
        handler = MessageHandler(driver, Settings(), plugins=[plugin])

        # Mock the call_function of the plugin so we can make some asserts
        async def mock_call_function(function, message, groups):
            # This is the regexp that we're trying to trigger
            assert function.matcher.pattern == "sleep ([0-9]+)"
            assert message.text == "sleep 5"  # username should be stripped off
            assert groups == ["5"]  # arguments should be matched and passed explicitly

        plugin.call_function = mock.Mock(wraps=mock_call_function)

        # Transform the default message into a raw post event so we can pass it
        new_body = message.body.copy()
        new_body["data"]["post"] = json.dumps(new_body["data"]["post"])
        new_body["data"]["mentions"] = json.dumps(new_body["data"]["mentions"])
        asyncio.run(handler._handle_post(new_body))

        # Assert the function was called, so we know the asserts succeeded.
        plugin.call_function.assert_called_once()
