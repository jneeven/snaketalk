import time

import pytest

from snaketalk import Bot, Settings

from .utils import start_bot  # noqa, we only import this so that the bot is started

OFF_TOPIC_ID = "8p516nuo8tfpdnhf56geskp7mc"  # Channel id
TEAM_ID = "5u4q3izes387mq494benjxyzya"
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


# Verifies that the bot is running and listening to this non-targeted message
def test_start(driver):
    post_id = driver.create_post(OFF_TOPIC_ID, "starting integration tests!")["id"]
    time.sleep(RESPONSE_TIMEOUT)
    thread_info = driver.get_thread(post_id)
    reply_id = thread_info["order"][-1]
    if reply_id == post_id:
        raise ValueError("Expected a response, but didn't get any!")

    assert thread_info["posts"][reply_id]["message"] == "Bring it on!"


class TestExamplePlugin:
    def test_info(self, driver):
        post_id = driver.create_post(OFF_TOPIC_ID, "!info")["id"]
        user_info = driver.get_user_info(driver.user_id)
        time.sleep(RESPONSE_TIMEOUT)

        thread_info = driver.get_thread(post_id)
        reply_id = thread_info["order"][-1]
        if reply_id == post_id:
            raise ValueError("Expected a response, but didn't get any!")

        reply = thread_info["posts"][reply_id]["message"]
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
        post_id = driver.create_post(OFF_TOPIC_ID, "@main_bot ping")["id"]
        time.sleep(RESPONSE_TIMEOUT)
        thread_info = driver.get_thread(post_id)
        reply_id = thread_info["order"][-1]
        if reply_id == post_id:
            raise ValueError("Expected a response, but didn't get any!")

        assert thread_info["posts"][reply_id]["message"] == "pong"

    def test_sleep(self, driver):
        post_info = driver.create_post(OFF_TOPIC_ID, "@main_bot sleep 5")
        post_id = post_info["id"]
        time.sleep(max(10, RESPONSE_TIMEOUT))  # wait at least 10 seconds

        thread_info = driver.get_thread(post_id)
        import json

        print(json.dumps(thread_info, indent=4))
        reply_id = thread_info["order"][-1]
        if reply_id == post_id:
            raise ValueError("Expected a response, but didn't get any!")

        assert thread_info["posts"][reply_id]["message"] == "Done!"
        # At least 5 seconds must have passed
        assert (
            thread_info["posts"][reply_id]["create_at"] - post_info["create_at"] >= 5000
        )
