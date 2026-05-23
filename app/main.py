import asyncio
import logging
import os
import sys


CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))

if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)


print("=== ENV DEBUG START ===")
print("BOT_TOKEN exists:", bool(os.getenv("BOT_TOKEN")))
print("GEMINI_API_KEY exists:", bool(os.getenv("GEMINI_API_KEY")))
print("GEMINI_MODEL exists:", bool(os.getenv("GEMINI_MODEL")))
print("TILDA_LOGIN exists:", bool(os.getenv("TILDA_LOGIN")))
print("TILDA_PASSWORD exists:", bool(os.getenv("TILDA_PASSWORD")))
print("TILDA_PROJECT_URL exists:", bool(os.getenv("TILDA_PROJECT_URL")))
print("HEADLESS exists:", bool(os.getenv("HEADLESS")))
print("=== ENV DEBUG END ===")


from config import settings
from bot_handlers import router
from aiogram import Bot, Dispatcher


async def main():
    logging.basicConfig(level=logging.INFO)

    bot = Bot(token=settings.BOT_TOKEN)
    dp = Dispatcher()

    dp.include_router(router)

    logging.info("Bot started")

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
    asyncio.run(main())
