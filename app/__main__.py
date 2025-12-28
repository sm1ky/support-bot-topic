import asyncio
from redis import asyncio as aioredis

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from apscheduler.jobstores.redis import RedisJobStore
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from .bot import commands
from .bot.handlers import include_routers
from .bot.middlewares import register_middlewares
from aiogram.fsm.storage.redis import RedisStorage
from .config import load_config, Config
from .logger import setup_logger
from .bot.jobs import setup_persistent_jobs
import logging

logger = logging.getLogger(__name__)


async def clear_fsm_keys(redis_url: str) -> None:
    redis = aioredis.from_url(redis_url)
    keys = await redis.keys("fsm:*")
    if keys:
        await redis.delete(*keys)
    await redis.close()


async def on_startup(
    dispatcher: Dispatcher,
    config: Config,
    bot: Bot,
    persistent_scheduler: AsyncIOScheduler,
    **kwargs,
) -> None:
    logger.info("Запускаю startup")
    print("⚡️ Бот запускается...")
    await setup_persistent_jobs(persistent_scheduler, bot)
    await commands.setup(bot, config)
    print("✅ Команды загружены!")


async def on_shutdown(
    dispatcher: Dispatcher,
    config: Config,
    bot: Bot,
    apscheduler: AsyncIOScheduler,
    persistent_scheduler: AsyncIOScheduler,
    **kwargs,
) -> None:
    logger.info("Запускаю shutdown")
    apscheduler.shutdown()
    persistent_scheduler.shutdown()
    await commands.delete(bot, config)
    await dispatcher.storage.close()
    await bot.delete_webhook()
    await bot.session.close()


async def main() -> None:
    config = load_config()
    await clear_fsm_keys(config.redis.dsn())

    # Инициализация вне хендлеров
    job_store = RedisJobStore(
        host=config.redis.HOST, port=config.redis.PORT, db=config.redis.DB
    )
    apscheduler = AsyncIOScheduler(jobstores={"default": job_store})
    persistent_scheduler = AsyncIOScheduler()

    redis_client = aioredis.from_url(config.redis.dsn())
    storage = RedisStorage(redis_client)

    bot = Bot(
        token=config.bot.TOKEN,
        default=DefaultBotProperties(
            parse_mode=ParseMode.HTML, link_preview_is_disabled=True
        ),
    )
    dp = Dispatcher(
        persistent_scheduler=persistent_scheduler,
        apscheduler=apscheduler,
        storage=storage,
        config=config,
        bot=bot,
    )

    # Передаём нужные зависимости в хендлеры через kwargs
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)

    logger.debug("Регистрирую роутеры")
    include_routers(dp)
    logger.debug("Регистрирую мидлвары")
    register_middlewares(
        dp, config=config, redis=storage.redis, apscheduler=apscheduler
    )

    # Запускаем планировщики после регистрации задач
    apscheduler.start()
    persistent_scheduler.start()

    await bot.delete_webhook()
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())


if __name__ == "__main__":
    setup_logger()
    asyncio.run(main())
