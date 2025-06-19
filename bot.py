import logging
import asyncio
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import requests
import os
import signal

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENWEATHER_TOKEN = os.getenv("OPENWEATHER_TOKEN")

if not TELEGRAM_TOKEN or not OPENWEATHER_TOKEN:
    raise ValueError("Токены TELEGRAM_TOKEN и OPENWEATHER_TOKEN не заданы!")

USERS = {
    "Женя": {"chat_id": "kkkv22", "city": "Warsaw"},
    "Никита": {"chat_id": "nikita_chat_id", "city": "Warsaw"},
    "Рома": {"chat_id": "roman_babun", "city": "Rivne"},
    "Витек": {"chat_id": "viktip09", "city": "Kelowna"},
}

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Бот запущен и работает!")

def get_weather(city: str) -> str:
    url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={OPENWEATHER_TOKEN}&units=metric&lang=ru"
    try:
        response = requests.get(url).json()
        if response.get("cod") != 200:
            return "Не удалось получить погоду."
        weather = response["weather"][0]["description"]
        temp = response["main"]["temp"]
        return f"Погода в {city}: {weather}, {temp}°C"
    except Exception as e:
        logger.error(f"Ошибка запроса погоды: {e}")
        return "Ошибка при запросе к API."

async def send_weather(application):
    for user, data in USERS.items():
        try:
            weather = get_weather(data["city"])
            await application.bot.send_message(
                chat_id=data["chat_id"],
                text=weather
            )
            logger.info(f"Погода отправлена для {user}")
        except Exception as e:
            logger.error(f"Ошибка при отправке для {user}: {e}")

async def run_bot():
    application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    application.add_handler(CommandHandler("start", start))

    scheduler = AsyncIOScheduler()
    scheduler.add_job(
        send_weather,
        "cron",
        hour=9,
        minute=0,
        args=[application]
    )
    scheduler.start()

    logger.info("Бот запущен и ожидает сообщений...")
    
    # Создаем и регистрируем обработчик сигналов
    loop = asyncio.get_running_loop()
    stop_event = asyncio.Event()
    
    def signal_handler():
        logger.info("Получен сигнал завершения")
        stop_event.set()
    
    for sig in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(sig, signal_handler)
    
    try:
        async with application:
            await application.start()
            await stop_event.wait()  # Ожидаем сигнала завершения
    finally:
        scheduler.shutdown()
        await application.stop()
        logger.info("Бот завершил работу")

def main():
    try:
        asyncio.run(run_bot())
    except KeyboardInterrupt:
        logger.info("Бот остановлен по запросу пользователя")
    except Exception as e:
        logger.critical(f"Фатальная ошибка: {e}")
    finally:
        logger.info("Приложение завершено")

if __name__ == "__main__":
    main()
