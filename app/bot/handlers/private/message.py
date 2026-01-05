# app/bot/handlers/private/message.py
import asyncio
import json
import logging  # Добавлен недостающий импорт
from datetime import datetime, timezone, timedelta
from contextlib import suppress
from aiogram import Router, F
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import StateFilter, MagicData
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message

from app.bot.manager import Manager
from app.bot.types.album import Album
from app.bot.utils.create_forum_topic import (
    create_forum_topic,
    get_or_create_forum_topic,
)
from app.bot.utils.redis import RedisStorage
from app.bot.utils.redis.models import UserData


from app.bot.handlers.private.windows import Window
from app.bot.manager import Form

from app.bot.utils.topics import TopicManager
from app.bot.utils.notifications import NotificationManager

from aiogram_newsletter.utils.states import ANState

router = Router()
router.message.filter((F.chat.type == "private"), ~StateFilter(ANState))


@router.message(
    StateFilter("waiting_notification_text"),
    MagicData(F.event_from_user.id == F.config.bot.DEV_ID),
)
async def handle_notification_text(
    message: Message, manager: Manager, redis: RedisStorage
) -> None:
    """
    Обрабатывает ввод текста уведомления.

    :param message: Message object.
    :param manager: Manager object.
    :param redis: RedisStorage object.
    :return: None
    """
    # Получаем данные о важности уведомления
    state_data = await manager.state.get_data()
    importance = state_data.get("notification_importance", "normal")

    # Создаем уведомление
    notification_manager = NotificationManager(redis)
    success = await notification_manager.add_notification(message.text, importance)

    # Сбрасываем состояние
    await manager.state.clear()

    if success:
        # Сообщение об успешном создании уведомления
        text = manager.text_message.get("add_notification_success")
        await manager.send_message(text)

        # Возвращаемся в админ-меню
        await Window.admin_menu(manager, redis)
    else:
        # Сообщение об ошибке
        text = manager.text_message.get("add_notification_error")
        await manager.send_message(text)

    # Удаляем сообщение с текстом уведомления
    await manager.delete_message(message)


