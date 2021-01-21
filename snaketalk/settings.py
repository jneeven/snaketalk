from dataclasses import dataclass, field
from typing import Sequence


@dataclass
class Settings:
    BOT_URL: str = "chat.com"
    BOT_TOKEN: str = "token"
    BOT_TEAM: str = "team_name"
    SSL_VERIFY: bool = True
    DEBUG: bool = False
    IGNORE_USERS: Sequence[str] = field(default_factory=list)
