from datetime import datetime, timedelta, timezone
from redis import asyncio as aioredis
import logging
import json
from typing import List
from aiogram import Bot
from aiogram.exceptions import TelegramAPIError
from app.bot.utils.redis import RedisStorage, UserData
from app.bot.utils.texts import TextMessage
from app.config import Config

logger = logging.getLogger(__name__)
INACTIVITY_HOURS = 6


async def close_inactive_topics(bot: Bot, config: Config) -> None:
    """
    Автоматически закрывает топики, которые неактивны более 6 часов.
    Топик считается неактивным если:
    - Последнее сообщение от поддержки было более 6 часов назад
    - ИЛИ не было сообщений от пользователя более 6 часов назад

    Args:
        bot: Экземпляр бота для управления топиками.
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

            closed_count = 0
            now = datetime.now(timezone.utc)
            inactivity_threshold = now - timedelta(hours=INACTIVITY_HOURS)

            for user_id in user_ids:
                user_data_json = users_data.get(str(user_id).encode())
                if not user_data_json:
                    continue

                user_data = UserData(**json.loads(user_data_json))

                # Пропускаем если топик уже закрыт или не создан
                if (
                    user_data.topic_status == "closed"
                    or user_data.message_thread_id is None
                ):
                    continue

                # Проверяем дату последнего сообщения
                last_message_date = user_data.last_message_date

                if last_message_date and last_message_date < inactivity_threshold:
                    try:
                        # Создаем экземпляр TextMessage для языка пользователя
                        text_message = TextMessage(user_data.language_code)

                        # Закрываем топик
                        await bot.close_forum_topic(
                            chat_id=GROUP_CHAT_ID,
                            message_thread_id=user_data.message_thread_id,
                        )

                        # Отправляем уведомление в топик
                        await bot.send_message(
                            chat_id=GROUP_CHAT_ID,
                            message_thread_id=user_data.message_thread_id,
                            text=(
                                f"🔒 <b>Топик автоматически закрыт</b>\n\n"
                                f"Причина: отсутствие активности более {INACTIVITY_HOURS} часов\n"
                                f"Последнее сообщение: {last_message_date.strftime('%d.%m.%Y %H:%M UTC')}"
                            ),
                            parse_mode="HTML",
                        )

                        # Обновляем статус в Redis
                        user_data.topic_status = "closed"
                        await redis.update_user(user_id, user_data)

                        closed_count += 1
                        logger.info(
                            f"Закрыт топик для пользователя {user_data.full_name} "
                            f"(ID: {user_id}, Thread: {user_data.message_thread_id})"
                        )

                        # Уведомляем пользователя на его языке
                        try:
                            await bot.send_message(
                                chat_id=user_id,
                                text=text_message.get("closed_topic"),
                                parse_mode="HTML",
                            )
                        except TelegramAPIError as e:
                            logger.warning(
                                f"Не удалось отправить уведомление пользователю {user_id}: {e}"
                            )

                    except TelegramAPIError as e:
                        logger.error(
                            f"Ошибка при закрытии топика {user_data.message_thread_id}: {e}"
                        )
                    except Exception as e:
                        logger.error(
                            f"Неожиданная ошибка при обработке топика {user_data.message_thread_id}: {e}",
                            exc_info=True,
                        )

            if closed_count > 0:
                logger.info(f"Автоматически закрыто топиков: {closed_count}")

                # Отправляем сводку в общий чат
                await bot.send_message(
                    chat_id=GROUP_CHAT_ID,
                    text=(
                        f"🔒 <b>Автоматическое закрытие топиков</b>\n\n"
                        f"Закрыто неактивных топиков: <b>{closed_count}</b>\n"
                        f"Порог неактивности: {INACTIVITY_HOURS} часов"
                    ),
                    parse_mode="HTML",
                )
            else:
                logger.info("Нет неактивных топиков для закрытия")

    except Exception as e:
        logger.error(f"Ошибка в close_inactive_topics: {e}", exc_info=True)
        raise
