# /app/bot/middlewares/__init__.py
from aiogram import Dispatcher
from aiogram_newsletter.middleware import AiogramNewsletterMiddleware

from .album import AlbumMiddleware
from .manager import ManagerMiddleware
from .redis import RedisMiddleware
from .throttling import ThrottlingMiddleware


def register_middlewares(dp: Dispatcher, **kwargs) -> None:
    dp.update.outer_middleware.register(RedisMiddleware(kwargs["redis"]))
    dp.update.outer_middleware.register(ManagerMiddleware()) 
    dp.message.middleware.register(AlbumMiddleware())
    dp.message.middleware.register(ThrottlingMiddleware())
    dp.update.middleware.register(AiogramNewsletterMiddleware(kwargs["apscheduler"]))


__all__ = ["register_middlewares"]