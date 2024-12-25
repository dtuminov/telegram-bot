import logging
import sqlite3
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from handlers.show_next_match import show_next_match
# Создаем и подключаемся к базе данных
conn = sqlite3.connect('/Users/dmitrijtuminov/Documents/Code/Telegram-bot/users.db') # бля вот это вообще пиздец
cursor = conn.cursor()

async def find_match(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.message.from_user.id

    cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
    user = cursor.fetchone()

    if user is None:
        await update.message.reply_text("Сначала зарегистрируйся с помощью команды /register.")
        return

    # Получаем всех пользователей, кроме текущего
    cursor.execute('SELECT * FROM users WHERE id != ?', (user_id,))
    potential_matches = cursor.fetchall()

    if not potential_matches:
        await update.message.reply_text("Пока нет совпадений.")
        return

    # Сохраняем потенциальные совпадения в контексте
    context.user_data['potential_matches'] = potential_matches
    context.user_data['match_index'] = 0  # Начинаем с первого совпадения

    # Показываем первое совпадение
    await show_next_match(update, context)