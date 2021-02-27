import asyncio
from queue import Queue

from aiohttp import web

from snaketalk.settings import Settings

routes = web.RouteTableDef()


def handle_json_error(func):
    async def handler(request: web.Request):
        try:
            return await func(request)
        except asyncio.CancelledError:
            raise
        except Exception as e:
            return web.json_response({"status": "failed", "reason": str(e)}, status=400)

    return handler


class WebHookServer:
    queue: Queue

    def __init__(self):
        self.app = web.Application()
        self.app_runner = web.AppRunner(self.app)
        self.app.add_routes(routes)
        self.settings = Settings()

    async def start(self, queue: Queue):
        WebHookServer.queue = queue
        webhook_host_ip = self.settings.WEBHOOK_HOST_URL.replace("http://", "")
        await self.app_runner.setup()
        site = web.TCPSite(
            self.app_runner, webhook_host_ip, self.settings.WEBHOOK_HOST_PORT
        )
        await site.start()

    def stop(self):
        self.app_runner.cleanup()

    @routes.post("/hooks/{webhook_id}")
    @handle_json_error
    async def process_webhook(request: web.Request):
        post = await request.json()
        webhook_id = request.match_info.get("webhook_id", "")
        WebHookServer.queue.put((webhook_id, post))
