import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.memory import MemoryStorage

from core.config import settings
from core.redis import init_redis, close_redis
from db.session import init_db
from bot.middlewares.db import DatabaseMiddleware

# Handlers
from bot.handlers.base import router as base_router
from bot.handlers.profile import router as profile_router
from bot.handlers.horoscope import router as horoscope_router
from bot.handlers.tarot import router as tarot_router
from bot.handlers.synastry import router as synastry_router
from bot.handlers.ai_chat import router as ai_chat_router
from bot.handlers.payments import router as payments_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("astro_bot")


async def main() -> None:
    logger.info("Initializing AstroBot application...")

    # Initialize DB schema
    await init_db()
    logger.info("Database initialized.")

    # Initialize Redis
    try:
        await init_redis()
        logger.info("Redis connected.")
    except Exception as e:
        logger.warning(f"Could not connect to Redis: {e}. Running with memory fallback.")

    bot = Bot(
        token=settings.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher(storage=MemoryStorage())

    # Middleware
    dp.update.middleware(DatabaseMiddleware())

    # Routers
    dp.include_router(base_router)
    dp.include_router(payments_router)
    dp.include_router(profile_router)
    dp.include_router(horoscope_router)
    dp.include_router(tarot_router)
    dp.include_router(synastry_router)
    dp.include_router(ai_chat_router)

    logger.info("Starting polling...")
    try:
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        await close_redis()
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
