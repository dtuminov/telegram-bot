import logging
import sqlite3
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

# Создаем и подключаемся к базе данных
conn = sqlite3.connect('/Users/dmitrijtuminov/Documents/Code/Telegram-bot/users.db') # бля вот это вообще пиздец
cursor = conn.cursor()

# Хэндлер для получения фотографии
async def receive_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id

    if context.user_data.get('registering') and context.user_data.get('step') == 'photo':
        # Получение файла фотографии
        photo_file = update.message.photo[-1].file_id
        name = context.user_data.get('name')
        info = context.user_data.get('info')

        # Сохраняем данные в БД
        cursor.execute(
            'INSERT INTO users (id, username, name, info, photo, matches) VALUES (?, ?, ?, ?, ?, ?)',
            (user_id, update.message.from_user.username, name, info, photo_file, '')
        )
        conn.commit()

        # Убираем флаг регистрации
        context.user_data['registering'] = False
        context.user_data['step'] = None  # Сбрасываем шаг

        await update.message.reply_text(
            "Регистрация завершена! Ваш профиль создан. Теперь вы можете использовать команду /profile."
        )
    else:
        await update.message.reply_text("Сначала зарегистрируйтесь с помощью команды /register.")
