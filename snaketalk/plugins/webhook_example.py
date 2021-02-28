from snaketalk.driver import Driver
from snaketalk.function import listen_to, listen_webhook
from snaketalk.plugins.base import Plugin
from snaketalk.settings import Settings
from snaketalk.wrappers import ActionEvent, Message


class WebhookExample(Plugin):
    """Webhook plugin with examples of webhook server functionality."""

    def initialize(self, driver: Driver, settings: Settings):
        super().initialize(driver, settings)
        self.webhook_host_url = settings.WEBHOOK_HOST_URL
        self.webhook_host_port = settings.WEBHOOK_HOST_PORT

    @listen_webhook("ping")
    @listen_webhook("pong")
    async def action_listener(self, event: ActionEvent):
        self.driver.respond_to_web(
            event,
            {
                "update": {"message": event.context["text"], "props": {}},
                "ephemeral_text": "You updated the post!",
            },
        )

    @listen_to("!button", direct_only=False)
    async def webhook_button(self, message: Message):
        self.driver.reply_to(
            message,
            "",
            props={
                "attachments": [
                    {
                        "pretext": None,
                        "text": "Take your pick..",
                        "actions": [
                            {
                                "id": "sendPing",
                                "name": "Ping",
                                "integration": {
                                    "url": f"{self.webhook_host_url}:{self.webhook_host_port}/"
                                    "hooks/ping",
                                    "context": {
                                        "text": "The ping webhook works! :tada:",
                                    },
                                },
                            },
                            {
                                "id": "sendPong",
                                "name": "Pong",
                                "integration": {
                                    "url": f"{self.webhook_host_url}:{self.webhook_host_port}/"
                                    "hooks/pong",
                                    "context": {
                                        "text": "The pong webhook works! :tada:",
                                    },
                                },
                            },
                        ],
                    }
                ]
            },
        )
