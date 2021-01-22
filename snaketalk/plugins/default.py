import asyncio
import re
from pathlib import Path

import mattermostdriver

from snaketalk.message import Message
from snaketalk.plugins.base import Plugin, listen_to


class DefaultPlugin(Plugin):
    @listen_to("^admin$", direct_only=True, allowed_users=["admin", "root"])
    async def users_access(self, message: Message):
        self.driver.reply_to(message, "Access allowed!")

    @listen_to("^busy|jobs$", re.IGNORECASE, needs_mention=True)
    async def busy_reply(self, message: Message):
        """Show the number of budy worker threads."""
        busy = self.driver.threadpool.get_busy_workers()
        self.driver.reply_to(
            message,
            f"Number of busy worker threads: {busy}",
        )

    @listen_to("hello$", re.IGNORECASE, needs_mention=True)
    async def hello_reply(self, message: Message):
        self.driver.reply_to(message, "hello sender!")

    @listen_to("hello_formatting$", needs_mention=True)
    async def hello_reply_formatting(self, message: Message):
        # Format message with italic style
        self.driver.reply_to(message, "_hello_ sender!")

    @listen_to("hello_channel$", needs_mention=True)
    async def hello_channel(self, message: Message):
        self.driver.create_post(channel_id=message.channel_id, message="hello channel!")

    # Needs admin permissions
    @listen_to("hello_ephemeral$", needs_mention=True)
    async def hello_empemeral(self, message: Message):
        try:
            self.driver.reply_to(message, "hello sender!", ephemeral=True)
        except mattermostdriver.exceptions.NotEnoughPermissions:
            self.driver.reply_to(
                message, "I do not have permission to create ephemeral posts!"
            )

    @listen_to("^hello_react$ ", re.IGNORECASE, needs_mention=True)
    async def hello_react(self, message: Message):
        self.driver.react_to(message, "+1")

    @listen_to("^hello_file$", re.IGNORECASE, needs_mention=True)
    async def hello_file(self, message: Message):
        file = Path("/tmp/hello.txt")
        file.write_text("Hello from this file!")
        self.driver.reply_to(message, "Here you go", file_paths=[file])

    # TODO: add webhook call option

    @listen_to("^!info$")
    async def info_request(self, message: Message):
        user_email = self.driver.get_user_info(message.user_id)["email"]
        reply = (
            f"TEAM-ID: {message.team_id}\nUSERNAME: {message.sender_name}\n"
            f"EMAIL: {user_email}\nUSER-ID: {message.user_id}\n"
            f"IS-DIRECT: {message.is_direct_message}\nMENTIONS: {message.mentions}\n"
            f"MESSAGE: {message.text}"
        )
        self.driver.reply_to(message, reply)

    @listen_to("^ping$", re.IGNORECASE, needs_mention=True)
    async def ping_reply(self, message: Message):
        self.driver.reply_to(message, "pong")

    @listen_to("sleep ([0-9]+)", needs_mention=True)
    async def sleep_reply(self, message: Message, seconds: str):
        self.driver.reply_to(message, f"Okay, I will be waiting {seconds} seconds.")
        await asyncio.sleep(int(seconds))
        self.driver.reply_to(message, "Done!")
