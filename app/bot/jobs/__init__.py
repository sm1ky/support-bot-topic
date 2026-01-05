from apscheduler.schedulers.asyncio import AsyncIOScheduler
from aiogram import Bot

from .close_inactive_topic import close_inactive_topics
from .send_new_topics import send_new_topics
from .bump_topic import bump_topic
from .delete_inactive_topics import delete_inactive_topics
import logging

from app.config import load_config

logger = logging.getLogger(__name__)


async def setup_persistent_jobs(
    persistent_scheduler: AsyncIOScheduler, bot: Bot
) -> None:

    config = load_config()

    job = persistent_scheduler.add_job(
        send_new_topics,
        "interval",
        hours=3,
        coalesce=True,
        misfire_grace_time=1,
        max_instances=1,
        kwargs={"bot": bot, "config": config},
        id="send_new_topics",
        replace_existing=True,
    )
    logger.info(f"Задача {job} добавлена с интервалом 3 часа")

    job = persistent_scheduler.add_job(
        close_inactive_topics,
        trigger="interval",
        hours=2,
        args=[bot, config],
        id="close_inactive_topics",
        replace_existing=True,
        max_instances=1,
    )
    logger.info(f"Задача {job} добавлена с интервалом 2 часа")

    # job = persistent_scheduler.add_job(
    #     delete_inactive_topics,
    #     "interval",
    #     hours=6,
    #     coalesce=True,
    #     misfire_grace_time=1,
    #     max_instances=1,
    #     kwargs={"bot": bot, "config": config},
    #     id="delete_inactive_topics",
    #     replace_existing=True,
    # )
    # logger.info(f"Задача {job} добавлена с интервалом 6 часов")

    if not config.bot.DISABLE_BUMP:
        job = persistent_scheduler.add_job(
            bump_topic,
            "interval",
            hours=2,
            coalesce=True,
            misfire_grace_time=1,
            max_instances=1,
            kwargs={"bot": bot, "config": config},
            id="bump_topic",
            replace_existing=True,
        )
        logger.info(f"Задача {job} добавлена с интервалом 2 часа")


__all__ = ["setup_persistent_jobs"]
