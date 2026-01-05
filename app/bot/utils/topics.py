from contextlib import suppress
from datetime import datetime, timedelta, timezone
import json
from typing import Any, Dict, List, Optional, Tuple
import logging

from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import Message

from app.bot.utils.redis import RedisStorage
from app.bot.utils.redis.models import UserData


class TopicManager:
    """
    Класс для управления топиками.
    """

    def __init__(self, bot: Bot, redis: RedisStorage, config: Any) -> None:
        """
        Инициализация TopicManager.

        :param bot: Объект бота.
        :param redis: RedisStorage.
        :param config: Конфигурация бота.
        """
        self.bot = bot
        self.redis = redis
        self.config = config

    async def close_topic(self, message: Message, user_data: UserData) -> None:
        """
        Закрывает топик.

        :param message: Объект сообщения.
        :param user_data: Данные пользователя.
        :return: None
        """
        try:
            new_name = f"⭕️ {user_data.full_name}"

            # Обновляем статус в Redis
            old_status = user_data.topic_status
            user_data.topic_status = "closed"
            await self.redis.update_user(user_data.id, user_data)
            logging.info(
                f"Изменен статус пользователя {user_data.id} с '{old_status}' на 'closed'"
            )

            # Изменяем название топика
            try:
                await self.bot.edit_forum_topic(
                    chat_id=self.config.bot.GROUP_ID,
                    message_thread_id=user_data.message_thread_id,
                    name=new_name,
                )
                logging.info(
                    f"Изменено название топика для {user_data.id} на '{new_name}'"
                )
            except TelegramBadRequest as ex:
                if "TOPIC_NOT_MODIFIED" not in ex.message:
                    logging.error(
                        f"Ошибка при изменении имени топика для {user_data.id}: {ex}"
                    )

            # Закрываем топик
            try:
                await self.bot.close_forum_topic(
                    chat_id=self.config.bot.GROUP_ID,
                    message_thread_id=user_data.message_thread_id,
                )
                logging.info(f"Закрыт топик для {user_data.id}")
            except TelegramBadRequest as ex:
                if (
                    "TOPIC_NOT_MODIFIED" not in ex.message
                    and "TOPIC_CLOSED" not in ex.message
                ):
                    logging.error(
                        f"Ошибка при закрытии топика для {user_data.id}: {ex}"
                    )

        except Exception as e:
            logging.error(
                f"Неожиданная ошибка при закрытии топика для пользователя {user_data.id}: {e}"
            )
            raise  # Пробрасываем ошибку для обработки в вызывающем коде

    async def open_topic(self, message: Message, user_data: UserData) -> None:
        """
        Открывает топик.

        :param message: Объект сообщения.
        :param user_data: Данные пользователя.
        :return: None
        """
        try:
            new_name = f"🟢 {user_data.full_name}"

            # Обновляем статус в Redis
            old_status = user_data.topic_status
            user_data.topic_status = "open"
            await self.redis.update_user(user_data.id, user_data)
            logging.info(
                f"Изменен статус пользователя {user_data.id} с '{old_status}' на 'open'"
            )

            # Изменяем название топика
            try:
                await self.bot.edit_forum_topic(
                    chat_id=self.config.bot.GROUP_ID,
                    message_thread_id=user_data.message_thread_id,
                    name=new_name,
                )
                logging.info(
                    f"Изменено название топика для {user_data.id} на '{new_name}'"
                )
            except TelegramBadRequest as ex:
                if "TOPIC_NOT_MODIFIED" not in ex.message:
                    logging.error(
                        f"Ошибка при изменении имени топика для {user_data.id}: {ex}"
                    )

            # Открываем топик
            try:
                await self.bot.reopen_forum_topic(
                    chat_id=self.config.bot.GROUP_ID,
                    message_thread_id=user_data.message_thread_id,
                )
                logging.info(f"Открыт топик для {user_data.id}")
            except TelegramBadRequest as ex:
                if "TOPIC_NOT_MODIFIED" not in ex.message:
                    logging.error(
                        f"Ошибка при открытии топика для {user_data.id}: {ex}"
                    )

        except Exception as e:
            logging.error(
                f"Неожиданная ошибка при открытии топика для пользователя {user_data.id}: {e}"
            )
            raise  # Пробрасываем ошибку для обработки в вызывающем коде

    async def new_topic(self, message: Message, user_data: UserData) -> None:
        """
        Новый топик.

        :param message: Объект сообщения.
        :param user_data: Данные пользователя.
        :return: None
        """
        try:
            new_name = f"🆕 {user_data.full_name}"

            # Обновляем статус в Redis
            old_status = user_data.topic_status
            user_data.topic_status = "new"
            await self.redis.update_user(user_data.id, user_data)
            logging.info(
                f"Изменен статус пользователя {user_data.id} с '{old_status}' на 'new'"
            )

            # Изменяем название топика
            try:
                await self.bot.edit_forum_topic(
                    chat_id=self.config.bot.GROUP_ID,
                    message_thread_id=user_data.message_thread_id,
                    name=new_name,
                )
                logging.info(
                    f"Изменено название топика для {user_data.id} на '{new_name}'"
                )
            except TelegramBadRequest as ex:
                if "TOPIC_NOT_MODIFIED" not in ex.message:
                    logging.error(
                        f"Ошибка при изменении имени топика для {user_data.id}: {ex}"
                    )

            # Убедимся, что топик открыт (не закрыт)
            try:
                await self.bot.reopen_forum_topic(
                    chat_id=self.config.bot.GROUP_ID,
                    message_thread_id=user_data.message_thread_id,
                )
                logging.info(f"Открыт топик (new) для {user_data.id}")
            except TelegramBadRequest as ex:
                if "TOPIC_NOT_MODIFIED" not in ex.message:
                    logging.error(
                        f"Ошибка при открытии топика (new) для {user_data.id}: {ex}"
                    )

        except Exception as e:
            logging.error(
                f"Неожиданная ошибка при создании нового топика для пользователя {user_data.id}: {e}"
            )
            raise  # Пробрасываем ошибку для обработки в вызывающем коде

    async def is_topic_closed(self, chat_id: int, message_thread_id: int) -> bool:
        """
        Проверяет, закрыт ли топик.

        :param chat_id: ID чата.
        :param message_thread_id: ID топика.
        :return: True если топик закрыт, False если открыт.
        """
        key = f"topic_status:{chat_id}:{message_thread_id}"
        status = await self.redis.redis.get(key)
        return status == b"closed"

    @staticmethod
    async def get_question_position(redis_storage: RedisStorage, user_id: int) -> int:
        """
        Возвращает порядковый номер пользователя в очереди на обработку.

        В очередь включаются только записи, находящиеся в состоянии "new".
        Позиция рассчитывается по времени появления топика (FIFO).

        Args:
            user_id: ID пользователя.

        Returns:
            Позиция пользователя (от 1 и выше). Если пользователь в очереди отсутствует — 0.
        """

        def parse_datetime(value: str) -> datetime:
            """
            Универсальный разбор строки даты (приведён к минимальному читабельному формату).
            """
            try:
                try:
                    return datetime.strptime(value, "%Y-%m-%d %H:%M:%S%z")
                except Exception:
                    pass

                if "UTC+" in value:
                    base, tz = value.rsplit(" UTC+", 1)
                    base_dt = datetime.strptime(base, "%Y-%m-%d %H:%M:%S")
                    offset = int(tz.split(":")[0])
                    return base_dt.replace(tzinfo=timezone(timedelta(hours=offset)))

                return datetime.strptime(value, "%Y-%m-%d %H:%M:%S")

            except Exception as exc:
                logging.error("Failed to parse datetime '%s': %s", value, exc)
                raise

        try:
            user_ids = await redis_storage.get_all_users_ids()
            raw_map: dict[bytes, bytes] = await redis_storage.redis.hgetall(
                redis_storage.NAME
            )
        except Exception as exc:
            logging.error(
                "Не удалось получить данные Redis для расчёта позиции очереди",
                exc_info=True,
            )
            return 0

        if not raw_map or not user_ids:
            return 0

        queue: List[Tuple[int, datetime]] = []

        for uid in user_ids:
            raw = raw_map.get(str(uid).encode())
            if not raw:
                continue

            try:
                data = UserData(**json.loads(raw))
            except Exception as exc:
                logging.warning("Повреждённые данные пользователя %s: %s", uid, exc)
                continue

            if data.topic_status != "new":
                continue

            ts = data.created_at
            try:
                created_at = parse_datetime(ts)
            except Exception:
                logging.debug("Невалидное время топика у %s: %s", uid, ts)
                continue

            queue.append((data.id, created_at))

        if not queue:
            return 0

        queue.sort(key=lambda item: item[1])

        for pos, (uid, _) in enumerate(queue, start=1):
            if uid == user_id:
                return pos

        return 0

    async def is_topic_open(self, chat_id: int, message_thread_id: int) -> bool:
        """
        Проверяет, открыт ли топик.

        :param chat_id: ID чата.
        :param message_thread_id: ID топика.
        :return: True если топик открыт, False если закрыт.
        """
        key = f"topic_status:{chat_id}:{message_thread_id}"
        status = await self.redis.redis.get(key)
        return status == b"open"

    async def is_topic_new(self, chat_id: int, message_thread_id: int) -> bool:
        """
        Проверяет, новый ли топик.

        :param chat_id: ID чата.
        :param message_thread_id: ID топика.
        :return: True если топик новый, False если нет.
        """
        key = f"topic_status:{chat_id}:{message_thread_id}"
        status = await self.redis.redis.get(key)
        return status == b"new"

    async def is_topic_closed(self, chat_id: int, message_thread_id: int) -> bool:
        """
        Проверяет, закрыт ли топик.

        :param chat_id: ID чата.
        :param message_thread_id: ID топика.
        :return: True если топик закрыт, False если открыт.
        """
        key = f"topic_status:{chat_id}:{message_thread_id}"
        status = await self.redis.redis.get(key)
        return status == b"closed"
