import logging
import sys
from typing import Sequence

from snaketalk.driver import Driver
from snaketalk.message_handler import MessageHandler
from snaketalk.plugins import DefaultPlugin, Plugin
from snaketalk.settings import Settings


class Bot:
    instance = None

    def __init__(self, settings=Settings(), plugins=[DefaultPlugin()]):
        logging.basicConfig(
            **{
                "format": "[%(asctime)s] %(message)s",
                "datefmt": "%m/%d/%Y %H:%M:%S",
                "level": logging.DEBUG if settings.DEBUG else logging.INFO,
                "stream": sys.stdout,
            }
        )
        self.settings = settings
        self.driver = Driver(
            {
                "url": settings.BOT_URL,
                "port": 443,
                "token": settings.BOT_TOKEN,
                "verify": settings.SSL_VERIFY,
                "timeout": 0.5,
            }
        )
        self.driver.login()
        self.plugins = self._initialize_plugins(plugins)
        self.message_handler = MessageHandler(
            self.driver, settings=self.settings, plugins=self.plugins
        )

    def _initialize_plugins(self, plugins: Sequence[Plugin]):
        for plugin in plugins:
            plugin.initialize(self.driver)
        return plugins

    def run(self):
        try:
            self.message_handler.start()
        except KeyboardInterrupt as e:
            self.driver.threadpool.stop()
            raise e
