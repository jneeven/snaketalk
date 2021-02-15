import asyncio
import re
from datetime import datetime
from pathlib import Path

import mattermostdriver

from snaketalk.message import Message
from snaketalk.plugins.base import Plugin, listen_to
from snaketalk.scheduler import schedule


class ExamplePlugin(Plugin):
    """Default plugin with examples of bot functionality and usage."""

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

    @listen_to("^hello_channel$", needs_mention=True)
    async def hello_channel(self, message: Message):
        self.driver.create_post(channel_id=message.channel_id, message="hello channel!")

    # Needs admin permissions
    @listen_to("^hello_ephemeral$", needs_mention=True)
    async def hello_ephemeral(self, message: Message):
        try:
            self.driver.reply_to(message, "hello sender!", ephemeral=True)
        except mattermostdriver.exceptions.NotEnoughPermissions:
            self.driver.reply_to(
                message, "I do not have permission to create ephemeral posts!"
            )

    @listen_to("^hello_react$", re.IGNORECASE, needs_mention=True)
    async def hello_react(self, message: Message):
        self.driver.react_to(message, "+1")

    @listen_to("^hello_file$", re.IGNORECASE, needs_mention=True)
    async def hello_file(self, message: Message):
        file = Path("/tmp/hello.txt")
        file.write_text("Hello from this file!")
        self.driver.reply_to(message, "Here you go", file_paths=[file])

    # TODO: add webhook call option

    @listen_to("^!info$")
    async def info(self, message: Message):
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

    @listen_to("^reply at (.*)$", re.IGNORECASE, needs_mention=True)
    def schedule_once(self, message: Message, trigger_time: str):
        """Schedules a reply to be sent at the given time.

        Arguments:
        - triger_time (str): Timestamp of format %d-%m-%Y_%H:%M:%S,
            e.g. 20-02-2021_20:22:01. The reply will be sent at that time.
        """
        try:
            time = datetime.strptime(trigger_time, "%d-%m-%Y_%H:%M:%S")
            self.driver.reply_to(message, f"Scheduled message at {trigger_time}!")
            schedule.once(time).do(
                self.driver.reply_to, message, "This is the scheduled message!"
            )
        except ValueError as e:
            self.driver.reply_to(message, str(e))

    @listen_to("^schedule every ([0-9]+)$", re.IGNORECASE, needs_mention=True)
    def schedule_every(self, message: Message, seconds: int):
        """Schedules a reply every x seconds. Use the `cancel jobs` command to stop.

        Arguments:
        - seconds (int): number of seconds between each reply.
        """
        schedule.every(int(seconds)).seconds.do(
            self.driver.reply_to, message, f"Scheduled message every {seconds} seconds!"
        )

    @listen_to("^cancel jobs$", re.IGNORECASE, needs_mention=True)
    def cancel_jobs(self, message: Message):
        """Cancels all scheduled jobs, including recurring and one-time events."""
        schedule.clear()
        self.driver.reply_to(message, "Canceled all jobs.")

    @listen_to("^sleep ([0-9]+)$", needs_mention=True)
    async def sleep_reply(self, message: Message, seconds: str):
        self.driver.reply_to(message, f"Okay, I will be waiting {seconds} seconds.")
        await asyncio.sleep(int(seconds))
        self.driver.reply_to(message, "Done!")
