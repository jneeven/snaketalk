from unittest import mock

import pytest

from snaketalk import Bot


@pytest.fixture(scope="function")
def bot():
    bot = Bot()
    yield bot
    bot.stop()  # if the bot was started, stop it


class TestBot:
    @mock.patch("snaketalk.driver.Driver.login")
    def test_init(self, login):
        bot = Bot()
        login.assert_called_once()

        # TODO: pass a settings object and verify that the driver was initialized
        # with the correct settings.

        # TODO: check that any passed plugins are initialized

    @mock.patch("snaketalk.driver.Driver.init_websocket")
    def test_run(self, init_websocket, bot):
        bot.run()
        init_websocket.assert_called_once()
        bot.stop()
        # assert False
        # TODO: test that on_stop was called for all plugins
