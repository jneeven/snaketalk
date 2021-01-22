import asyncio

from snaketalk.message import Message
from snaketalk.plugins.base import Plugin, listen_to


class DefaultPlugin(Plugin):
    @listen_to(r"^test$", needs_mention=True)
    async def test(self, message: Message):
        print("test function called!")
        await asyncio.sleep(10)
        print(message.text)

    @listen_to(r"^test_2\s?(.*)$")
    def test_2(self, message: Message, additional_text=None):
        print(f"test_2 function called! Additional text: {additional_text}")

    @listen_to(r"^test_3$", direct_only=True)
    async def test_3(self, message: Message):
        print("test_3 function called!")
