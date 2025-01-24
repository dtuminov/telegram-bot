from telegram import Update
from telegram.ext import ContextTypes
from init import commands


# Функция для отображения доступных команд
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    command_list = "\n".join([f"{cmd} - {desc}" for cmd, desc in commands])
    await update.message.reply_text(f"Вам доступны следующие команды:\n{command_list}")
