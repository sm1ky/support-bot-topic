from contextlib import suppress
from typing import Any, Dict, Optional
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
            logging.info(f"Изменен статус пользователя {user_data.id} с '{old_status}' на 'closed'")

            # Изменяем название топика
            try:
                await self.bot.edit_forum_topic(
                    chat_id=self.config.bot.GROUP_ID,
                    message_thread_id=user_data.message_thread_id,
                    name=new_name,
                )
                logging.info(f"Изменено название топика для {user_data.id} на '{new_name}'")
            except TelegramBadRequest as ex:
                if "TOPIC_NOT_MODIFIED" not in ex.message:
                    logging.error(f"Ошибка при изменении имени топика для {user_data.id}: {ex}")
            
            # Закрываем топик
            try:
                await self.bot.close_forum_topic(
                    chat_id=self.config.bot.GROUP_ID,
                    message_thread_id=user_data.message_thread_id
                )
                logging.info(f"Закрыт топик для {user_data.id}")
            except TelegramBadRequest as ex:
                if "TOPIC_NOT_MODIFIED" not in ex.message and "TOPIC_CLOSED" not in ex.message:
                    logging.error(f"Ошибка при закрытии топика для {user_data.id}: {ex}")
                    
        except Exception as e:
            logging.error(f"Неожиданная ошибка при закрытии топика для пользователя {user_data.id}: {e}")
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
            logging.info(f"Изменен статус пользователя {user_data.id} с '{old_status}' на 'open'")

            # Изменяем название топика
            try:
                await self.bot.edit_forum_topic(
                    chat_id=self.config.bot.GROUP_ID,
                    message_thread_id=user_data.message_thread_id,
                    name=new_name,
                )
                logging.info(f"Изменено название топика для {user_data.id} на '{new_name}'")
            except TelegramBadRequest as ex:
                if "TOPIC_NOT_MODIFIED" not in ex.message:
                    logging.error(f"Ошибка при изменении имени топика для {user_data.id}: {ex}")
            
            # Открываем топик
            try:
                await self.bot.reopen_forum_topic(
                    chat_id=self.config.bot.GROUP_ID,
                    message_thread_id=user_data.message_thread_id
                )
                logging.info(f"Открыт топик для {user_data.id}")
            except TelegramBadRequest as ex:
                if "TOPIC_NOT_MODIFIED" not in ex.message:
                    logging.error(f"Ошибка при открытии топика для {user_data.id}: {ex}")
        
        except Exception as e:
            logging.error(f"Неожиданная ошибка при открытии топика для пользователя {user_data.id}: {e}")
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
            logging.info(f"Изменен статус пользователя {user_data.id} с '{old_status}' на 'new'")

            # Изменяем название топика
            try:
                await self.bot.edit_forum_topic(
                    chat_id=self.config.bot.GROUP_ID,
                    message_thread_id=user_data.message_thread_id,
                    name=new_name,
                )
                logging.info(f"Изменено название топика для {user_data.id} на '{new_name}'")
            except TelegramBadRequest as ex:
                if "TOPIC_NOT_MODIFIED" not in ex.message:
                    logging.error(f"Ошибка при изменении имени топика для {user_data.id}: {ex}")
            
            # Убедимся, что топик открыт (не закрыт)
            try:
                await self.bot.reopen_forum_topic(
                    chat_id=self.config.bot.GROUP_ID,
                    message_thread_id=user_data.message_thread_id
                )
                logging.info(f"Открыт топик (new) для {user_data.id}")
            except TelegramBadRequest as ex:
                if "TOPIC_NOT_MODIFIED" not in ex.message:
                    logging.error(f"Ошибка при открытии топика (new) для {user_data.id}: {ex}")
        
        except Exception as e:
            logging.error(f"Неожиданная ошибка при создании нового топика для пользователя {user_data.id}: {e}")
            raise  # Пробрасываем ошибку для обработки в вызывающем коде