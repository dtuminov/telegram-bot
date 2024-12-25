import logging
import sqlite3
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

# Создаем и подключаемся к базе данных
conn = sqlite3.connect('/Users/dmitrijtuminov/Documents/Code/Telegram-bot/users.db') # бля вот это вообще пиздец
cursor = conn.cursor()


# Команда для отображения профиля
async def profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id

    cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
    user = cursor.fetchone()

    if user:
        name = user[2]  # Имя пользователя
        info = user[3]
        photo = user[4]

        response_message = f"Ваш профиль:\nИмя: {name}\nИнформация: {info}\n"

        if photo:
            response_message += "Фотография: (отправлена)"
            await context.bot.send_photo(chat_id=user_id, photo=photo)
        else:
            response_message += "Фотография: не установлена."

        await update.message.reply_text(response_message)
    else:
        await update.message.reply_text(
            "Вы еще не создали профиль. Используйте команду /register."
        )
