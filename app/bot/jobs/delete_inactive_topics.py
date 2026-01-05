from datetime import datetime, timedelta, timezone
from redis import asyncio as aioredis
import logging
import json
from aiogram import Bot
from aiogram.exceptions import TelegramAPIError
from app.bot.utils.redis import RedisStorage, UserData
from app.config import Config

logger = logging.getLogger(__name__)

DELETE_INACTIVE_DAYS = 7


async def delete_inactive_topics(bot: Bot, config: Config) -> None:
    """
    Автоматически удаляет топики, которые неактивны более 7 дней.

    Args:
        bot: Экземпляр бота для управления топиками.
        config: Конфигурация бота с GROUP_ID и Redis DSN.
    """
    GROUP_CHAT_ID = config.bot.GROUP_ID

    def parse_datetime(value: str) -> datetime:
        """
        Универсальный разбор строки даты.
        """
        try:
            # Попытка разбора с timezone
            try:
                return datetime.strptime(value, "%Y-%m-%d %H:%M:%S%z")
            except ValueError:
                pass

            # Попытка разбора с UTC+
            if "UTC+" in value:
                base, tz = value.rsplit(" UTC+", 1)
                base_dt = datetime.strptime(base, "%Y-%m-%d %H:%M:%S")
                offset = int(tz.split(":")[0])
                return base_dt.replace(tzinfo=timezone(timedelta(hours=offset)))

            # Попытка разбора без timezone (добавляем UTC)
            return datetime.strptime(value, "%Y-%m-%d %H:%M:%S").replace(
                tzinfo=timezone.utc
            )

        except Exception as exc:
            logger.error(f"Failed to parse datetime '{value}': {exc}")
            raise

    try:
        async with aioredis.from_url(config.redis.dsn()) as redis_client:
            redis = RedisStorage(redis_client)
            user_ids = await redis.get_all_users_ids()
            users_data = await redis.redis.hgetall(redis.NAME)

            if not users_data:
                logger.info("Нет данных о пользователях в Redis")
                return

            deleted_count = 0
            now = datetime.now(timezone.utc)
            deletion_threshold = now - timedelta(days=DELETE_INACTIVE_DAYS)

            for user_id in user_ids:
                user_data_json = users_data.get(str(user_id).encode())
                if not user_data_json:
                    continue

                user_data = UserData(**json.loads(user_data_json))

                # Пропускаем если топик не создан
                if user_data.message_thread_id is None:
                    continue

                # Проверяем дату последнего сообщения
                last_message_date_str = user_data.last_message_date

                if not last_message_date_str:
                    continue

                try:
                    last_message_date = parse_datetime(last_message_date_str)
                except Exception as e:
                    logger.warning(
                        f"Не удалось распарсить дату для пользователя {user_id}: {last_message_date_str}"
                    )
                    continue

                # Удаляем только если прошло больше 7 дней
                if last_message_date < deletion_threshold:
                    try:
                        # Удаляем топик
                        await bot.delete_forum_topic(
                            chat_id=GROUP_CHAT_ID,
                            message_thread_id=user_data.message_thread_id,
                        )

                        # Очищаем данные топика в Redis
                        user_data.message_thread_id = None
                        user_data.topic_status = "closed"
                        await redis.update_user(user_id, user_data)

                        deleted_count += 1
                        logger.info(
                            f"Удалён топик для пользователя {user_data.full_name} "
                            f"(ID: {user_id}, неактивен с {last_message_date.strftime('%d.%m.%Y %H:%M')})"
                        )

                    except TelegramAPIError as e:
                        if "message thread not found" in str(e).lower():
                            # Топик уже удалён, обновляем данные
                            user_data.message_thread_id = None
                            user_data.topic_status = "closed"
                            await redis.update_user(user_id, user_data)
                            logger.info(f"Топик уже удалён для пользователя {user_id}")
                        else:
                            logger.error(
                                f"Ошибка при удалении топика {user_data.message_thread_id}: {e}"
                            )
                    except Exception as e:
                        logger.error(
                            f"Неожиданная ошибка при удалении топика {user_data.message_thread_id}: {e}",
                            exc_info=True,
                        )

            if deleted_count > 0:
                logger.info(f"Автоматически удалено топиков: {deleted_count}")

                # Отправляем сводку в общий чат
                await bot.send_message(
                    chat_id=GROUP_CHAT_ID,
                    text=(
                        f"🗑 <b>Автоматическое удаление топиков</b>\n\n"
                        f"Удалено неактивных топиков: <b>{deleted_count}</b>\n"
                        f"Топики без активности более {DELETE_INACTIVE_DAYS} дней"
                    ),
                    parse_mode="HTML",
                )
            else:
                logger.info("Нет неактивных топиков для удаления")

    except Exception as e:
        logger.error(f"Ошибка в delete_inactive_topics: {e}", exc_info=True)
        raise
