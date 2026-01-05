import asyncio
from typing import Optional

from aiogram import Router, F
from aiogram.exceptions import TelegramAPIError
from aiogram.filters import MagicData, Command
from aiogram.types import Message
from aiogram.utils.markdown import hlink

from app.bot.manager import Manager
from app.bot.types.album import Album
from app.bot.utils.redis import RedisStorage
from app.bot.utils.redis.models import UserData
from app.bot.utils.topics import TopicManager

from app.bot.handlers.group.windows import Window

router = Router()
router.message.filter(
    MagicData(F.event_chat.id == F.config.bot.GROUP_ID),  # type: ignore
    F.chat.type.in_(["group", "supergroup"]),
    F.message_thread_id.is_not(None),
)


@router.message(F.forum_topic_created)
@router.message(Command("renew"))
async def handler(message: Message, manager: Manager, redis: RedisStorage) -> None:
    await asyncio.sleep(3)
    user_data = await redis.get_by_message_thread_id(message.message_thread_id)
    if not user_data:
        return None  # noqa

    # Generate a URL for the user's profile
    url = (
        f"https://t.me/{user_data.username[1:]}"
        if user_data.username != "-"
        else f"tg://user?id={user_data.id}"
    )

    # Get the appropriate text based on the user's state
    text = manager.text_message.get("user_started_bot")

    message = await message.bot.send_message(
        chat_id=manager.config.bot.GROUP_ID,
        text=text.format(name=hlink(user_data.full_name, url)),
        message_thread_id=user_data.message_thread_id,
    )

    # await Window.menu_of_user(manager, message, redis)

    # Pin the message
    await message.pin()


@router.message(
    F.pinned_message
    | F.forum_topic_edited
    | F.forum_topic_closed
    | F.forum_topic_reopened
    | F.forum_topic
)
async def handler(message: Message) -> None:
    """
    Delete service messages such as pinned, edited, closed, or reopened forum topics.

    :param message: Message object.
    :return: None
    """
    await message.delete()


@router.message(F.media_group_id, F.from_user[F.is_bot.is_(False)])
@router.message(F.media_group_id.is_(None), F.from_user[F.is_bot.is_(False)])
async def handler(
    message: Message,
    manager: Manager,
    redis: RedisStorage,
    album: Optional[Album] = None,
) -> None:
    """
    Handles user messages and sends them to the respective user.
    If silent mode is enabled for the user, the messages are ignored.

    :param message: Message object.
    :param manager: Manager object.
    :param redis: RedisStorage object.
    :param album: Album object or None.
    :return: None
    """
    user_data: UserData | None = await redis.get_by_message_thread_id(
        message.message_thread_id
    )
    if not user_data:
        return None  # noqa

    # Проверяем, открыт ли топик
    if user_data.topic_status == "closed":
        text = manager.text_message.get("topic_closed_warning")
        msg = await message.reply(text)
        await asyncio.sleep(10)
        await msg.delete()
        return

    if user_data.message_silent_mode:
        # If silent mode is enabled, ignore all messages.
        return

    text = manager.text_message.get("message_sent_to_user")

    try:
        # Проверяем, есть ли reply на сообщение
        if message.reply_to_message:
            reply_text = (
                message.reply_to_message.text
                or message.reply_to_message.caption
                or "[медиа]"
            )
            reply_header = (
                f"<blockquote>↩️ Ответ на сообщение:\n{reply_text}</blockquote>\n\n"
            )

            # Отправляем информацию о reply пользователю
            await message.bot.send_message(
                chat_id=user_data.id, text=reply_header, parse_mode="HTML"
            )

        if not album:
            await message.copy_to(chat_id=user_data.id)
        else:
            # Копируем альбом пользователю
            msg_list = await album.copy_to(chat_id=user_data.id)

            # Собираем все подписи из альбома
            captions = []
            for idx, msg_item in enumerate(msg_list, start=1):
                if hasattr(msg_item, "caption") and msg_item.caption:
                    captions.append(f"📸 Фото {idx}: {msg_item.caption}")
                elif hasattr(msg_item, "caption"):
                    captions.append(f"📸 Фото {idx}: [без подписи]")

            # Если есть подписи, отправляем их сводкой
            if captions:
                captions_text = "\n\n".join(captions)
                await message.bot.send_message(
                    chat_id=user_data.id,
                    text=f"<b>📝 Подписи к медиа:</b>\n\n{captions_text}",
                    parse_mode="HTML",
                )

    except TelegramAPIError as ex:
        if "blocked" in ex.message:
            text = manager.text_message.get("blocked_by_user")
        else:
            text = manager.text_message.get("message_not_sent")

    except Exception:
        text = manager.text_message.get("message_not_sent")

    # Reply to the edited message with the specified text
    msg = await message.reply(text)
    # Wait for 5 seconds before deleting the reply
    await asyncio.sleep(5)
    # Delete the reply to the edited message
    await msg.delete()
