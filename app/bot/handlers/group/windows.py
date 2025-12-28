from contextlib import suppress
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.utils.markdown import hbold
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message
from app.bot.manager import Manager
from app.bot.utils.texts import SUPPORTED_LANGUAGES
from app.bot.utils.redis.models import UserData
from app.bot.manager import Form
import base64
from app.bot.utils.redis import RedisStorage


class Window:
    """
    Window class.
    """

    @staticmethod
    async def menu_of_user(
        manager: Manager, message: Message, redis: RedisStorage
    ) -> None:
        """
        Main of user
        :param manager: Manager object.
        :return: None
        """
        user_data = await redis.get_by_message_thread_id(message.message_thread_id)

        message_text = (
            f"<b>Информация о пользователе</b>\n"
            f"отсутствует подробная информация\n\n"
        )

        await message.reply(
            text=message_text,
        )
