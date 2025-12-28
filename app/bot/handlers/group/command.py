import asyncio
import logging
from contextlib import suppress

from aiogram import Router, F
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command, MagicData
from aiogram.types import Message
from aiogram.utils.markdown import hcode, hlink

from app.bot.manager import Manager
from app.bot.utils.redis import RedisStorage
from app.bot.utils.topics import TopicManager

from app.bot.handlers.group.windows import Window

from app.config import Config
from app.bot.jobs.send_new_topics import send_new_topics

router_id = Router()
router_id.message.filter(
    F.chat.type.in_(["group", "supergroup"]),
    F.message_thread_id.is_(None),
)


@router_id.message(Command("id"))
async def handler(message: Message) -> None:
    """
    Sends chat ID in response to the /id command.

    :param message: Message object.
    :return: None
    """
    await message.reply(hcode(message.chat.id))
    await message.reply(hcode(message.message_thread_id))
    await message.delete()


@router_id.message(Command("summary"))
async def handler(message: Message, config: Config) -> None:
    await message.delete()
    await send_new_topics(message.bot, config)


@router_id.message(Command("closeall"))
async def close_all_topics(
    message: Message, manager: Manager, redis: RedisStorage
) -> None:
    """
    Закрывает все открытые топики.

    :param message: Message object.
    :param manager: Manager object.
    :param redis: RedisStorage object.
    :return: None
    """
    # Перенаправляем в лог для отладки
    logging.info("Вызвана команда closeall")

    # Проверка прав (можно убрать для отладки)
    if message.from_user.id != manager.config.bot.DEV_ID:
        logging.info(
            f"Отказано в доступе: {message.from_user.id} != {manager.config.bot.DEV_ID}"
        )
        await message.reply("У вас нет прав для выполнения этой команды.")
        await message.delete()
        return

    # Отправляем сообщение о начале процесса
    status_msg = await message.reply("⏳ Начинаю закрытие топиков...")
    logging.info("Начинаю процесс закрытия всех топиков")

    # Получаем все ID пользователей
    user_ids = await redis.get_all_users_ids()
    logging.info(f"Получено {len(user_ids)} пользователей")

    # Счетчики для статистики
    closed = 0
    already_closed = 0
    errors = 0

    # Простой и прямой подход к закрытию топиков
    for user_id in user_ids:
        try:
            # Получаем данные пользователя
            user_data = await redis.get_user(user_id)

            # Проверяем необходимые условия
            if not user_data or not user_data.message_thread_id:
                logging.info(f"Пропускаю пользователя {user_id}: нет thread_id")
                continue

            # Проверяем статус топика
            if user_data.topic_status not in ("new", "open"):
                already_closed += 1
                logging.info(
                    f"Топик пользователя {user_id} уже закрыт: {user_data.topic_status}"
                )
                continue

            # Меняем статус в Redis
            old_status = user_data.topic_status
            user_data.topic_status = "closed"
            await redis.update_user(user_data.id, user_data)
            logging.info(
                f"Изменен статус пользователя {user_id} с {old_status} на closed"
            )

            # Обновляем название топика
            try:
                new_name = f"⭕️ {user_data.full_name}"
                await message.bot.edit_forum_topic(
                    chat_id=manager.config.bot.GROUP_ID,
                    message_thread_id=user_data.message_thread_id,
                    name=new_name,
                )
                logging.info(f"Изменено название топика для {user_id}")
            except Exception as e:
                logging.error(
                    f"Ошибка при изменении названия топика для {user_id}: {e}"
                )
                errors += 1
                continue

            # Закрываем топик
            try:
                await message.bot.close_forum_topic(
                    chat_id=manager.config.bot.GROUP_ID,
                    message_thread_id=user_data.message_thread_id,
                )
                logging.info(f"Закрыт топик для {user_id}")
            except Exception as e:
                logging.error(f"Ошибка при закрытии топика для {user_id}: {e}")
                # Не увеличиваем счетчик ошибок, т.к. главное что статус изменился

            # Отправляем уведомление пользователю
            try:
                text = manager.text_message.get("closed_topic_bulk")
                await message.bot.send_message(chat_id=user_id, text=text)
                logging.info(f"Отправлено уведомление пользователю {user_id}")
            except Exception as e:
                logging.error(
                    f"Ошибка при отправке уведомления пользователю {user_id}: {e}"
                )

            closed += 1

            # Обновляем статус каждые 5 пользователей
            if closed % 5 == 0:
                await status_msg.edit_text(
                    f"⏳ Закрытие топиков в процессе...\n"
                    f"Обработано: {closed + already_closed + errors}/{len(user_ids)}\n"
                    f"Закрыто: {closed}"
                )

            # Небольшая пауза чтобы избежать флуда
            await asyncio.sleep(0.3)

        except Exception as e:
            logging.error(
                f"Непредвиденная ошибка при обработке пользователя {user_id}: {e}"
            )
            errors += 1

    # Финальный отчет
    final_report = (
        f"✅ <b>Результат закрытия топиков:</b>\n\n"
        f"✅ Успешно закрыто: {closed}\n"
        f"⭕️ Уже были закрыты: {already_closed}\n"
        f"❌ Ошибки: {errors}\n"
        f"📊 Всего обработано: {closed + already_closed + errors}/{len(user_ids)}"
    )

    await status_msg.edit_text(final_report)
    logging.info(
        f"Завершено закрытие топиков: {closed} закрыто, {already_closed} уже были закрыты, {errors} ошибок"
    )
    await message.delete()


