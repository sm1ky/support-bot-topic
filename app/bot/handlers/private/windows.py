# app/bot/handlers/private/windows.py
from contextlib import suppress
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.utils.markdown import hbold
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from app.bot.manager import Manager
from app.bot.utils.texts import SUPPORTED_LANGUAGES
from app.bot.utils.redis.models import UserData
from app.bot.manager import Form
from app.bot.utils.notifications import NotificationManager

from app.config import load_config


def select_language_markup() -> InlineKeyboardMarkup:
    """
    Generate an inline keyboard markup for selecting the language.

    :return: InlineKeyboardMarkup
    """
    builder = InlineKeyboardBuilder().row(
        *[
            InlineKeyboardButton(text=text, callback_data=callback_data)
            for callback_data, text in SUPPORTED_LANGUAGES.items()
        ],
        width=2,
    )
    return builder.as_markup()


class Window:

    @staticmethod
    async def select_language(manager: Manager) -> None:
        """
        Display the window for selecting the language.

        :param manager: Manager object.
        :return: None
        """
        text = manager.text_message.get("select_language")
        with suppress(IndexError, KeyError):
            text = text.format(full_name=hbold(manager.user.full_name))
        reply_markup = select_language_markup()
        await manager.send_message(text, reply_markup=reply_markup)

    @staticmethod
    async def request(manager: Manager) -> None:
        """
        Display the window for request description

        :param manager: Manager object.
        :return: None
        """

        state = await manager.state.get_data()
        choice = state.get("choice")
        text = manager.text_message.get("request")
        with suppress(IndexError, KeyError):
            text = text.format(full_name=hbold(manager.user.full_name))

        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="← Назад", callback_data="start")]
            ]
        )

        message = await manager.send_message(
            text, reply_markup=keyboard
        )  # Костыль для удаления старого сообщения
        await manager.state.update_data(request_message=message.message_id)

    @staticmethod
    async def main_menu(manager: Manager, **_) -> None:
        """
        Display the main menu window.

        :param manager: Manager object.
        :return: None
        """
        text = manager.text_message.get("main_menu")
        getstate = await manager.state.get_state()

        config = load_config()
        bot_name = config.bot.BOT_NAME

        with suppress(IndexError, KeyError):
            text = text.format(
                full_name=hbold(manager.user.full_name), bot_name=hbold(bot_name)
            )

        builder = InlineKeyboardBuilder()
        builder.row(
            InlineKeyboardButton(text="Другой вопрос", callback_data="other_question")
        )

        # Добавляем кнопку настроек уведомлений
        builder.row(
            InlineKeyboardButton(
                text="🔔 Настройки уведомлений", callback_data="notifications_settings"
            )
        )

        keyboard = builder.as_markup()

        await manager.send_message(text, reply_markup=keyboard)
        await manager.state.set_state(None)

    @staticmethod
    async def notifications_settings(
        manager: Manager, redis, user_data: UserData
    ) -> None:
        """
        Отображает настройки уведомлений пользователя.

        :param manager: Manager object.
        :param redis: RedisStorage object.
        :param user_data: UserData object.
        :return: None
        """
        status = "Включены" if user_data.notifications_enabled else "Отключены"
        text = manager.text_message.get("notification_settings").format(status=status)

        # Получаем непрочитанные уведомления
        notification_manager = NotificationManager(redis)
        notifications = await notification_manager.get_all_notifications()

        if notifications:
            text += "\n\n" + manager.text_message.get("notifications_title") + "\n\n"

            for notification in notifications:
                importance = notification.get("importance", "normal")
                message_text = notification.get("message", "")
                created_at = notification.get("created_at", "")

                if importance == "critical":
                    notification_text = manager.text_message.get(
                        "notification_critical"
                    ).format(message=message_text)
                elif importance == "important":
                    notification_text = manager.text_message.get(
                        "notification_important"
                    ).format(message=message_text)
                else:
                    notification_text = manager.text_message.get(
                        "notification_normal"
                    ).format(message=message_text)

                text += notification_text + "\n<i>" + created_at + "</i>\n"
                text += f"<code>ID: {notification.get('id')}</code>\n\n"
        else:
            text += "\n\n" + manager.text_message.get("no_notifications")

        # Создаем клавиатуру
        builder = InlineKeyboardBuilder()

        if user_data.notifications_enabled:
            builder.row(
                InlineKeyboardButton(
                    text="🔕 Отключить уведомления",
                    callback_data="notifications_disable",
                )
            )
        else:
            builder.row(
                InlineKeyboardButton(
                    text="🔔 Включить уведомления", callback_data="notifications_enable"
                )
            )

        if notifications:
            builder.row(
                InlineKeyboardButton(
                    text="✅ Отметить прочитанными", callback_data="notifications_read"
                )
            )
            builder.row(
                InlineKeyboardButton(
                    text="🗑️ Удалить все уведомления",
                    callback_data="clear_all_notifications",
                )
            )

            # Добавляем кнопки для удаления отдельных уведомлений
            for notification in notifications:
                notification_id = notification.get("id")
                message_preview = (
                    notification.get("message", "")[:20] + "..."
                    if len(notification.get("message", "")) > 20
                    else notification.get("message", "")
                )
                builder.row(
                    InlineKeyboardButton(
                        text=f"❌ Удалить: {message_preview}",
                        callback_data=f"delete_notification_{notification_id}",
                    )
                )

        builder.row(InlineKeyboardButton(text="← Назад в меню", callback_data="start"))

        await manager.send_message(text, reply_markup=builder.as_markup())

    @staticmethod
    async def change_language(manager: Manager) -> None:
        """
        Display the window for changing the language.

        :param manager: Manager object.
        :return: None
        """
        text = manager.text_message.get("change_language")
        reply_markup = select_language_markup()
        await manager.send_message(text, reply_markup=reply_markup)

    @staticmethod
    async def command_source(manager: Manager) -> None:
        """
        Display the window with information about the command source.

        :param manager: Manager object.
        :return: None
        """
        text = manager.text_message.get("command_source")
        await manager.send_message(text)
