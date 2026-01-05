# app/bot/utils/texts.py
from abc import abstractmethod, ABCMeta

# Add other languages and their corresponding codes as needed.
# You can also keep only one language by removing the line with the unwanted language.
SUPPORTED_LANGUAGES = {
    "ru": "🇷🇺 Русский",
    "en": "🇺🇸 English",
}


class Text(metaclass=ABCMeta):
    """
    Abstract base class for handling text data in different languages.
    """

    def __init__(self, language_code: str) -> None:
        """
        Initializes the Text instance with the specified language code.

        :param language_code: The language code (e.g., "ru" or "en").
        """
        self.language_code = (
            language_code if language_code in SUPPORTED_LANGUAGES.keys() else "ru"
        )

    @property
    @abstractmethod
    def data(self) -> dict:
        """
        Abstract property to be implemented by subclasses. Represents the language-specific text data.

        :return: Dictionary containing language-specific text data.
        """
        raise NotImplementedError

    def get(self, code: str) -> str:
        """
        Retrieves the text corresponding to the provided code in the current language.

        :param code: The code associated with the desired text.
        :return: The text in the current language.
        """
        return self.data[self.language_code][code]


class TextMessage(Text):
    """
    Subclass of Text for managing text messages in different languages.
    """

    @property
    def data(self) -> dict:
        """
        Provides language-specific text data for text messages.

        :return: Dictionary containing language-specific text data for text messages.
        """
        return {
            "ru": {
                "select_language": "👋 <b>Привет</b>, {full_name}!\n\nВыберите язык:",
                "change_language": "<b>Выберите язык:</b>",
                "main_menu": (
                    "<b>Здравствуйте, {full_name}</b>!\n\n"
                    "Добро пожаловать в бот поддержки {bot_name}\n"
                    "Здесь вы можете получить помощь, если у вас возникли вопросы или проблемы с нашим ботом.\n\n"
                    "<b>Выберите тему обращения:</b>"
                ),
                "message_sent": "<b>Сообщение отправлено!</b> Ожидайте ответа.\n\nВаша позиция в очереди: {position}",
                "message_sent_topic_open": "<b>Сообщение отправлено!</b> Наша поддержка уже работает над вашим обращением.",
                "message_edited": (
                    "<b>Сообщение отредактировано только в вашем чате.</b> "
                    "Чтобы отправить отредактированное сообщение, отправьте его как новое сообщение."
                ),
                "user_started_bot": (
                    "<b>Пользователь {name} запустил(а) бота!</b>\n\n"
                    "Список доступных команд:\n\n"
                    "• /ban\n"
                    "Заблокировать/Разблокировать пользователя"
                    "<blockquote>Заблокируйте пользователя, если не хотите получать от него сообщения.</blockquote>\n\n"
                    "• /silent\n"
                    "Активировать/Деактивировать тихий режим"
                    "<blockquote>При включенном тихом режиме сообщения не отправляются пользователю.</blockquote>\n\n"
                    "• /information\n"
                    "Информация о пользователе"
                    "<blockquote>Получить сообщение с основной информацией о пользователе.</blockquote>"
                ),
                "user_restarted_bot": "<b>Пользователь {name} перезапустил(а) бота!</b>",
                "user_stopped_bot": "<b>Пользователь {name} остановил(а) бота!</b>",
                "user_blocked": "<b>Пользователь заблокирован!</b> Сообщения от пользователя не принимаются.\nЗаблокирован {full_name}",
                "user_unblocked": "<b>Пользователь разблокирован!</b> Сообщения от пользователя вновь принимаются.\nРазблокирован {full_name}",
                "blocked_by_user": "<b>Сообщение не отправлено!</b> Бот был заблокирован пользователем.",
                "user_information": (
                    "<b>ID:</b>\n"
                    "- <code>{id}</code>\n"
                    "<b>Имя:</b>\n"
                    "- {full_name}\n"
                    "<b>Статус:</b>\n"
                    "- {state}\n"
                    "<b>Username:</b>\n"
                    "- {username}\n"
                    "<b>Заблокирован:</b>\n"
                    "- {is_banned}\n"
                    "<b>Дата регистрации:</b>\n"
                    "- {created_at}"
                ),
                "message_not_sent": "<b>Сообщение не отправлено!</b> Произошла неожиданная ошибка.",
                "message_sent_to_user": "<b>Сообщение отправлено пользователю!</b>",
                "silent_mode_enabled": (
                    "<b>Тихий режим активирован!</b> Сообщения не будут доставлены пользователю.\n"
                    "Активировано {full_name}"
                ),
                "silent_mode_disabled": (
                    "<b>Тихий режим деактивирован!</b> Пользователь будет получать все сообщения.\n"
                    "Деактивировано {full_name}"
                ),
                "other_question": "<b>Другой вопрос</b>",
                "request": "💬 <b>Оставьте свой вопрос</b>, и мы ответим вам в ближайшее время:",
                "open_topic": "<b>Ваше обращение принято в работу</b>",
                "open_topic_by": "<b>Обращение открыто {full_name}</b>",
                "closed_topic_by": "<b>Обращение закрыто {full_name}</b>",
                "closed_topic": "<b>Ваше обращение закрыто</b>\n\nЕсли у вас остались вопросы, создайте новое обращение - /start",
                "closed_topic_bulk": "<b>Ваше обращение было закрыто администратором.</b>\n\nЕсли у вас остались вопросы, создайте новое обращение - /start",
                "all_topics_closed": "<b>Все обращения были закрыты.</b>\nВсего закрыто: {count}",
                "no_open_topics": "<b>Нет открытых обращений для закрытия.</b>",
                # Новые строки для уведомлений
                "notifications_enabled": "<b>Уведомления включены!</b> Вы будете получать системные уведомления.",
                "notifications_disabled": "<b>Уведомления отключены!</b> Вы не будете получать системные уведомления.",
                "notifications_title": "<b>🔔 Уведомления</b>",
                "no_notifications": "У вас нет активных уведомлений.",
                "notification_item": "• {message}\n<i>{created_at}</i>",
                "notifications_read": "Все уведомления отмечены как прочитанными.",
                "notification_important": "❗ <b>ВАЖНО:</b> {message}",
                "notification_critical": "🚨 <b>КРИТИЧНО:</b> {message}",
                "notification_normal": "ℹ️ {message}",
                "add_notification_success": "Уведомление успешно добавлено!",
                "notification_settings": "<b>Настройки уведомлений</b>\n\nТекущий статус: {status}",
                # Новые строки для удаления уведомлений
                "notification_deleted": "Уведомление успешно удалено!",
                "all_notifications_cleared": "Все уведомления успешно удалены!",
                "confirm_delete_notification": "Вы уверены, что хотите удалить это уведомление?",
                "confirm_clear_all_notifications": "Вы уверены, что хотите удалить ВСЕ уведомления?",
                "delete_notification_title": "Удаление уведомления",
                "clear_all_notifications_title": "Очистка всех уведомлений",
                "topic_closed_warning": "⚠️ Топик закрыт! Откройте топик, чтобы отправлять сообщения пользователю.",
            },
            "en": {
                "select_language": "👋 <b>Hello</b>, {full_name}!\n\nSelect a language:",
                "change_language": "<b>Select a language:</b>",
                "main_menu": (
                    "<b>Hello, {full_name}</b>!\n\n"
                    "Welcome to the {bot_name} support bot.\n"
                    "Here you can get assistance if you have questions or issues with our bot.\n\n"
                    "<b>Select a topic:</b>"
                ),
                "message_sent": "<b>Message sent!</b> Please wait for a reply.\n\nYour position in the queue: {position}",
                "message_sent_topic_open": "<b>Message sent!</b> Our support team is already working on your request.",
                "message_edited": (
                    "<b>The message has been edited only in your chat.</b> "
                    "To send the edited message, send it as a new message."
                ),
                "user_started_bot": (
                    "<b>User {name} started the bot!</b>\n\n"
                    "Available commands:\n\n"
                    "• /ban\n"
                    "Block/Unblock a user"
                    "<blockquote>Block a user if you do not want to receive messages from them.</blockquote>\n\n"
                    "• /silent\n"
                    "Enable/Disable silent mode"
                    "<blockquote>When silent mode is enabled, messages are not sent to the user.</blockquote>\n\n"
                    "• /information\n"
                    "User information"
                    "<blockquote>Receive a message with basic information about the user.</blockquote>"
                ),
                "user_restarted_bot": "<b>User {name} restarted the bot!</b>",
                "user_stopped_bot": "<b>User {name} stopped the bot!</b>",
                "user_blocked": "<b>User blocked!</b> User messages will not be received.\nBlocked: {full_name}",
                "user_unblocked": "<b>User unblocked!</b> User messages will now be received.\nUnblocked: {full_name}",
                "blocked_by_user": "<b>Message not sent!</b> The bot was blocked by the user.",
                "user_information": (
                    "<b>ID:</b>\n"
                    "- <code>{id}</code>\n"
                    "<b>Name:</b>\n"
                    "- {full_name}\n"
                    "<b>Status:</b>\n"
                    "- {state}\n"
                    "<b>Username:</b>\n"
                    "- {username}\n"
                    "<b>Banned:</b>\n"
                    "- {is_banned}\n"
                    "<b>Registration date:</b>\n"
                    "- {created_at}"
                ),
                "message_not_sent": "<b>Message not sent!</b> An unexpected error occurred.",
                "message_sent_to_user": "<b>Message sent to the user!</b>",
                "silent_mode_enabled": (
                    "<b>Silent mode enabled!</b> Messages will not be delivered to the user.\n"
                    "Enabled by {full_name}"
                ),
                "silent_mode_disabled": (
                    "<b>Silent mode disabled!</b> The user will receive all messages.\n"
                    "Disabled by {full_name}"
                ),
                "other_question": "<b>Other question</b>",
                "request": "💬 <b>Leave your question</b>, and we will reply shortly:",
                "open_topic": "<b>Your request has been accepted</b>",
                "open_topic_by": "<b>Request opened by {full_name}</b>",
                "closed_topic_by": "<b>Request closed by {full_name}</b>",
                "closed_topic": "<b>Your request has been closed</b>\n\nIf you still have questions, create a new request - /start",
                "closed_topic_bulk": "<b>Your request was closed by an administrator.</b>\n\nIf you still have questions, create a new request - /start",
                "all_topics_closed": "<b>All requests have been closed.</b>\nTotal closed: {count}",
                "no_open_topics": "<b>No open requests to close.</b>",
                "notifications_enabled": "<b>Notifications enabled!</b> You will receive system notifications.",
                "notifications_disabled": "<b>Notifications disabled!</b> You will not receive system notifications.",
                "notifications_title": "<b>🔔 Notifications</b>",
                "no_notifications": "You have no active notifications.",
                "notification_item": "• {message}\n<i>{created_at}</i>",
                "notifications_read": "All notifications marked as read.",
                "notification_important": "❗ <b>IMPORTANT:</b> {message}",
                "notification_critical": "🚨 <b>CRITICAL:</b> {message}",
                "notification_normal": "ℹ️ {message}",
                "add_notification_success": "Notification successfully added!",
                "notification_settings": "<b>Notification settings</b>\n\nCurrent status: {status}",
                "notification_deleted": "Notification successfully deleted!",
                "all_notifications_cleared": "All notifications successfully deleted!",
                "confirm_delete_notification": "Are you sure you want to delete this notification?",
                "confirm_clear_all_notifications": "Are you sure you want to delete ALL notifications?",
                "delete_notification_title": "Delete notification",
                "clear_all_notifications_title": "Clear all notifications",
                "topic_closed_warning": "⚠️ The topic is closed! Open the topic to send messages to the user.",
            },
        }
