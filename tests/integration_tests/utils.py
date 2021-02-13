import time
from multiprocessing import Process

import pytest
from filelock import FileLock

from snaketalk import Bot, ExamplePlugin, Message, Plugin, Settings, listen_to


class TestPlugin(Plugin):
    @listen_to("^starting integration tests")
    async def reply_start(self, message: Message):
        self.driver.reply_to(message, "Bring it on!")


# At the start of the pytest session, the bot is started
@pytest.fixture(scope="session", autouse=True)
def start_bot(request):
    lock = FileLock("./bot.lock")

    try:
        # We want to run the tests in multiple parallel processes, but launch at most
        # a single bot.
        lock.acquire(timeout=0.01)
        bot = Bot(
            settings=Settings(
                MATTERMOST_URL="http://127.0.0.1",
                BOT_TOKEN="tdf5ozcwt7yf9kb6xzs748ot1h",
                MATTERMOST_PORT=8065,
                SSL_VERIFY=False,
            ),
            plugins=[TestPlugin(), ExamplePlugin()],
        )

        def run_bot():
            bot.run()

        # Start the bot now
        bot_process = Process(target=run_bot)
        bot_process.start()

        def stop_bot():
            time.sleep(5)
            bot_process.terminate()
            lock.release()

        # Once all tests are finished, stop the bot
        request.addfinalizer(stop_bot)

    except TimeoutError:
        # If the lock times out, it means a bot is already running and we don't need
        # to do anything here.
        pass
