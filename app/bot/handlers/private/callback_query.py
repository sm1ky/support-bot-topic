# app/bot/handlers/private/callback_query.py
from aiogram import Router, F
from aiogram.filters import StateFilter
from aiogram.types import CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardButton

from app.bot.handlers.private.windows import Window
from app.bot.manager import Manager
from app.bot.utils.redis import RedisStorage
from app.bot.utils.redis.models import UserData
from app.bot.utils.texts import SUPPORTED_LANGUAGES
from aiogram.fsm.context import FSMContext
from app.bot.manager import Form
from aiogram_newsletter.utils.states import ANState
from app.bot.utils.notifications import NotificationManager

router = Router()
router.callback_query.filter(F.message.chat.type == "private", ~StateFilter(ANState))


@router.callback_query(F.data == "start")
async def handler(
    call: CallbackQuery, manager: Manager, redis: RedisStorage, user_data: UserData
) -> None:
    """
    Handles callback queries for selecting the subscription

    :param call: CallbackQuery object.
    :param manager: Manager object.
    :param redis: RedisStorage object.
    :param user_data: UserData object.
    :return: None
    """

    await Window.main_menu(manager)
    await call.answer()


@router.callback_query(F.data == "notifications_settings")
async def notifications_settings_handler(
    call: CallbackQuery, manager: Manager, redis: RedisStorage, user_data: UserData
) -> None:
    """
    Обрабатывает нажатие на кнопку настроек уведомлений.

    :param call: CallbackQuery object.
    :param manager: Manager object.
    :param redis: RedisStorage object.
    :param user_data: UserData object.
    :return: None
    """
    await Window.notifications_settings(manager, redis, user_data)
    await call.answer()


@router.callback_query(F.data == "notifications_enable")
async def notifications_enable_handler(
    call: CallbackQuery, manager: Manager, redis: RedisStorage, user_data: UserData
) -> None:
    """
    Обрабатывает включение уведомлений.

    :param call: CallbackQuery object.
    :param manager: Manager object.
    :param redis: RedisStorage object.
    :param user_data: UserData object.
    :return: None
    """
    user_data.notifications_enabled = True
    await redis.update_user(user_data.id, user_data)

    # Отправляем сообщение об успехе
    await manager.send_message(manager.text_message.get("notifications_enabled"))

    # Обновляем окно настроек
    await Window.notifications_settings(manager, redis, user_data)
    await call.answer()


@router.callback_query(F.data == "notifications_disable")
async def notifications_disable_handler(
    call: CallbackQuery, manager: Manager, redis: RedisStorage, user_data: UserData
) -> None:
    """
    Обрабатывает отключение уведомлений.

    :param call: CallbackQuery object.
    :param manager: Manager object.
    :param redis: RedisStorage object.
    :param user_data: UserData object.
    :return: None
    """
    user_data.notifications_enabled = False
    await redis.update_user(user_data.id, user_data)

    # Отправляем сообщение об успехе
    await manager.send_message(manager.text_message.get("notifications_disabled"))

    # Обновляем окно настроек
    await Window.notifications_settings(manager, redis, user_data)
    await call.answer()


@router.callback_query(F.data == "notifications_read")
async def notifications_read_handler(
    call: CallbackQuery, manager: Manager, redis: RedisStorage, user_data: UserData
) -> None:
    """
    Обрабатывает отметку уведомлений как прочитанных.

    :param call: CallbackQuery object.
    :param manager: Manager object.
    :param redis: RedisStorage object.
    :param user_data: UserData object.
    :return: None
    """
    notification_manager = NotificationManager(redis)
    await notification_manager.mark_notifications_read(user_data.id)

    # Отправляем сообщение об успехе
    await manager.send_message(manager.text_message.get("notifications_read"))

    # Обновляем окно настроек
    await Window.notifications_settings(manager, redis, user_data)
    await call.answer()


@router.callback_query(F.data == "confirm_notifications")
async def confirm_notifications_handler(
    call: CallbackQuery, manager: Manager, redis: RedisStorage, user_data: UserData
) -> None:
    """
    Обрабатывает подтверждение прочтения уведомлений.

    :param call: CallbackQuery object.
    :param manager: Manager object.
    :param redis: RedisStorage object.
    :param user_data: UserData object.
    :return: None
    """
    notification_manager = NotificationManager(redis)
    await notification_manager.mark_notifications_read(user_data.id)

    # Удаляем сообщение с уведомлениями
    await call.message.delete()

    # Показываем главное меню
    await Window.main_menu(manager)
    await call.answer()


