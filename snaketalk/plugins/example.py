import asyncio
import re
from pathlib import Path

import mattermostdriver

from snaketalk.message import Message
from snaketalk.plugins.base import Plugin, listen_to


class ExamplePlugin(Plugin):
    """Default plugin with examples of bot functionality and usage."""

    @listen_to("^admin$", direct_only=True, allowed_users=["admin", "root"])
    async def users_access(self, message: Message):
        """Showcases a function with restricted access."""
        self.driver.reply_to(message, "Access allowed!")

    @listen_to("^busy|jobs$", re.IGNORECASE, needs_mention=True)
    async def busy_reply(self, message: Message):
        """Show the number of busy worker threads."""
        busy = self.driver.threadpool.get_busy_workers()
        self.driver.reply_to(
            message,
            f"Number of busy worker threads: {busy}",
        )

    @listen_to("^hello_channel$", needs_mention=True)
    async def hello_channel(self, message: Message):
        """Responds with a channel post rather than a reply."""
        self.driver.create_post(channel_id=message.channel_id, message="hello channel!")

    # Needs admin permissions
    @listen_to("^hello_ephemeral$", needs_mention=True)
    async def hello_ephemeral(self, message: Message):
        """Tries to reply with an ephemeral message, if the bot has system admin
        permissions."""
        try:
            self.driver.reply_to(message, "hello sender!", ephemeral=True)
        except mattermostdriver.exceptions.NotEnoughPermissions:
            self.driver.reply_to(
                message, "I do not have permission to create ephemeral posts!"
            )

    @listen_to("^hello_react$", re.IGNORECASE, needs_mention=True)
    async def hello_react(self, message: Message):
        """Responds by giving a thumbs up reaction."""
        self.driver.react_to(message, "+1")

    @listen_to("^hello_file$", re.IGNORECASE, needs_mention=True)
    async def hello_file(self, message: Message):
        """Responds by uploading a text file."""
        file = Path("/tmp/hello.txt")
        file.write_text("Hello from this file!")
        self.driver.reply_to(message, "Here you go", file_paths=[file])

    @listen_to("^!hello_webhook$", re.IGNORECASE)
    async def hello_webhook(self, message: Message):
        self.driver.webhooks.call_webhook(
            "eauegoqk4ibxigfybqrsfmt48r",
            options={
                "username": "webhook_test",  # Requires the right webhook permissions
                "channel": "off-topic",
                "text": "Hello?",
                "attachments": [
                    {
                        "fallback": "Fallback text",
                        "title": "Title",
                        "author_name": "Author",
                        "text": "Attachment text here...",
                        "color": "#59afe1",
                    }
                ],
            },
        )

    @listen_to("^!info$")
    async def info(self, message: Message):
        """Responds with the user info of the requesting user."""
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
        """Pong."""
        self.driver.reply_to(message, "pong")

    @listen_to("^sleep ([0-9]+)", needs_mention=True)
    async def sleep_reply(self, message: Message, seconds: str):
        """Sleeps for the specified number of seconds.
        Arguments:
            - seconds: How many seconds to sleep for."""
        self.driver.reply_to(message, f"Okay, I will be waiting {seconds} seconds.")
        await asyncio.sleep(int(seconds))
        self.driver.reply_to(message, "Done!")
