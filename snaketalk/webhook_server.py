import asyncio
from queue import Queue
from typing import Optional

from aiohttp import web

from snaketalk.settings import Settings
from snaketalk.wrappers import ActionEvent, WebHookEvent


def handle_json_error(func):
    async def handler(instance, request: web.Request):
        try:
            return await func(instance, request)
        except asyncio.CancelledError:
            raise
        except Exception as e:
            return web.json_response({"status": "failed", "reason": str(e)}, status=400)

    return handler


class WebHookServer:
    """A small server that listens to incoming webhooks and forwards them to the bot
    EventHandler in the main thread/process."""

    def __init__(
        self,
        event_queue: Optional[Queue] = None,
        response_queue: Optional[Queue] = None,
    ):
        self.app = web.Application()
        self.app_runner = web.AppRunner(self.app)
        self.settings = Settings()

        # Create queues if necessary.
        self.event_queue = event_queue or Queue()
        self.response_queue = response_queue or Queue()

        # Register /hooks endpoint
        self.app.add_routes([web.post("/hooks/{webhook_id}", self.process_webhook)])

    async def start(self):
        webhook_host_ip = self.settings.WEBHOOK_HOST_URL.replace("http://", "")
        await self.app_runner.setup()
        site = web.TCPSite(
            self.app_runner, webhook_host_ip, self.settings.WEBHOOK_HOST_PORT
        )
        await site.start()

    def stop(self):
        self.app_runner.cleanup()

    @handle_json_error
    async def process_webhook(self, request: web.Request):
        data = await request.json()
        webhook_id = request.match_info.get("webhook_id", "")
        if "trigger_id" in data:
            event = ActionEvent(data)
        else:
            event = WebHookEvent(data)
        self.event_queue.put((webhook_id, event))