router = Router()
router.message.filter(
    F.message_thread_id.is_not(None),
    F.chat.type.in_(["group", "supergroup"]),
    MagicData(F.event_chat.id == F.config.bot.GROUP_ID),  # type: ignore
)


@router.message(Command("silent"))
async def handler(message: Message, manager: Manager, redis: RedisStorage) -> None:
    """
    Toggles silent mode for a user in the group.
    If silent mode is disabled, it will be enabled, and vice versa.

    :param message: Message object.
    :param manager: Manager object.
    :param redis: RedisStorage object.
    :return: None
    """
    user_data = await redis.get_by_message_thread_id(message.message_thread_id)
    if not user_data:
        return None  # noqa

    url = (
        f"https://t.me/{message.from_user.username}"
        if message.from_user.username != "-"
        else f"tg://user?id={message.from_user.id}"
    )

    if user_data.message_silent_mode:
        text = manager.text_message.get("silent_mode_disabled")
        with suppress(IndexError, KeyError):
            text = text.format(full_name=hlink(message.from_user.full_name, url))

        with suppress(TelegramBadRequest):
            # Reply with the specified text
            await message.reply(text)

            # Unpin the chat message with the silent mode status
            await message.bot.unpin_chat_message(
                chat_id=message.chat.id,
                message_id=user_data.message_silent_id,
            )

        user_data.message_silent_mode = False
        user_data.message_silent_id = None
    else:
        text = manager.text_message.get("silent_mode_enabled")
        with suppress(IndexError, KeyError):
            text = text.format(full_name=hlink(message.from_user.full_name, url))
        with suppress(TelegramBadRequest):
            # Reply with the specified text
            msg = await message.reply(text)

            # Pin the chat message with the silent mode status
            await msg.pin(disable_notification=True)

        user_data.message_silent_mode = True
        user_data.message_silent_id = msg.message_id

    await redis.update_user(user_data.id, user_data)
    await message.delete()


@router.message(Command("information"))
async def handler(message: Message, manager: Manager, redis: RedisStorage) -> None:
    """
    Sends user information in response to the /information command.

    :param message: Message object.
    :param manager: Manager object.
    :param redis: RedisStorage object.
    :return: None
    """
    user_data = await redis.get_by_message_thread_id(message.message_thread_id)
    if not user_data:
        return None  # noqa

    text = manager.text_message.get("user_information")
    # Reply with formatted user information
    await message.reply(text.format_map(user_data.to_dict()))
    # await Window.menu_of_user(manager, message, redis)
    await message.delete()


