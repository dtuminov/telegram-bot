import logging
import sqlite3
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

from handlers.start import start
from handlers.register import register
from handlers.receive_photo import receive_photo
from handlers.help_command import help_command
from handlers.show_next_match import show_next_match
from handlers.find_match import find_match
from handlers.profie import profile
from handlers.edit_profile import edit_profile, receive_new_info
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
    name TEXT,
    info TEXT,
    photo TEXT,
    matches TEXT
)
''')
conn.commit()

commands = [
    ("/start", "Запустить бота"),
    ("/help", "Показать доступные команды"),
    ("/register", "Зарегистрироваться"),
    ("/profile", "Посмотреть свой профиль"),
    ("/edit_profile", "Редактировать профиль"),
    ("/find_match", "Найти совпадения")
]

# Хэндлер для текстовой информации
async def receive_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id

    step = context.user_data.get('step')

    if context.user_data.get('registering'):
        if step == 'name':
            name = update.message.text
            context.user_data['name'] = name  # Сохраняем имя
            await update.message.reply_text("Имя сохранено. Теперь расскажите немного о себе.")
            context.user_data['step'] = 'info'  # Переходим к следующему шагу
        elif step == 'info':
            info = update.message.text
            context.user_data['info'] = info  # Сохраняем информацию об пользователе

            await update.message.reply_text("Информация сохранена. Теперь отправьте свою фотографию.")
            context.user_data['step'] = 'photo'  # Переходим к следующему шагу
    else:
        print("поправь потом")
        #await update.message.reply_text("Сначала зарегистрируйтесь с помощью команды /register.")


# Указываем функцию для обработки текстовых сообщений
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if context.user_data.get('potential_matches'):
        await show_next_match(update, context)
    else:
        await update.message.reply_text("Сначала закажите поиск совпадений с помощью команды /find_match.")
    # Обрабатываем текст, либо вызываем обработчики
    if context.user_data.get('registering'):
        await receive_info(update, context)
    else:
        await update.message.reply_text("Команда не распознана. Используйте /help.")

def main() -> None:
    application = ApplicationBuilder().token("7558907076:AAHsIPc9L2zGXMDZDtTrxqH7mhr01eApt2g").build()  # Замените на ваш токен

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
    application.add_handler(CommandHandler("profile", profile))
    application.add_handler(CommandHandler("find_match", find_match))
    application.add_handler(CommandHandler("edit_profile", edit_profile))
    application.add_handler(MessageHandler(filters.PHOTO, receive_photo))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    # Запускаем бота
    application.run_polling()

if __name__ == '__main__':
    try:
        main()
    finally:
        conn.close()  # Закрываем соединение с базой данных при завершении