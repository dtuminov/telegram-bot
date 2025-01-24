import logging

from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

from handlers.edit_profile import edit_profile, receive_new_info, receive_photo_edit
from handlers.find_matches import find_match, handle_user_input, handle_message
from handlers.help import help_command
from handlers.profile import profile
from handlers.registration import register, receive_info, receive_photo
from handlers.start import start
from init import conn, cursor, create_menu_keyboard

# Включаем логирование
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

# Создаем таблицу для хранения пользователей, если она не существует
cursor.execute('''
CREATE TABLE IF NOT EXISTS users (
   id INTEGER PRIMARY KEY,
    username TEXT,
    name TEXT,
    course TEXT,
    course_name TEXT,
    age TEXT,
    tags TEXT,
    info TEXT,
    preferences TEXT,
    photo TEXT,
    matches TEXT,
    interests TEXT,
    gender TEXT
)
''')

# Добавляем таблицу лайков
cursor.execute('''
    CREATE TABLE IF NOT EXISTS likes (
        user_id INTEGER,
        liked_user_id INTEGER,
        PRIMARY KEY (user_id, liked_user_id)
    )
''')

conn.commit()


async def delete_profile(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    cursor.execute('DELETE FROM users WHERE id = ?', (user_id,))
    conn.commit()

    # Сначала удаляем все лайки, связанные с пользователем
    cursor.execute('DELETE FROM likes WHERE user_id = ?', (user_id,))
    conn.commit()

    if cursor.rowcount > 0:
        await update.message.reply_text("Ваш профиль был успешно удалён.")
    else:
        await update.message.reply_text("Профиль не найден. Вы не зарегистрированы.")


# Указываем функцию для обработки текстовых сообщений
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if context.user_data.get('awaiting_message'):
        await handle_message(update, context)
    if context.user_data.get('potential_matches'):
        await handle_user_input(update, context)
    elif context.user_data.get('registering'):
        await receive_info(update, context)
    elif context.user_data.get('edit_mode'):
        await receive_new_info(update, context)
    else:
        await update.message.reply_text("Команда не распознана. Используйте /help.",
                                        reply_markup=create_menu_keyboard())


# Функция для обработки фотографий
async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message.photo and context.user_data.get('edit_mode'):
        await receive_photo_edit(update, context)
    elif update.message.photo and context.user_data.get('registering'):
        await receive_photo(update, context)



def main() -> None:
    application = ApplicationBuilder().token("7632994860:AAFIt1WIhet6we6fJWsy2SJ5t3I25hNOxgQ").build()

    # Установка команд
    application.bot.set_my_commands([
        ("start", "Запустить бота"),
        ("help", "Показать доступные команды"),
        ("register", "Зарегистрироваться"),
        ("profile", "Посмотреть свой профиль"),
        ("edit_profile", "Редактировать профиль"),
        ("find_match", "Найти совпадения"),
        ("delete_profile", "Удалить свой профиль")
    ])

    # Обработчики команд
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("register", register))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("profile", profile))
    application.add_handler(CommandHandler("edit_profile", edit_profile))
    application.add_handler(CommandHandler("find_match", find_match))
    application.add_handler(CommandHandler("delete_profile", delete_profile))  # Добавлен обработчик
    application.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    # Запускаем бота
    application.run_polling()


if __name__ == '__main__':
    try:
        main()
    finally:
        conn.close()  # Закрываем соединение с базой данных при завершении
