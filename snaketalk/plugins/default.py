import asyncio

from snaketalk.message import Message
from snaketalk.plugins.base import Plugin, listen_to


class DefaultPlugin(Plugin):
    @listen_to(r".*")
    async def test(self, message: Message):
        print("test function called!")
        await asyncio.sleep(10)
        print(message.text)

    @listen_to(r"test_2")
    def test_2(self, message: Message):
        print("test_2 function called!")
