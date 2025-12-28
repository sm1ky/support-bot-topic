# app/bot/utils/notifications.py
import logging
import json
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional

from app.bot.utils.redis import RedisStorage
from app.bot.manager import Manager
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardButton

class NotificationManager:
    """
    Класс для управления системой уведомлений.
    """
    
    NOTIFICATIONS_KEY = "system_notifications"
    
    def __init__(self, redis: RedisStorage):
        """
        Инициализация менеджера уведомлений.
        
        :param redis: Объект RedisStorage для работы с хранилищем Redis.
        """
        self.redis = redis
    
    async def add_notification(self, message: str, importance: str = "normal", 
                              expiry_date: Optional[str] = None) -> bool:
        """
        Добавляет новое уведомление в систему.
        
        :param message: Текст уведомления.
        :param importance: Важность уведомления ('critical', 'important', 'normal').
        :param expiry_date: Дата истечения срока действия уведомления (опционально).
        :return: True если уведомление успешно добавлено, False в противном случае.
        """
        try:
            current_time = datetime.now(timezone(timedelta(hours=3)))
            notification = {
                "id": f"notif_{int(current_time.timestamp())}",
                "message": message,
                "importance": importance,
                "created_at": current_time.strftime("%Y-%m-%d %H:%M:%S%z"),
                "expiry_date": expiry_date
            }
            
            notifications = await self.get_all_notifications()
            notifications.append(notification)
            
            # Сохраняем обновленный список уведомлений
            await self._save_notifications(notifications)
            return True
        except Exception as e:
            logging.error(f"Ошибка при добавлении уведомления: {e}")
            return False
    
    async def remove_notification(self, notification_id: str) -> bool:
        """
        Удаляет уведомление по его ID.
        
        :param notification_id: ID уведомления для удаления.
        :return: True если уведомление успешно удалено, False в противном случае.
        """
        try:
            notifications = await self.get_all_notifications()
            notifications = [n for n in notifications if n.get("id") != notification_id]
            
            # Сохраняем обновленный список уведомлений
            await self._save_notifications(notifications)
            return True
        except Exception as e:
            logging.error(f"Ошибка при удалении уведомления: {e}")
            return False
    
    async def clear_all_notifications(self) -> bool:
        """
        Удаляет все уведомления из системы.
        
        :return: True если операция успешна, False в противном случае.
        """
        try:
            await self._save_notifications([])
            return True
        except Exception as e:
            logging.error(f"Ошибка при очистке всех уведомлений: {e}")
            return False
    
    async def get_all_notifications(self) -> List[Dict[str, Any]]:
        """
        Получает все активные уведомления.
        
        :return: Список всех активных уведомлений.
        """
        try:
            # Получаем данные из Redis
            notifications_data = await self.redis.redis.get(self.NOTIFICATIONS_KEY)
            if notifications_data:
                notifications = json.loads(notifications_data)
                
                # Фильтрация по сроку действия
                current_time = datetime.now(timezone(timedelta(hours=3)))
                active_notifications = []
                
                for notification in notifications:
                    # Проверяем срок действия уведомления
                    if notification.get("expiry_date"):
                        expiry_date = datetime.strptime(notification["expiry_date"], "%Y-%m-%d %H:%M:%S%z")
                        if expiry_date < current_time:
                            continue
                    
                    active_notifications.append(notification)
                
                return active_notifications
            return []
        except Exception as e:
            logging.error(f"Ошибка при получении уведомлений: {e}")
            return []
    
    async def get_important_notifications(self) -> List[Dict[str, Any]]:
        """
        Получает только важные уведомления ('critical', 'important').
        
        :return: Список важных уведомлений.
        """
        notifications = await self.get_all_notifications()
        return [n for n in notifications if n.get("importance") in ("critical", "important")]
    
    async def _save_notifications(self, notifications: List[Dict[str, Any]]) -> None:
        """
        Сохраняет список уведомлений в Redis.
        
        :param notifications: Список уведомлений для сохранения.
        """
        try:
            notifications_json = json.dumps(notifications)
            await self.redis.redis.set(self.NOTIFICATIONS_KEY, notifications_json)
        except Exception as e:
            logging.error(f"Ошибка при сохранении уведомлений: {e}")
            
    async def mark_notifications_read(self, user_id: int) -> bool:
        """
        Отмечает все уведомления как прочитанные для пользователя.
        
        :param user_id: ID пользователя.
        :return: True в случае успеха, False в противном случае.
        """
        try:
            user_data = await self.redis.get_user(user_id)
            if user_data:
                current_time = datetime.now(timezone(timedelta(hours=3))).strftime("%Y-%m-%d %H:%M:%S%z")
                user_data.last_notification_read = current_time
                await self.redis.update_user(user_id, user_data)
                return True
            return False
        except Exception as e:
            logging.error(f"Ошибка при отметке уведомлений как прочитанных: {e}")
            return False
    
    async def has_unread_notifications(self, user_id: int) -> bool:
        """
        Проверяет, есть ли у пользователя непрочитанные уведомления.
        
        :param user_id: ID пользователя.
        :return: True если есть непрочитанные уведомления, False в противном случае.
        """
        try:
            user_data = await self.redis.get_user(user_id)
            if not user_data or not user_data.notifications_enabled:
                return False
                
            # Получаем все уведомления
            notifications = await self.get_all_notifications()
            if not notifications:
                return False
                
            # Если пользователь никогда не читал уведомления
            if not user_data.last_notification_read:
                return bool(notifications)
                
            # Проверяем, есть ли новые уведомления после последнего прочтения
            last_read = datetime.strptime(user_data.last_notification_read, "%Y-%m-%d %H:%M:%S%z")
            for notification in notifications:
                created_at = datetime.strptime(notification["created_at"], "%Y-%m-%d %H:%M:%S%z")
                if created_at > last_read:
                    return True
                    
            return False
        except Exception as e:
            logging.error(f"Ошибка при проверке непрочитанных уведомлений: {e}")
            return False

    async def show_important_notifications_with_confirmation(self, manager: Manager, user_id: int) -> bool:
        """
        Показывает важные уведомления и ждет подтверждения пользователя.
        
        :param manager: Manager object для отправки сообщений.
        :param user_id: ID пользователя.
        :return: True если есть уведомления, False если нет.
        """
        try:
            # Получаем данные пользователя
            user_data = await self.redis.get_user(user_id)
            if not user_data or not user_data.notifications_enabled:
                return False
                
            # Получаем важные уведомления
            important_notifications = await self.get_important_notifications()
            if not important_notifications:
                return False
                
            # Проверяем, есть ли непрочитанные уведомления
            has_unread = False
            last_read_time = None
            
            if user_data.last_notification_read:
                last_read_time = datetime.strptime(user_data.last_notification_read, "%Y-%m-%d %H:%M:%S%z")
                
            # Формируем текст уведомлений
            notification_text = manager.text_message.get("notifications_title") + "\n\n"
            
            for notification in important_notifications:
                if notification["importance"] == "critical":
                    notification_item = manager.text_message.get("notification_critical").format(
                        message=notification["message"]
                    )
                elif notification["importance"] == "important":
                    notification_item = manager.text_message.get("notification_important").format(
                        message=notification["message"]
                    )
                else:
                    continue  # Пропускаем обычные уведомления
                    
                created_at = datetime.strptime(notification["created_at"], "%Y-%m-%d %H:%M:%S%z")
                notification_text += notification_item + "\n<i>" + notification["created_at"] + "</i>\n\n"
                
                # Проверяем, прочитано ли уведомление
                if not last_read_time or created_at > last_read_time:
                    has_unread = True
                    
            # Если нет непрочитанных уведомлений, возвращаем False
            if not has_unread:
                return False
                
            # Создаем клавиатуру с кнопкой подтверждения
            builder = InlineKeyboardBuilder()
            builder.row(
                InlineKeyboardButton(text="✅ Понятно", callback_data="confirm_notifications")
            )
            
            # Отправляем сообщение с уведомлениями и кнопкой
            await manager.send_message(notification_text, reply_markup=builder.as_markup())
            return True
        except Exception as e:
            logging.error(f"Ошибка при отображении уведомлений с подтверждением: {e}")
            return False