import asyncio
import logging
import os
from datetime import datetime
import pytz
import requests

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from telegram import Update
from telegram.ext import (
    ApplicationBuilder, CommandHandler, ContextTypes
)

# Логгирование
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# Константы
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENWEATHER_TOKEN = os.getenv("OPENWEATHER_TOKEN")

USERS = [
    {"chat_id": 123456789, "name": "Женя", "city": "Warsaw", "timezone": "Europe/Warsaw"},
    {"chat_id": 987654321, "name": "Никита", "city": "Warsaw", "timezone": "Europe/Warsaw"},
    {"chat_id": 112233445, "name": "Рома", "city": "Rivne", "timezone": "Europe/Kiev"},
    {"chat_id": 998877665, "name": "Витек", "city": "Kelowna", "timezone": "America/Vancouver"},
]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Бот работает и будет присылать тебе погоду!")

def get_weather(city: str):
    url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={OPENWEATHER_TOKEN}&units=metric&lang=ru"
    response = requests.get(url)
    if response.status_code != 200:
        return f"Ошибка получения погоды для {city}"
    data = response.json()
    description = data["weather"][0]["description"].capitalize()
    temp = data["main"]["temp"]
    return f"Погода в {city}: {description}, {temp}°C"

async def send_weather(application):
    for user in USERS:
        city = user["city"]
        weather = get_weather(city)
        try:
            await application.bot.send_message(chat_id=user["chat_id"], text=weather)
        except Exception as e:
            logger.error(f"Не удалось отправить погоду {user['name']}: {e}")

async def main():
    application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    application.add_handler(CommandHandler("start", start))

    scheduler = AsyncIOScheduler()
    scheduler.add_job(send_weather, "cron", hour=9, minute=0, args=[application])
    scheduler.start()

    logger.info("Бот запущен и ожидает сообщений...")
    await application.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
