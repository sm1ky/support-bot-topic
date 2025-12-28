# app/bot/handlers/private/command.py
from aiogram import Router, F
from aiogram.filters import Command, MagicData
from aiogram.types import Message
from aiogram_newsletter.manager import ANManager

from app.bot.handlers.private.windows import Window
from app.bot.manager import Manager
from app.bot.utils.create_forum_topic import get_or_create_forum_topic
from app.bot.utils.redis import RedisStorage
from app.bot.utils.redis.models import UserData
from app.bot.utils.notifications import NotificationManager

router = Router()
router.message.filter(F.chat.type == "private")


@router.message(Command("start"))
async def handler(
        message: Message,
        manager: Manager,
        redis: RedisStorage,
        user_data: UserData,
) -> None:
    """
    Handles the /start command.

    If the user has already selected a language, displays the main menu window.
    Otherwise, prompts the user to select a language.

    :param message: Message object.
    :param manager: Manager object.
    :param redis: RedisStorage object.
    :param user_data: UserData object.
    :return: None
    """
    if user_data.language_code:
        # Проверяем наличие важных уведомлений
        notification_manager = NotificationManager(redis)
        has_notifications = await notification_manager.show_important_notifications_with_confirmation(manager, user_data.id)
        
        # Если были показаны уведомления, не показываем главное меню
        # Оно будет показано после подтверждения уведомлений
        if not has_notifications:
            await Window.main_menu(manager)
    else:
        await Window.select_language(manager)
    await manager.delete_message(message)

    # Create the forum topic
    await get_or_create_forum_topic(message.bot, redis, manager.config, user_data)


@router.message(Command("time"))
async def handler(message: Message, manager: Manager, user_data: UserData) -> None:

    last_message_date = user_data.last_message_date
    text = f"Last time: {last_message_date}"

    return await manager.send_message(text)


@router.message(Command("language"))
async def handler(message: Message, manager: Manager, user_data: UserData) -> None:
    """
    Handles the /language command.

    If the user has already selected a language, prompts the user to select a new language.
    Otherwise, prompts the user to select a language.

    :param message: Message object.
    :param manager: Manager object.
    :param user_data: UserData object.
    :return: None
    """
    if user_data.language_code:
        await Window.change_language(manager)
    else:
        await Window.select_language(manager)
    await manager.delete_message(message)


@router.message(Command("notifications"))
async def notifications_handler(message: Message, manager: Manager, redis: RedisStorage, user_data: UserData) -> None:
    """
    Обрабатывает команду /notifications.
    Отображает настройки уведомлений пользователя и позволяет включить/выключить уведомления.

    :param message: Message object.
    :param manager: Manager object.
    :param redis: RedisStorage object.
    :param user_data: UserData object.
    :return: None
    """
    await Window.notifications_settings(manager, redis, user_data)
    await manager.delete_message(message)


@router.message(
    Command("newsletter"),
    MagicData(F.event_from_user.id == F.config.bot.DEV_ID),  # type: ignore
)
async def handler(
        message: Message,
        manager: Manager,
        an_manager: ANManager,
        redis: RedisStorage,
) -> None:
    """
    Handles the /newsletter command.

    :param message: Message object.
    :param manager: Manager object.
    :param redis: RedisStorage object.
    :param an_manager: Manager object from aiogram_newsletter.
    :return: None
    """
    users_ids = await redis.get_all_users_ids()
    await an_manager.newsletter_menu(users_ids, Window.main_menu)
    await manager.delete_message(message)


@router.message(
    Command("add_notification"),
    MagicData(F.event_from_user.id == F.config.bot.DEV_ID),  # type: ignore
)
async def add_notification_handler(message: Message, manager: Manager, redis: RedisStorage) -> None:
    """
    Обрабатывает команду /add_notification для админа.
    Позволяет добавить новое системное уведомление.

    :param message: Message object.
    :param manager: Manager object.
    :param redis: RedisStorage object.
    :return: None
    """
    # Парсим аргументы команды
    command_parts = message.text.split(maxsplit=3)
    
    if len(command_parts) < 3:
        await message.reply("Использование: /add_notification [важность] [текст]\n"
                          "Где важность: normal, important, critical")
        return
    
    importance = command_parts[1].lower()
    notification_text = command_parts[2]
    
    if len(command_parts) > 3:
        notification_text += " " + command_parts[3]
    
    if importance not in ["normal", "important", "critical"]:
        await message.reply("Неверный уровень важности. Используйте: normal, important, critical")
        return
    
    notification_manager = NotificationManager(redis)
    success = await notification_manager.add_notification(notification_text, importance)
    
    if success:
        await message.reply(manager.text_message.get("add_notification_success"))
    else:
        await message.reply("Ошибка при добавлении уведомления.")