@router.callback_query(F.data.startswith("delete_notification_"))
async def delete_notification_handler(
    call: CallbackQuery, manager: Manager, redis: RedisStorage, user_data: UserData
) -> None:
    """
    Обрабатывает удаление конкретного уведомления.

    :param call: CallbackQuery object.
    :param manager: Manager object.
    :param redis: RedisStorage object.
    :param user_data: UserData object.
    :return: None
    """
    notification_id = call.data.replace("delete_notification_", "")

    # Подтверждение удаления
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="✅ Да, удалить", callback_data=f"confirm_delete_{notification_id}"
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="❌ Нет, отмена", callback_data="notifications_settings"
        )
    )

    text = manager.text_message.get("confirm_delete_notification")
    await manager.send_message(text, reply_markup=builder.as_markup())
    await call.answer()


@router.callback_query(F.data.startswith("confirm_delete_"))
async def confirm_delete_notification_handler(
    call: CallbackQuery, manager: Manager, redis: RedisStorage, user_data: UserData
) -> None:
    """
    Подтверждает удаление конкретного уведомления.

    :param call: CallbackQuery object.
    :param manager: Manager object.
    :param redis: RedisStorage object.
    :param user_data: UserData object.
    :return: None
    """
    notification_id = call.data.replace("confirm_delete_", "")
    notification_manager = NotificationManager(redis)

    success = await notification_manager.remove_notification(notification_id)

    if success:
        await manager.send_message(manager.text_message.get("notification_deleted"))
    else:
        await manager.send_message("Произошла ошибка при удалении уведомления.")

    # Обновляем окно настроек
    await Window.notifications_settings(manager, redis, user_data)
    await call.answer()


@router.callback_query(F.data == "clear_all_notifications")
async def clear_all_notifications_handler(
    call: CallbackQuery, manager: Manager, redis: RedisStorage, user_data: UserData
) -> None:
    """
    Обрабатывает запрос на очистку всех уведомлений.

    :param call: CallbackQuery object.
    :param manager: Manager object.
    :param redis: RedisStorage object.
    :param user_data: UserData object.
    :return: None
    """
    # Подтверждение удаления
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="✅ Да, удалить все", callback_data="confirm_clear_all"
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="❌ Нет, отмена", callback_data="notifications_settings"
        )
    )

    text = manager.text_message.get("confirm_clear_all_notifications")
    await manager.send_message(text, reply_markup=builder.as_markup())
    await call.answer()


@router.callback_query(F.data == "confirm_clear_all")
async def confirm_clear_all_notifications_handler(
    call: CallbackQuery, manager: Manager, redis: RedisStorage, user_data: UserData
) -> None:
    """
    Подтверждает очистку всех уведомлений.

    :param call: CallbackQuery object.
    :param manager: Manager object.
    :param redis: RedisStorage object.
    :param user_data: UserData object.
    :return: None
    """
    notification_manager = NotificationManager(redis)

    success = await notification_manager.clear_all_notifications()

    if success:
        await manager.send_message(
            manager.text_message.get("all_notifications_cleared")
        )
    else:
        await manager.send_message("Произошла ошибка при очистке уведомлений.")

    # Обновляем окно настроек
    await Window.notifications_settings(manager, redis, user_data)
    await call.answer()


@router.callback_query(F.data.endswith("_question"))
async def handler(
    call: CallbackQuery, manager: Manager, redis: RedisStorage, user_data: UserData
) -> None:
    """
    Handles callback queries for the language question.


    :param call: CallbackQuery object.
    :param manager: Manager object.
    :param redis: RedisStorage object.
    :param user_data: UserData object.
    :return: None
    """
    choice = call.data.split("_question")[0]
    await manager.state.update_data(choice=choice)

    if choice == "payment":
        await manager.state.set_state(Form.PAYMENT)

    if choice == "other":
        await manager.state.set_state(Form.OTHER)

    await Window.request(manager)
    await call.answer()


@router.callback_query()
async def handler(
    call: CallbackQuery, manager: Manager, redis: RedisStorage, user_data: UserData
) -> None:
    """
    Handles callback queries for selecting the language.

    If the callback data is 'ru' or 'en', updates the user's language code in Redis and sets
    the language for the manager's text messages. Then, displays the main menu window.

    :param call: CallbackQuery object.
    :param manager: Manager object.
    :param redis: RedisStorage object.
    :param user_data: UserData object.
    :return: None
    """
    if call.data in SUPPORTED_LANGUAGES.keys():
        user_data.language_code = call.data
        manager.text_message.language_code = call.data
        await redis.update_user(user_data.id, user_data)
        await manager.state.update_data(language_code=call.data)
        await Window.main_menu(manager)

    await call.answer()
