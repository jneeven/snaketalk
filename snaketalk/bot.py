import logging
import sys
from typing import Sequence

from snaketalk.driver import Driver
from snaketalk.message_handler import MessageHandler
from snaketalk.plugins import ExamplePlugin, Plugin, WebhookExample
from snaketalk.settings import Settings
from snaketalk.webhook_server import WebhookServer


class Bot:
    """Base chatbot class.

    Can be either subclassed for custom functionality, or used as-is with custom plugins
    and settings. To start the bot, simply call bot.run().
    """

    def __init__(
        self, settings=Settings(), plugins=[ExamplePlugin(), WebhookExample()]
    ):
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
                "url": settings.MATTERMOST_URL,
                "port": settings.MATTERMOST_PORT,
                "token": settings.BOT_TOKEN,
                "scheme": settings.SCHEME,
                "verify": settings.SSL_VERIFY,
            }
        )
        self.driver.login()
        self.plugins = self._initialize_plugins(plugins)
        self.message_handler = MessageHandler(
            self.driver, settings=self.settings, plugins=self.plugins
        )
        self.webhook_server = WebhookServer()

    def _initialize_plugins(self, plugins: Sequence[Plugin]):
        for plugin in plugins:
            plugin.initialize(self.driver)
        return plugins

    def run(self):
        logging.info(f"Starting bot {self.__class__.__name__}.")
        try:
            self.driver.threadpool.start()
            # Start a thread to run potential scheduled jobs
            self.driver.threadpool.start_scheduler_thread(
                self.settings.SCHEDULER_PERIOD
            )
            for plugin in self.plugins:
                plugin.on_start()
            if self.settings.WEBHOOK_HOST_ENABLED:
                webhook_host_ip = self.settings.WEBHOOK_HOST_URL
                webhook_host_port = self.settings.WEBHOOK_HOST_PORT
                logging.info(
                    "Starting webhook server on "
                    f"{webhook_host_ip}:{webhook_host_port}"
                )
                self.webhook_server.start()
            self.message_handler.start()

        except KeyboardInterrupt as e:
            self.stop()
            raise e

    def stop(self):
        logging.info("Stopping bot.")
        # Shutdown the running plugins
        for plugin in self.plugins:
            plugin.on_stop()
        # Stop the threadpool
        self.driver.threadpool.stop()
