import time
from multiprocessing import Process
from pathlib import Path

import pytest

from snaketalk import Bot, Message, Plugin, Settings, listen_to


class TestPlugin(Plugin):
    @listen_to("^starting integration tests")
    async def reply_start(self, message: Message):
        self.driver.reply_to(message, "Bring it on!")


# At the start of the pytest session, the bot is started
@pytest.fixture(scope="session", autouse=True)
def start_bot(request):
    log_path = Path("./bot.log")
    bot = Bot(
        settings=Settings(
            MATTERMOST_URL="http://127.0.0.1",
            BOT_TOKEN="tdf5ozcwt7yf9kb6xzs748ot1h",
            MATTERMOST_PORT=8065,
            SSL_VERIFY=False,
        ),
        plugins=[TestPlugin()],
    )

    def run_bot():
        log_path.write_text(f"Bot started at {time.time()}")
        bot.run()

    # Start the bot now
    bot_process = Process(target=run_bot)
    bot_process.start()

    def stop_bot():
        time.sleep(5)
        log_path.write_text(f"Bot stopped at {time.time()}")
        bot_process.terminate()

    # Once all tests are finished, stop the bot
    request.addfinalizer(stop_bot)
