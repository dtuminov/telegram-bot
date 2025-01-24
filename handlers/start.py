from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ContextTypes

from handlers.registration import register
from init import commands, create_menu_keyboard


# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("👋 Привет! Я бот для знакомств.")

    command_list = "\n".join([f"{cmd} - {desc}" for cmd, desc in commands])
    await update.message.reply_text(f"Вам доступны следующие команды:\n{command_list}")

    await update.message.reply_text("Для начала, давай зарегистрируемся.")
    await register(update, context)