@router.message(Command(commands=["ban"]))
async def handler(message: Message, manager: Manager, redis: RedisStorage) -> None:
    """
    Toggles the ban status for a user in the group.
    If the user is banned, they will be unbanned, and vice versa.

    :param message: Message object.
    :param manager: Manager object.
    :param redis: RedisStorage object.
    :return: None
    """
    user_data = await redis.get_by_message_thread_id(message.message_thread_id)
    if not user_data:
        return None  # noqa

    url = (
        f"https://t.me/{message.from_user.username}"
        if message.from_user.username != "-"
        else f"tg://user?id={message.from_user.id}"
    )

    if user_data.is_banned:
        user_data.is_banned = False
        text = manager.text_message.get("user_unblocked")

        with suppress(IndexError, KeyError):
            text = text.format(full_name=hlink(message.from_user.full_name, url))
    else:
        user_data.is_banned = True
        text = manager.text_message.get("user_blocked")

        with suppress(IndexError, KeyError):
            text = text.format(full_name=hlink(message.from_user.full_name, url))

    # Reply with the specified text
    await message.reply(text)
    await redis.update_user(user_data.id, user_data)
    await message.delete()


@router.message(Command(commands=["close"]))
async def handler(message: Message, manager: Manager, redis: RedisStorage) -> None:
    """
    Closes the topic for a user in the group.

    :param message: Message object.
    :param manager: Manager object.
    :param redis: RedisStorage object.
    :return: None
    """
    user_data = await redis.get_by_message_thread_id(message.message_thread_id)
    if not user_data:
        return None  # noqa

    url = (
        f"https://t.me/{message.from_user.username}"
        if message.from_user.username != "-"
        else f"tg://user?id={message.from_user.id}"
    )

    topic_manager = TopicManager(manager.bot, redis, manager.config)
    await topic_manager.close_topic(message, user_data)

    text = manager.text_message.get("closed_topic")
    await message.bot.send_message(chat_id=user_data.id, text=text)

    text = manager.text_message.get("closed_topic_by")
    with suppress(IndexError, KeyError):
        text = text.format(full_name=hlink(message.from_user.full_name, url))

    await message.reply(text, disable_web_page_preview=True)
    await message.delete()


@router.message(Command(commands=["open"]))
async def open_handler(message: Message, manager: Manager, redis: RedisStorage) -> None:
    """
    Opens the topic for a user in the group.

    :param message: Message object.
    :param manager: Manager object.
    :param redis: RedisStorage object.
    :return: None
    """
    user_data = await redis.get_by_message_thread_id(message.message_thread_id)
    if not user_data:
        return None  # noqa

    url = (
        f"https://t.me/{message.from_user.username}"
        if message.from_user.username != "-"
        else f"tg://user?id={message.from_user.id}"
    )

    topic_manager = TopicManager(manager.bot, redis, manager.config)
    await topic_manager.open_topic(message, user_data)

    text = manager.text_message.get("open_topic")
    await message.bot.send_message(chat_id=user_data.id, text=text)

    text = manager.text_message.get("open_topic_by")
    with suppress(IndexError, KeyError):
        text = text.format(full_name=hlink(message.from_user.full_name, url))

    await message.reply(text, disable_web_page_preview=True)
    await message.delete()


@router.message(Command(commands=["status"]))
async def handler(message: Message, manager: Manager, redis: RedisStorage) -> None:
    """
    Sends the status of the topic for a user in the group.

    :param message: Message object.
    :param manager: Manager object.
    :param redis: RedisStorage object.
    :return: None
    """
    user_data = await redis.get_by_message_thread_id(message.message_thread_id)
    if not user_data:
        return None  # noqa

    await message.reply(f"Статус топика: <b>{user_data.topic_status}</b>")
    await message.delete()
