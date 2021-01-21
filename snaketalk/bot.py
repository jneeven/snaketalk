import logging
import sys

from snaketalk.driver import Driver
from snaketalk.message_handler import MessageHandler
from snaketalk.settings import Settings


class Bot:
    instance = None

    def __init__(self, settings=Settings()):
        logging.basicConfig(
            **{
                "format": "[%(asctime)s] %(message)s",
                "datefmt": "%m/%d/%Y %H:%M:%S",
                "level": logging.DEBUG if settings.DEBUG else logging.INFO,
                "stream": sys.stdout,
            }
        )
        self.settings = settings
        self.api = Driver(
            {
                "url": settings.BOT_URL,
                "port": 443,
                "token": settings.BOT_TOKEN,
                "verify": settings.SSL_VERIFY,
                "timeout": 0.5,
            }
        )
        self.api.login()
        self.message_handler = MessageHandler(self.api, settings=self.settings)

    def run(self):
        self.message_handler.start()
