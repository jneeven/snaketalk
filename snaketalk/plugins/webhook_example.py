
from snaketalk.message import Message
from snaketalk.plugins.base import Plugin, listen_to
from snaketalk.settings import Settings


class WebhookExample(Plugin):
    """ Webhook plugin with examples of webhook server functionality """

    def __init__(self):
        super().__init__()
        self.webhook_host_url = Settings().WEBHOOK_HOST_URL
        self.webhook_host_port = Settings().WEBHOOK_HOST_PORT
        self.webhook_id = Settings().WEBHOOK_ID
        self.webhook_url = self._make_webhook_url()

    def _make_webhook_url(self):
        mattermost_url = Settings().MATTERMOST_URL
        mattermost_port = Settings().MATTERMOST_PORT
        webhook_url = f"http://{mattermost_url}:{mattermost_port}/hooks/{self.webhook_id}"

        return webhook_url

    @listen_to("!button", direct_only=False)
    async def webhook_button(self, message: Message):
        self.driver.reply_to(message, "", props={
                                 "attachments": [
                                     {
                                         "pretext": None,
                                         "text": "Take your pick..",
                                         "actions": [
                                             {
                                                 "id": "Ping",
                                                 "name": "Ping",
                                                 "integration": {
                                                     "url": f"{self.webhook_host_url}:{self.webhook_host_port}/"
                                                            "actions/ping",
                                                     "context": {
                                                         "data": "ping"
                                                     }
                                                 }
                                                 }, {
                                                 "id": "sendWebhook",
                                                 "name": "Send a webhook",
                                                 "integration": {
                                                     "url": f"{self.webhook_host_url}:{self.webhook_host_port}/"
                                                            f"hooks/{self.webhook_id}",
                                                     "context": {
                                                         "text": "The webhook works! :tada:",
                                                         "webhook_url": self.webhook_url
                                                     }
                                                 }
                                             }
                                         ]
                                     }
                                 ]
                             }
                             )
