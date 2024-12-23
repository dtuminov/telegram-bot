import logging
import sqlite3
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# Включаем логирование
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

# Создаем и подключаемся к базе данных
conn = sqlite3.connect('users.db')
cursor = conn.cursor()

# Создаем таблицу для хранения пользователей, если она не существует
cursor.execute('''
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY,
    username TEXT,
    matches TEXT
)
''')
conn.commit()

# Словарь для хранения профилей пользователей
user_profiles = {}

commands = [
    ("/start", "Запустить бота"),
    ("/help", "Показать доступные команды"),
    ("/register", "Зарегистрироваться"),
    ("/profile", "Посмотреть свой профиль"),
    ("/edit_profile", "Редактировать профиль"),
    ("/find_match", "Найти совпадения")
]

def create_menu_keyboard():
    keyboard = [[command[0] for command in commands]]  # Создаем одну строку с командами
    return ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)


async def set_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Пожалуйста, введите информацию о себе."
    )


# Хэндлер для текстовой информации
async def receive_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id

    info = update.message.text
    user_profiles[user_id] = {'info': info, 'photo': None}

    await update.message.reply_text(
        f"Информация о вас сохранена: {info}. "
        "Теперь вы можете отправить свою фотографию, используя команду /set_photo."
    )


async def set_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Пожалуйста, отправьте фотографию для вашего профиля."
    )


# Хэндлер для получения фотографии
async def receive_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id

    if user_id in user_profiles:
        # Получение файла фотографии
        photo_file = update.message.photo[-1].file_id
        user_profiles[user_id]['photo'] = photo_file

        # Отправляем подтверждение
        await update.message.reply_text(
            "Фотография профиля сохранена! Теперь вы можете использовать команду /profile, чтобы увидеть свой профиль."
        )
    else:
        await update.message.reply_text(
            "Сначала введите свою информацию с помощью команды /set_info."
        )


# Команда для отображения профиля
async def profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id

    if user_id in user_profiles:
        info = user_profiles[user_id]['info']
        photo = user_profiles[user_id]['photo']

        response_message = f"Ваш профиль:\nИнформация: {info}\n"

        if photo:
            response_message += "Фотография: (отправлена)"
            await context.bot.send_photo(chat_id=user_id, photo=photo)
        else:
            response_message += "Фотография: не установлена."

        await update.message.reply_text(response_message)
    else:
        await update.message.reply_text(
            "Вы еще не создали профиль. Используйте команду /set_info."
        )


# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(f"Привет! Я бот для знакомств.",
                                    reply_markup=create_menu_keyboard())  # Отправляем клавиатуру с командами"


# Регистрация пользователя
async def register(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.message.from_user.id
    user_name = update.message.from_user.username

    # Проверяем, зарегистрирован ли пользователь
    cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
    user = cursor.fetchone()

    if user is None:
        cursor.execute('INSERT INTO users (id, username, matches) VALUES (?, ?, ?)',
                       (user_id, user_name, ''))
        conn.commit()
        await update.message.reply_text(f"{user_name}, ты зарегистрирован!")
    else:
        await update.message.reply_text("Ты уже зарегистрирован!")


# Команда для поиска совпадений
async def find_match(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.message.from_user.id

    cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
    user = cursor.fetchone()

    if user is None:
        await update.message.reply_text("Сначала зарегистрируйся с помощью команды 'регистрация'.")
        return

    # Получаем всех пользователей, кроме текущего
    cursor.execute('SELECT * FROM users WHERE id != ?', (user_id,))
    potential_matches = cursor.fetchall()

    matches = []
    for uid, username, matched_ids in potential_matches:
        if str(uid) not in user[2].split(','):  # matched_ids
            matches.append(username)

    if matches:
        await update.message.reply_text("Вот потенциальные совпадения:\n" + "\n".join(matches))
    else:
        await update.message.reply_text("Пока нет совпадений.")


# Указываем функцию для обработки текстовых сообщений
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = update.message.text.lower()
    if text[0] == '?':
        await find_match(update, context)
    if text == 'регистрация':
        await register(update, context)
    elif text == 'найти совпадение':
        await find_match(update, context)
    else:
        await update.message.reply_text("Команда не распознана. Используй 'регистрация' или 'найти совпадение'.")


# Функция для отображения доступных команд
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # Формируем сообщение с командами
    command_list = "\n".join([f"{cmd} - {desc}" for cmd, desc in commands])

    await update.message.reply_text(f"Вам доступны следующие команды:\n{command_list}")


def main() -> None:
    # Замените 'YOUR_TOKEN_HERE' на токен вашего бота
    application = ApplicationBuilder().token("7558907076:AAHsIPc9L2zGXMDZDtTrxqH7mhr01eApt2g").build()

    # Установка команд
    application.bot.set_my_commands([
        ("start", "Запустить бота"),
        ("help", "Показать доступные команды"),
        ("register", "Зарегистрироваться"),
        ("profile", "Посмотреть свой профиль"),
        ("edit_profile", "Редактировать профиль"),
        ("find_match", "Найти совпадения")
    ])

    # Обработчики команд
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("register", register))
    application.add_handler(CommandHandler("find_match", find_match))
    # application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    application.add_handler(CommandHandler("set_info", set_info))
    application.add_handler(CommandHandler("set_photo", set_photo))
    application.add_handler(CommandHandler("profile", profile))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, receive_info))
    application.add_handler(MessageHandler(filters.PHOTO, receive_photo))

    # Запускаем бота
    application.run_polling()


if __name__ == '__main__':
    try:
        main()
    finally:
        conn.close()  # Закрываем соединение с базой данных при завершении
