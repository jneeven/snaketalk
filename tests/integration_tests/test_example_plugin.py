import time
from typing import Dict

import pytest

from snaketalk import Bot, Settings
from snaketalk.driver import Driver

from .utils import start_bot  # noqa, we only import this so that the bot is started

OFF_TOPIC_ID = "8p516nuo8tfpdnhf56geskp7mc"  # Channel id
TEAM_ID = "5u4q3izes387mq494benjxyzya"
MAIN_BOT_ID = "7rfim79wnignxjqxzbd6fb9ofr"
RESPONSE_TIMEOUT = 5


@pytest.fixture(scope="session")
def driver():
    return Bot(
        settings=Settings(
            MATTERMOST_URL="http://127.0.0.1",
            BOT_TOKEN="usi1ir74x3yq7qodtzzpc6kudw",
            MATTERMOST_PORT=8065,
            SSL_VERIFY=False,
        ),
        plugins=[],  # We only use this to send messages, not to reply to anything.
    ).driver


def expect_reply(driver: Driver, post: Dict, wait=RESPONSE_TIMEOUT, retries=1):
    """Utility function to specify we expect some kind of reply after `wait` seconds."""
    reply = None
    for _ in range(retries + 1):
        time.sleep(wait)
        thread_info = driver.get_thread(post["id"])
        reply_id = thread_info["order"][-1]
        if reply_id != post["id"]:
            reply = thread_info["posts"][reply_id]
            break

    if not reply:
        raise ValueError("Expected a response, but didn't get any!")

    return reply


# Verifies that the bot is running and listening to this non-targeted message
def test_start(driver):
    post = driver.create_post(OFF_TOPIC_ID, "starting integration tests!")
    assert expect_reply(driver, post)["message"] == "Bring it on!"


class TestExamplePlugin:
    def test_admin(self, driver):
        # Since this is not a direct message, we expect no reply at all
        post_id = driver.create_post(OFF_TOPIC_ID, "@main_bot admin")["id"]
        time.sleep(RESPONSE_TIMEOUT)
        thread_info = driver.get_thread(post_id)
        assert len(thread_info["order"]) == 1

        # For the direct message, we expect to have insufficient permissions, since
        # our name isn't admin
        private_channel = driver.channels.create_direct_message_channel(
            [driver.user_id, MAIN_BOT_ID]
        )["id"]
        post = driver.create_post(private_channel, "admin")
        reply = expect_reply(driver, post)
        assert reply["message"] == "You do not have permission to perform this action!"

    def test_hello_channel(self, driver):
        original_post = driver.create_post(OFF_TOPIC_ID, "@main_bot hello_channel")
        time.sleep(RESPONSE_TIMEOUT)

        as_expected = False
        for id, post in driver.posts.get_posts_for_channel(OFF_TOPIC_ID)[
            "posts"
        ].items():
            if (
                post["message"] == "hello channel!"
                and post["create_at"] > original_post["create_at"]
            ):
                as_expected = True
                break
        if not as_expected:
            raise ValueError(
                "Expected bot to reply 'hello channel!', but found no such message!"
            )

    def test_hello_ephemeral(self, driver):
        """Unfortunately ephemeral posts do not show up through the thread API, so we
        cannot check if an ephemeral reply was sent successfully.

        We can only check whether the right response is sent in case the bot doesn't
        have permission to send ephemeral posts.
        """
        post = driver.create_post(OFF_TOPIC_ID, "@main_bot hello_ephemeral")
        reply = expect_reply(driver, post)
        assert reply["message"] == "I do not have permission to create ephemeral posts!"

    def test_react(self, driver):
        post_id = driver.create_post(OFF_TOPIC_ID, "@main_bot hello_react")["id"]
        time.sleep(RESPONSE_TIMEOUT)
        reactions = driver.reactions.get_reactions_of_post(post_id)
        assert len(reactions) == 1
        assert reactions[0]["emoji_name"] == "+1"

    def test_file(self, driver):
        post = driver.create_post(OFF_TOPIC_ID, "@main_bot hello_file")
        reply = expect_reply(driver, post)
        assert len(reply["metadata"]["files"]) == 1
        file = reply["metadata"]["files"][0]
        assert file["name"] == "hello.txt"
        file = driver.files.get_file(file["id"])
        assert file.content.decode("utf-8") == "Hello from this file!"

    def test_info(self, driver):
        post = driver.create_post(OFF_TOPIC_ID, "!info")
        user_info = driver.get_user_info(driver.user_id)

        reply = expect_reply(driver, post)["message"]
        reply = {
            line.split(": ")[0].lower(): line.split(": ")[1]
            for line in reply.split("\n")
        }
        assert reply["team-id"] == TEAM_ID
        assert reply["username"] == driver.username
        assert reply["email"] == user_info["email"]
        assert reply["user-id"] == driver.user_id
        assert reply["is-direct"] == "False"
        assert reply["mentions"] == "[]"
        assert reply["message"] == "!info"

    def test_ping(self, driver):
        post = driver.create_post(OFF_TOPIC_ID, "@main_bot ping")
        assert expect_reply(driver, post)["message"] == "pong"

    def test_sleep(self, driver):
        post = driver.create_post(OFF_TOPIC_ID, "@main_bot sleep 5")
        # wait at least 15 seconds
        reply = expect_reply(driver, post, wait=max(15, RESPONSE_TIMEOUT))
        assert reply["message"] == "Done!"
        # At least 5 seconds must have passed between our message and the response
        assert reply["create_at"] - post["create_at"] >= 5000
