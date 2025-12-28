# app/bot/utils/redis/models.py
from dataclasses import dataclass, asdict
from datetime import datetime, timezone, timedelta


@dataclass
class UserData:
    """Data class representing user information."""
    message_thread_id: int | None
    message_silent_id: int | None
    message_silent_mode: bool

    id: int
    full_name: str
    username: str | None
    topic_status: str = ""
    state: str = "member"
    is_banned: bool = False
    language_code: str | None = None
    last_message_date: str | None = None
    notifications_enabled: bool = True  # Включены ли уведомления для пользователя
    last_notification_read: str | None = None  # Время когда пользователь последний раз просматривал уведомления
    created_at: str = datetime.now(timezone(timedelta(hours=3))).strftime("%Y-%m-%d %H:%M:%S %Z")

    def to_dict(self) -> dict:
        """
        Converts UserData object to a dictionary.

        :return: Dictionary representation of UserData.
        """
        return asdict(self)