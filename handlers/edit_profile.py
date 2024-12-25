import logging
import sqlite3
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

logger = logging.getLogger(__name__)

# Создаем и подключаемся к базе данных
conn = sqlite3.connect('/Users/dmitrijtuminov/Documents/Code/Telegram-bot/users.db') # бля вот это вообще пиздец
cursor = conn.cursor()

# Функция для обновления имени пользователя в базе данных
def update_user_name_in_db(user_id, new_name):
    try:
        cursor.execute('''
            UPDATE users SET username = ? WHERE id = ?
        ''', (new_name, user_id))
        conn.commit()
        logger.info(f'Имя пользователя с ID {user_id} обновлено на {new_name}.')
    except Exception as e:
        logger.error(f'Ошибка обновления имени пользователя: {e}')

async def edit_profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    await update.message.reply_text('Введите новое имя для вашего профиля.')

    # Сохраняем состояние, чтобы ожидать ответ от пользователя
    context.user_data['edit_mode'] = True
    context.user_data['user_id'] = user.id  # Сохраняем ID пользователя для дальнейшего использования

async def receive_new_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get('edit_mode'):
        new_name = update.message.text
        user_id = context.user_data.get('user_id')

        # Проверка наличия пользователя в базе данных
        cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
        if cursor.fetchone() is None:
            await update.message.reply_text('Пользователь не найден в базе данных. Пожалуйста, зарегистрируйтесь.')
            return

        # Обновляем имя в базе данных
        update_user_name_in_db(user_id, new_name)

        await update.message.reply_text(f'Ваше имя было обновлено на: {new_name}')

        # Убираем режим редактирования
        context.user_data['edit_mode'] = False
    else:
        await update.message.reply_text('Вы не находитесь в режиме редактирования. Начните с команды /edit_profile.')