@router.message(StateFilter(Form.WAITING))
@router.message(StateFilter(Form.PAYMENT))
@router.message(StateFilter(Form.OTHER))
@router.message(F.media_group_id)
@router.message(F.media_group_id.is_(None))
async def handle_waiting_state(
    message: Message,
    manager: Manager,
    redis: RedisStorage,
    user_data: UserData,
    album: Album | None = None,
) -> None:
    """
    Handle messages in the waiting state.

    :param message: The message.
    :param manager: Manager object.
    :return: None
    """

    # Check if the user is banned
    if user_data.is_banned:
        return

    message_thread_id = await get_or_create_forum_topic(
        message.bot,
        redis,
        manager.config,
        user_data,
    )

    current_state = await manager.state.get_state()
    state_data = await manager.state.get_data()
    topic_manager = TopicManager(manager.bot, redis, manager.config)

    # Проверка: если статус "closed" или не установлен, то установить "new"
    if user_data.topic_status == "closed" or not user_data.topic_status:
        logging.info(
            f"Изменяем статус с '{user_data.topic_status}' на 'new' для пользователя {user_data.id}"
        )
        await topic_manager.new_topic(message, user_data)

        # Проверяем наличие важных уведомлений при создании нового тикета
        notification_manager = NotificationManager(redis)
        await notification_manager.show_important_notifications_with_confirmation(
            manager, user_data.id
        )

    if current_state is None and (
        not user_data.topic_status or user_data.topic_status == "closed"
    ):
        return await Window.main_menu(manager)

    async def copy_message_to_topic():
        """
        Copies the message or album to the forum topic.
        If no album is provided, the message is copied. Otherwise, the album is copied.
        """

        message_thread_id = await get_or_create_forum_topic(
            message.bot,
            redis,
            manager.config,
            user_data,
        )

        choose = state_data.get("choosed_service")
        service_id = state_data.get("service_id")

        if current_state == Form.WAITING:
            message_text = manager.text_message.get("subscription_question")
            with suppress(IndexError, KeyError):
                message_text = message_text.format(name=choose, service_id=service_id)
        elif current_state == Form.PAYMENT:
            message_text = manager.text_message.get("payment_question")
        elif current_state == Form.OTHER:
            message_text = manager.text_message.get("other_question")
        else:
            message_text = ""

        if current_state is not None:
            keyboard = InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text="✅ Принять обращение", callback_data="apply_appeal"
                        )
                    ]
                ]
            )
            await message.bot.send_message(
                chat_id=manager.config.bot.GROUP_ID,
                message_thread_id=message_thread_id,
                text=message_text,
                reply_markup=keyboard,
            )

        # Получаем маппинг сообщений из Redis
        message_mapping_key = f"message_mapping:{user_data.id}"
        message_mapping_data = await redis.redis.get(message_mapping_key)
        message_mapping = {}
        if message_mapping_data:
            message_mapping = json.loads(message_mapping_data)

        reply_to_message_id = None

        # Проверяем, есть ли reply на сообщение
        if message.reply_to_message:
            # Ищем соответствующее сообщение в топике (обратный маппинг)
            user_msg_id = str(message.reply_to_message.message_id)
            # Ищем в маппинге, где ключ - это message_id в личке пользователя
            if user_msg_id in message_mapping:
                reply_to_message_id = message_mapping[user_msg_id]
                logging.info(
                    f"Found reply mapping: user {user_msg_id} -> topic {reply_to_message_id}"
                )
            else:
                # Если маппинг не найден, отправляем информацию о reply текстом
                reply_text = (
                    message.reply_to_message.text
                    or message.reply_to_message.caption
                    or "[медиа]"
                )
                reply_header = f"<blockquote>↩️ Reply to:\n{reply_text}</blockquote>\n\n"

                await message.bot.send_message(
                    chat_id=manager.config.bot.GROUP_ID,
                    message_thread_id=message_thread_id,
                    text=reply_header,
                    parse_mode="HTML",
                )

        if not album:
            msg = await message.copy_to(
                chat_id=manager.config.bot.GROUP_ID,
                message_thread_id=message_thread_id,
                reply_to_message_id=reply_to_message_id,
            )

            # Сохраняем маппинг: user_message_id -> topic_message_id
            message_mapping[str(message.message_id)] = msg.message_id
        else:
            # Копируем альбом
            msg_list = await album.copy_to(
                chat_id=manager.config.bot.GROUP_ID,
                message_thread_id=message_thread_id,
            )

            # Сохраняем маппинг для первого сообщения альбома
            if isinstance(msg_list, list) and len(msg_list) > 0:
                message_mapping[str(message.message_id)] = msg_list[0].message_id

            # Берем первое сообщение для даты
            msg = msg_list[0] if isinstance(msg_list, list) else msg_list

        # Сохраняем обновленный маппинг в Redis
        await redis.redis.set(
            message_mapping_key,
            json.dumps(message_mapping),
            ex=86400 * 7,  # Храним 7 дней
        )

        last_message_date = msg.date.astimezone(timezone(timedelta(hours=3))).strftime(
            "%Y-%m-%d %H:%M:%S%z"
        )
        user_data.last_message_date = last_message_date
        await redis.update_user(user_data.id, user_data)
        logging.info(f"Last message date updated: {user_data.last_message_date}")

        await manager.state.clear()

    try:
        await copy_message_to_topic()
    except TelegramBadRequest as ex:
        if "message thread not found" in ex.message:
            user_data.message_thread_id = await create_forum_topic(
                message.bot,
                manager.config,
                user_data.full_name,
            )
            await redis.update_user(user_data.id, user_data)
            await copy_message_to_topic()
        else:
            raise

    # Delete previous message
    request_message = state_data.get("request_message")
    if request_message is not None:
        await message.bot.delete_message(
            chat_id=user_data.id, message_id=request_message
        )
        await manager.state.update_data(request_message=None)

    # Send a confirmation message to the user
    get_question_position: int | None = await TopicManager.get_question_position(
        redis, user_data.id
    )

    # Проверяем статус топика (открыт/принят в работу или новый)
    if user_data.topic_status == "open":
        text = manager.text_message.get("message_sent_topic_open")
    else:
        text = manager.text_message.get("message_sent")
        with suppress(IndexError, KeyError):
            text = text.format(position=get_question_position)

    # Reply to the edited message with the specified text
    msg = await message.reply(text)
    # Wait for 5 seconds before deleting the reply
    await asyncio.sleep(5)
    # Delete the reply to the edited message
    await msg.delete()
    await manager.state.clear()


@router.edited_message()
async def handle_edited_message(message: Message, manager: Manager) -> None:
    """
    Handle edited messages.

    :param message: The edited message.
    :param manager: Manager object.
    :return: None
    """
    # Get the text for the edited message
    text = manager.text_message.get("message_edited")
    # Reply to the edited message with the specified text
    msg = await message.reply(text)
    # Wait for 5 seconds before deleting the reply
    await asyncio.sleep(5)
    # Delete the reply to the edited message
    await msg.delete()
