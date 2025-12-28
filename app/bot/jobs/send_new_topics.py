from datetime import datetime, timedelta, timezone
from redis import asyncio as aioredis
import logging
import json
from typing import List, Tuple
from aiogram import Bot
from app.bot.utils.redis import RedisStorage, UserData
from app.config import Config


logger = logging.getLogger(__name__)
THREAD_LINK_TEMPLATE = "https://t.me/c/{chat_id}/{thread_id}"


async def send_new_topics(bot: Bot, config: Config) -> None:
    """Отправляет сводку новых топиков в указанную группу.

    Args:
        bot: Экземпляр бота для отправки сообщений.
        config: Конфигурация бота с GROUP_ID и Redis DSN.
    """
    GROUP_CHAT_ID = config.bot.GROUP_ID
    LINK_CHAT_ID = str(GROUP_CHAT_ID)[4:]

    try:
        async with aioredis.from_url(config.redis.dsn()) as redis_client:
            redis = RedisStorage(redis_client)
            user_ids = await redis.get_all_users_ids()
            users_data = await redis.redis.hgetall(redis.NAME)

            if not users_data:
                logger.info("Нет данных о пользователях в Redis")
                return

            new_threads: List[str] = []

            for user_id in user_ids:
                user_data_json = users_data.get(str(user_id).encode())
                if user_data_json:
                    user_data = UserData(**json.loads(user_data_json))
                    if (
                        user_data.topic_status == "new"
                        and user_data.message_thread_id is not None
                    ):
                        thread_link = THREAD_LINK_TEMPLATE.format(
                            chat_id=LINK_CHAT_ID, thread_id=user_data.message_thread_id
                        )
                        new_threads.append(
                            f'<a href="{thread_link}">{user_data.full_name}</a>'
                        )

            if new_threads:
                message = (
                    "📢 <b>Сводка новых топиков, требующих ответа</b>:\n\n"
                    "{threads}\n\n"
                    "<b>Всего новых топиков: {count}</b>"
                ).format(
                    threads="\n".join(f"- {link}" for link in new_threads),
                    count=len(new_threads),
                )
                await bot.send_message(
                    chat_id=GROUP_CHAT_ID, text=message, parse_mode="HTML"
                )
            else:
                logger.info("Нет топиков для сводки")
    except Exception as e:
        logger.error(f"Ошибка в send_new_topics: {e}", exc_info=True)
        raise
