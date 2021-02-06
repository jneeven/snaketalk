import asyncio
import json
import re
from collections import defaultdict
from typing import Sequence

from snaketalk.driver import Driver
from snaketalk.message import Message
from snaketalk.plugins import Plugin
from snaketalk.settings import Settings


class MessageHandler(object):
    def __init__(
        self,
        driver: Driver,
        settings: Settings,
        plugins: Sequence[Plugin],
        ignore_own_messages=True,
    ):
        """The MessageHandler class takes care of the connection to mattermost and
        calling the appropriate response function to each event."""
        self.driver = driver
        self.settings = settings
        self.ignore_own_messages = ignore_own_messages
        self.plugins = plugins

        self._name_matcher = re.compile(rf"^@{self.driver.username}\:?\s?")

        # Collect the listeners from all plugins
        self.listeners = defaultdict(list)
        for plugin in self.plugins:
            for matcher, functions in plugin.listeners.items():
                self.listeners[matcher].extend(functions)

        print("Registered listeners:")
        print(
            json.dumps(
                {
                    pattern.pattern: list([function.name for function in functions])
                    for (pattern, functions) in self.listeners.items()
                },
                indent=4,
            )
        )

    def start(self):
        # This is blocking, will loop forever
        self.driver.init_websocket(self.handle_event)

    def _should_ignore(self, message):
        # Ignore message from senders specified in settings, and maybe from ourself
        return (
            True
            if message.sender_name.lower()
            in (name.lower() for name in self.settings.IGNORE_USERS)
            else False
        ) or (self.ignore_own_messages and message.sender_name == self.driver.username)

    async def handle_event(self, data):
        post = json.loads(data)
        event_action = post.get("event")
        if event_action == "posted":
            await self._handle_post(post)

    async def _handle_post(self, post):
        # For some reason these are JSON strings, so need to parse them first
        for item in ["post", "mentions"]:
            if post.get("data", {}).get(item):
                post["data"][item] = json.loads(post["data"][item])

        # If the post starts with a mention of this bot, strip off that part.
        post["data"]["post"]["message"] = self._name_matcher.sub(
            "", post["data"]["post"]["message"]
        )
        message = Message(post)
        if self._should_ignore(message):
            return

        print(json.dumps(post, indent=4))

        # Find all the listeners that match this message, and have their plugins handle
        # the rest.
        tasks = []
        for matcher, functions in self.listeners.items():
            match = matcher.match(message.text)
            if match:
                groups = list([group for group in match.groups() if group != ""])
                for function in functions:
                    # Create an asyncio task to handle this callback
                    tasks.append(
                        asyncio.create_task(
                            function.plugin.call_function(
                                function, message, groups=groups
                            )
                        )
                    )
        # Execute the callbacks in parallel
        asyncio.gather(*tasks)
