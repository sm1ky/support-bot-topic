import aioredis
import asyncio
import logging
import json
from typing import List
from aiogram import Bot
from app.bot.utils.redis import RedisStorage, UserData
from app.config import Config
from datetime import datetime, timezone, timedelta

logger = logging.getLogger(__name__)

async def bump_topic(bot: Bot, config: Config) -> None:
    """Отправляет сообщение 'BUMP' в топики пользователей с topic_status 'new' или 'open',
    если с последнего сообщения прошло более 2 часов.

    Args:
        bot: Экземпляр бота для отправки сообщений.
        config: Конфигурация бота с GROUP_ID и Redis DSN.
    """
    GROUP_CHAT_ID = config.bot.GROUP_ID

    try:
        async with aioredis.from_url(config.redis.dsn()) as redis_client:
            redis = RedisStorage(redis_client)
            user_ids = await redis.get_all_users_ids()
            users_data = await redis.redis.hgetall(redis.NAME)

            if not users_data:
                logger.info("Нет данных о пользователях в Redis")
                return

            current_time = datetime.now(timezone(timedelta(hours=3)))

            for user_id in user_ids:
                user_data_json = users_data.get(str(user_id).encode())
                if user_data_json:
                    user_data = UserData(**json.loads(user_data_json))
                    if user_data.topic_status in ("new", "open") and user_data.message_thread_id is not None:
                        if user_data.last_message_date:
                            try:
                                last_message_time = datetime.strptime(user_data.last_message_date, "%Y-%m-%d %H:%M:%S%z")
                                time_difference = current_time - last_message_time
                                if time_difference > timedelta(minutes=5):
                                    try:
                                        await bot.send_message(
                                            chat_id=GROUP_CHAT_ID,
                                            text="🆙 <b>BUMP</b> 🆙",
                                            message_thread_id=user_data.message_thread_id,
                                            parse_mode="HTML"
                                        )
                                        logger.info(f"Отправлен BUMP в thread_id={user_data.message_thread_id} для user_id={user_id}")
                                        await asyncio.sleep(0.5)
                                    except Exception as e:
                                        logger.error(f"Ошибка при отправке BUMP для user_id={user_id}: {e}", exc_info=True)
                                else:
                                    logger.info(f"Не прошло 2 часа с последнего сообщения для user_id={user_id}")
                            except ValueError as e:
                                logger.error(f"Ошибка парсинга last_message_date для user_id={user_id}: {e}")
                        else:
                            logger.info(f"last_message_date не установлена для user_id={user_id}, пропускаем")

            logger.info("Задача bump_topic выполнена")
    except Exception as e:
        logger.error(f"Ошибка в bump_topic: {e}", exc_info=True)
        raise