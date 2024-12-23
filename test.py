import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

# Включаем логирование
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

# Словарь для хранения пользователей
users = {}

# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("Привет! Я бот для знакомств. Напиши 'регистрация', чтобы зарегистрироваться.")

# Регистрация пользователя
async def register(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.message.from_user.id
    user_name = update.message.from_user.username

    # Добавляем пользователя в словарь, если его еще нет
    if user_id not in users:
        users[user_id] = {'username': user_name, 'matches': []}
        await update.message.reply_text(f"{user_name}, ты зарегистрирован!")
    else:
        await update.message.reply_text("Ты уже зарегистрирован!")

# Команда для поиска совпадений
async def find_match(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.message.from_user.id

    if user_id not in users:
        await update.message.reply_text("Сначала зарегистрируйся с помощью команды 'регистрация'.")
        return

    matches = [u['username'] for uid, u in users.items() if uid != user_id and uid not in users[user_id]['matches']]

    if matches:
        await update.message.reply_text("Вот потенциальные совпадения:\n" + "\n".join(matches))
    else:
        await update.message.reply_text("Пока нет совпадений.")

# Указываем функцию для обработки текстовых сообщений
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = update.message.text.lower()
    if text == 'регистрация':
        await register(update, context)
    elif text == 'найти совпадение':
        await find_match(update, context)
    else:
        await update.message.reply_text("Команда не распознана. Используй 'регистрация' или 'найти совпадение'.")

def main() -> None:
    # Замените 'YOUR_TOKEN_HERE' на токен вашего бота
    application = ApplicationBuilder().token("7558907076:AAHsIPc9L2zGXMDZDtTrxqH7mhr01eApt2g").build()

    # Обработчики команд
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    # Запускаем бота
    application.run_polling()

if __name__ == '__main__':
    main()