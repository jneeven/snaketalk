import pytest

from snaketalk import Bot, Settings

from .utils import start_bot  # noqa, we only import this so that the bot is started

OFF_TOPIC_ID = "8p516nuo8tfpdnhf56geskp7mc"  # Channel id


@pytest.fixture(scope="session")
def tester():
    return Bot(
        settings=Settings(
            MATTERMOST_URL="http://127.0.0.1",
            BOT_TOKEN="usi1ir74x3yq7qodtzzpc6kudw",
            MATTERMOST_PORT=8065,
            SSL_VERIFY=False,
        ),
        plugins=[],  # We only use this to send messages, not to reply to anything.
    )


"""TODO: Should create a bunch of pytest functions that send a single message and check
whether the responses are as intended (e.g. was an emoji added, did the other bot
respond with an ephemeral message, etc.)."""


def test_start(tester):
    post_id = tester.driver.create_post(OFF_TOPIC_ID, "starting integration tests!")[
        "id"
    ]
    # TODO: check if we got a response (we should, see utils.py)
