from contextlib import suppress
from aiogram import Router, F
from aiogram.filters import MagicData
from aiogram.types import CallbackQuery
from aiogram.utils.markdown import hcode, hlink

from app.bot.manager import Manager
from app.bot.utils.redis import RedisStorage
from app.bot.utils.redis.models import UserData

from app.bot.utils.topics import TopicManager


router = Router()
router.message.filter(
    F.chat.type.in_(["group", "supergroup"]),
)


@router.callback_query(F.data == "apply_appeal")
async def handler(call: CallbackQuery, manager: Manager, redis: RedisStorage) -> None:
    """
    Handles callback queries for apply appeal

    :param call: CallbackQuery object.
    :param manager: Manager object.
    :param redis: RedisStorage object.
    :return: None
    """

    user_data = await redis.get_by_message_thread_id(call.message.message_thread_id)
    if not user_data: return None  # noqa

    if user_data.topic_status == "open":
        await manager.show_alert(callback=call, text="✅ Обращение уже в работе", show_alert=True)
        await call.answer()
        return


    url = f"https://t.me/{call.from_user.username}" if call.from_user.username != "-" else f"tg://user?id={call.from_user.id}"

    topic_manager = TopicManager(manager.bot, redis, manager.config)
    await topic_manager.open_topic(call.message, user_data)

    text = manager.text_message.get("open_topic")
    await call.message.bot.send_message(chat_id=user_data.id, text=text)

    text = manager.text_message.get("open_topic_by")
    with suppress(IndexError, KeyError):
            text = text.format(full_name=hlink(call.from_user.full_name, url))

    await call.message.bot.send_message(
        chat_id=call.message.chat.id,
        message_thread_id=call.message.message_thread_id,
        text=text
    )
    await manager.show_alert(callback=call, text="✅ Обращение в работе", show_alert=True)
    await call.answer()



@router.callback_query(F.data == "close_appeal")
async def handler(call: CallbackQuery, manager: Manager, redis: RedisStorage) -> None:
    """
    Handles callback queries for apply appeal

    :param call: CallbackQuery object.
    :param manager: Manager object.
    :param redis: RedisStorage object.
    :return: None
    """

    user_data = await redis.get_by_message_thread_id(call.message.message_thread_id)
    if not user_data: return None  # noqa

    if user_data.topic_status == "closed":
        await manager.show_alert(callback=call, text="⭕️ Обращение уже закрыто!", show_alert=True)
        await call.answer()
        return


    url = f"https://t.me/{call.from_user.username}" if call.from_user.username != "-" else f"tg://user?id={call.from_user.id}"

    topic_manager = TopicManager(manager.bot, redis, manager.config)
    await topic_manager.close_topic(call.message, user_data)  # Исправлено: открытие -> закрытие

    text = manager.text_message.get("close_topic")
    await call.message.bot.send_message(chat_id=user_data.id, text=text)

    text = manager.text_message.get("close_topic_by")
    with suppress(IndexError, KeyError):
            text = text.format(full_name=hlink(call.from_user.full_name, url))

    await call.message.bot.send_message(
        chat_id=call.message.chat.id,
        message_thread_id=call.message.message_thread_id,
        text=text
    )
    await manager.show_alert(callback=call, text="✅ Обращение закрыто!", show_alert=True)
    await call.answer()