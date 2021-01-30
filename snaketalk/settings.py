from dataclasses import dataclass, field
from typing import Sequence


@dataclass
class Settings:
    """Simple dataclass to hold some values.

    Will probably be removed in the future. To run a chatbot, you should always create a
    custom Settings instance with the appropriate values.
    """

    BOT_URL: str = "chat.com"
    BOT_TOKEN: str = "token"
    BOT_TEAM: str = "team_name"
    SSL_VERIFY: bool = True
    DEBUG: bool = False
    IGNORE_USERS: Sequence[str] = field(default_factory=list)
