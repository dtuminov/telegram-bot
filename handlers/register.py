import logging
import sqlite3
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

# Создаем и подключаемся к базе данных
conn = sqlite3.connect('/Users/dmitrijtuminov/Documents/Code/Telegram-bot/users.db') # бля вот это вообще пиздец
cursor = conn.cursor()

# Регистрация пользователя
async def register(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.message.from_user.id

    # Проверяем, зарегистрирован ли пользователь
    cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
    user = cursor.fetchone()

    if user is None:
        # Начинаем процесс регистрации
        await update.message.reply_text("Вы зарегистрируетесь. Пожалуйста, введите ваше имя.")
        context.user_data['registering'] = True  # Устанавливаем флаг регистрации
        context.user_data['step'] = 'name'  # Устанавливаем текущий шаг регистрации
    else:
        await update.message.reply_text("Вы уже зарегистрированы!")