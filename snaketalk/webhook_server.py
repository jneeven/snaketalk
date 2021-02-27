import asyncio

from aiohttp import ClientSession, web

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


@routes.post("/hooks/{webhook_id}")
@handle_json_error
async def process_webhook(request: web.Request):
    post = await request.json()
    text = post["context"]["text"]
    webhook_url = post["context"]["webhook_url"]
    # webhook_id = request.match_info.get("webhook_id", "")
    payload = {"text": text}
    async with ClientSession() as session:
        await session.post(webhook_url, json=payload)

    # TODO: Improve processing of Webhooks.


@routes.post("/actions/{action}")
@handle_json_error
async def process_action(request: web.Request):
    post = await request.json()
    print(post)
    data = post["context"]["data"]
    if data == "ping":
        return web.json_response(
            {
                "update": {"message": f"You sent {data}, I send pong!", "props": {}},
                "ephemeral_text": "You updated the post!",
            }
        )


class WebhookServer:
    def __init__(self):
        self.app = web.Application()
        self.app_runner = web.AppRunner(self.app)
        self.app.add_routes(routes)
        self.settings = Settings()

    async def start(self):
        webhook_host_ip = self.settings.WEBHOOK_HOST_URL.replace("http://", "")
        await self.app_runner.setup()
        site = web.TCPSite(
            self.app_runner, webhook_host_ip, self.settings.WEBHOOK_HOST_PORT
        )
        await site.start()

    def stop(self):
        self.app_runner.cleanup()
