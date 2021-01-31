import pytest

from snaketalk.message import Message


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
                    "message": "hello",
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
    def test_init(self):
        # TODO: test the name matcher regexp
        # TODO: test that the registered listeners correspond to those registered on
        # the (multiple) chosen plugins
        pass

    def test_should_ignore(self):
        # TODO: test whether people from the Settings.IGNORE_USERS are ignored correctly
        # TODO: test whether ignore_own_messages is used correctly
        # Both can use the test message defined above, with some manual modifications
        pass

    def test_handle_event(self):
        # TODO: test that _handle_post is called on `posted` event, and nothing happens
        # otherwise. Should mock _handle_post.
        pass

    def test_handle_post(self):
        # TODO: test that any registered listeners are called with the appropriate
        # arguments, and any bot mentions at the start of the message are stripped off.
        # Will probably need to mock some driver / plugin functions to prevent making
        # API calls.
        pass
