import os
from flask import Flask, request
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

TOKEN = '7558907076:AAHsIPc9L2zGXMDZDtTrxqH7mhr01eApt2g'  # Замените вашим токеном

app = Flask(__name__)

# Функция для обработки команды /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text('Привет! Этот бот поможет вам найти единомышленников в вашем вузе. Напишите "Я ищу", чтобы начать.')

# Функция для обработки текстовых сообщений
async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_message = update.message.text
    if user_message.lower() == "я ищу":
        await update.message.reply_text('Пожалуйста, напишите, кого вы ищете.')
    else:
        await update.message.reply_text('Спасибо! Ваш запрос будет обработан.')

# Функция для обработки webhook
@app.route('/webhook', methods=['POST'])
def webhook() -> str:
    json_update = request.get_json(force=True)
    update = Update.de_json(json_update)  # Преобразуем JSON в объект Update
    dp.process_update(update)  # Обрабатываем обновление
    return '', 200

# Настройка бота и его обработчиков
application = ApplicationBuilder().token(TOKEN).build()  # Создаем экземпляр приложения

# Добавляем обработчики
application.add_handler(CommandHandler('start', start))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))

# Запускаем приложение
if __name__ == '__main__':
    application.run_webhook(drop_pending_updates=True, port=int(os.environ.get('PORT', 8443)), url_path=TOKEN)
    app.run(host='0.0.0.0', port=5000)