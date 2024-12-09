import os
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, Bot
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters
from telethon import TelegramClient
import nest_asyncio
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# Установка asyncio для работы в Replit
nest_asyncio.apply()

# Чтение переменных окружения из Replit
api_id = int(os.getenv("API_ID", "24324199"))  
api_hash = os.getenv("API_HASH", "eb7b4c1e0abe7b498d48aac94c542f2b")
phone_number = os.getenv("PHONE_NUMBER", "+393758134345")  
TOKEN = os.getenv("BOT_TOKEN", "7730268810:AAGTR-NZksFykOYFUokP-8X9H1a9ydMaX_I")

# Каналы для проверки подписки
channels_to_check = [{'name': 'MovieVauIt', 'link': 'https://t.me/MovieVauIt'}]

# Инициализация Telethon клиента
client = TelegramClient('session_name', api_id, api_hash)
bot = Bot(TOKEN)

# Проверка подписки на каналы
async def check_subscription(user_id):
    try:
        await client.start()
        for channel in channels_to_check:
            try:
                participants = await client.get_participants(channel['name'])
                if not any(user.id == user_id for user in participants):
                    return False
            except Exception as e:
                logging.error(f"Ошибка при проверке подписки на канал {channel['name']}: {e}")
                return False
        return True
    except Exception as e:
        logging.error(f"Ошибка подключения к Telethon: {e}")
        return False

# Поиск фильма по коду
async def find_movie_by_code(channel, code):
    try:
        await client.start()
        messages = await client.get_messages(channel['name'], limit=1000)
        for message in messages:
            if str(code) in message.text:
                return message.text
    except Exception as e:
        logging.error(f"Ошибка при поиске фильма в канале {channel['name']}: {e}")
    return None

# Команда /start
async def start(update: Update, context):
    name = update.message.from_user.first_name
    keyboard = [
        [InlineKeyboardButton("MovieVauIt", url="https://t.me/MovieVauIt")],
        [InlineKeyboardButton("Подписался", callback_data="check_subscription")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        f"Привет, {name}! Я помогу тебе найти лучшие фильмы по одному коду.\n\n"
        "Чтобы использовать бота, подпишись на каналы ниже, затем нажми кнопку 'Подписался'.",
        reply_markup=reply_markup
    )

# Обработка кнопок
async def button_click(update: Update, context):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    if await check_subscription(user_id):
        keyboard = [[InlineKeyboardButton("Искать фильм по коду", callback_data="start_search_movie")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            text="Отлично, теперь вы можете искать фильмы. Нажмите на кнопку ниже, чтобы начать поиск!",
            reply_markup=reply_markup
        )
    else:
        keyboard = [
            [InlineKeyboardButton("MovieVauIt", url="https://t.me/MovieVauIt")],
            [InlineKeyboardButton("Подписался", callback_data="check_subscription")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            text="Вы не подписались на все каналы. Пожалуйста, подпишитесь и нажмите кнопку снова.",
            reply_markup=reply_markup
        )

# Начало поиска фильма
async def start_search_movie(update: Update, context):
    await update.callback_query.answer()
    user_id = update.callback_query.from_user.id
    if not await check_subscription(user_id):
        await update.callback_query.edit_message_text("Пожалуйста, подпишитесь на все каналы, чтобы начать поиск фильма.")
        return
    await update.callback_query.edit_message_text("Пожалуйста, напишите код фильма для поиска.")
# Обработка кода фильма
async def handle_movie_code(update: Update, context):
    user_id = update.message.from_user.id
    movie_code = update.message.text.strip()
    if not await check_subscription(user_id):
        await update.message.reply_text("Пожалуйста, подпишитесь на все каналы, чтобы использовать эту функцию.")
        return
    try:
        movie_code = int(movie_code)
        movie_description = None
        for channel in channels_to_check:
            movie_description = await find_movie_by_code(channel, movie_code)
            if movie_description:
                break
        if movie_description:
            await update.message.reply_text(f"Фильм с кодом {movie_code} найден: {movie_description}")
        else:
            await update.message.reply_text(f"Фильм с кодом {movie_code} не найден.")
    except ValueError:
        await update.message.reply_text("Введите корректный числовой код.")
    keyboard = [[InlineKeyboardButton("Искать фильм по коду", callback_data="start_search_movie")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Что вы хотите сделать дальше?", reply_markup=reply_markup)

# Главная функция
async def main():
    try:
        await client.start()
        application = Application.builder().token(TOKEN).build()
        application.add_handler(CommandHandler("start", start))
        application.add_handler(CallbackQueryHandler(button_click, pattern="^check_subscription$"))
        application.add_handler(CallbackQueryHandler(start_search_movie, pattern="^start_search_movie$"))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_movie_code))
        logging.info("Бот запущен и готов к работе!")
        await application.run_polling()
    except Exception as e:
        logging.error(f"Ошибка запуска бота: {e}")

if __name__ == "__main__":
    asyncio.run(main())