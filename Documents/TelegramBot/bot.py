import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes, CallbackQueryHandler, MessageHandler, filters
from telethon import TelegramClient
import nest_asyncio
import re

nest_asyncio.apply()

api_id = '24324199'
api_hash = 'eb7b4c1e0abe7b498d48aac94c542f2b'
phone_number = '+393758134345'

channels_to_check = [
    {'name': 'MovieVauIt', 'link': 'https://t.me/MovieVauIt'},
]

client = TelegramClient('session_name', api_id, api_hash)

# Проверка подписки на каналы
async def check_subscription(user_id):
    await client.start(phone_number)
    for channel in channels_to_check:
        try:
            participants = await client.get_participants(channel['name'])
            if not any(user.id == user_id for user in participants):
                return False
        except Exception as e:
            print(f"Ошибка при проверке подписки на канал {channel['name']}: {e}")
            return False
    return True

# Поиск фильма по коду
async def find_movie_by_code(channel, code):
    try:
        messages = await client.get_messages(channel['name'], limit=10000)
        for message in messages:
            match = re.search(r'\b' + str(code) + r'\b', message.text)
            if match:
                return message.text
    except Exception as e:
        print(f"Ошибка при поиске фильма в канале {channel['name']}: {e}")
    return None

# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print("Обработка команды /start")
    name = update.message.from_user.first_name

    # Кнопки с каналами и кнопка "Подписался"
    keyboard = [
        [InlineKeyboardButton("MovieVauIt", url="https://t.me/MovieVauIt")],
        [InlineKeyboardButton("Подписался", callback_data="check_subscription")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        f"Привет, {name}! Я помогу тебе найти лучшие фильмы всего лишь по одному коду.\n\n"
        "Чтобы использовать бота, подпишись на каналы ниже, затем нажми кнопку 'Подписался'.",
        reply_markup=reply_markup
    )

# Проверка подписки при нажатии на кнопку "Подписался"
async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = update.callback_query.from_user.id
    if await check_subscription(user_id):
        # Если подписка проверена, отправляем сообщение и показываем кнопку для поиска фильма
        keyboard = [[InlineKeyboardButton("Искать фильм по коду", callback_data="start_search_movie")]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text(
            text="Отлично, теперь вы можете искать фильмы. Нажмите на кнопку ниже, чтобы начать поиск!",
            reply_markup=reply_markup
        )
    else:
        # Если пользователь не подписан, отправляем кнопку подписки снова
        keyboard = [
            [InlineKeyboardButton("MovieVauIt", url="https://t.me/MovieVauIt")],
            [InlineKeyboardButton("Подписался", callback_data="check_subscription")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            text="Вы не подписались на все каналы. Пожалуйста, подпишитесь и нажмите кнопку снова.",
            reply_markup=reply_markup
        )

# Обработка кнопки для начала поиска фильма
async def start_search_movie(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    
    user_id = update.callback_query.from_user.id
    if not await check_subscription(user_id):
        await update.callback_query.edit_message_text("Пожалуйста, подпишитесь на все каналы, чтобы начать поиск фильма.")
        return
    
    # Запрашиваем код фильма
    await update.callback_query.edit_message_text("Пожалуйста, напишите код фильма для поиска.")
# Обработка введенного пользователем кода для поиска фильма
async def handle_movie_code(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    movie_code = update.message.text.strip()  # Получаем введенный код фильма
    
    if not await check_subscription(user_id):
        await update.message.reply_text("Пожалуйста, подпишитесь на все каналы, чтобы использовать эту функцию.")
        return

    try:
        movie_code = int(movie_code)  # Преобразуем введенный код в целое число
        movie_description = None
        for channel in channels_to_check:
            movie_description = await find_movie_by_code(channel, movie_code)
            if movie_description:
                break

        if movie_description:
            await update.message.reply_text(f"Фильм с кодом {movie_code} найден: {movie_description}")
        else:
            await update.message.reply_text(f"Фильм с кодом {movie_code} не найден в канале.")
    except ValueError:
        await update.message.reply_text("Пожалуйста, введите корректный числовой код для поиска фильма.")

    # После ответа, показываем кнопку для повторного поиска
    keyboard = [[InlineKeyboardButton("Искать фильм по коду", callback_data="start_search_movie")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        text="Что вы хотите сделать дальше?",
        reply_markup=reply_markup
    )

# Главная асинхронная функция для запуска бота
async def main():
    TOKEN = "7730268810:AAGTR-NZksFykOYFUokP-8X9H1a9ydMaX_I"  # Ваш токен Telegram бота
    print("Запуск бота...")
    application = Application.builder().token(TOKEN).build()

    # Добавляем обработчики команд
    application.add_handler(CommandHandler("start", start))  # Команда /start
    application.add_handler(CallbackQueryHandler(button_click, pattern="^check_subscription$"))  # Обработчик кнопки "Подписался"
    application.add_handler(CallbackQueryHandler(start_search_movie, pattern="^start_search_movie$"))  # Обработка кнопки начала поиска
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_movie_code))  # Обработка текста с кодом фильма

    await application.run_polling()  # Запуск бота

# Запуск бота
if __name__ == "__main__":
    try:
        loop = asyncio.get_event_loop()
        loop.run_until_complete(main())  # Запуск бота с использованием текущего цикла событий
    except RuntimeError:
        asyncio.run(main())  # Если цикл событий уже запущен, используем asyncio.run()