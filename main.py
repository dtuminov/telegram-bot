import logging
import sqlite3
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

# Включаем логирование
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

# Создаем и подключаемся к базе данных
conn = sqlite3.connect('users.db')
cursor = conn.cursor()

# Создаем таблицу для хранения пользователей, если она не существует
cursor.execute('''
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY,
    username TEXT,
    name TEXT,
    info TEXT,
    photo TEXT,
    matches TEXT
)
''')
conn.commit()

commands = [
    ("/start", "Запустить бота"),
    ("/help", "Показать доступные команды"),
    ("/register", "Зарегистрироваться"),
    ("/profile", "Посмотреть свой профиль"),
    ("/edit_profile", "Редактировать профиль"),
    ("/find_match", "Найти совпадения")
]

def create_menu_keyboard():
    keyboard = [[command[0] for command in commands]]  # Создаем одну строку с командами
    return ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)

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

# Хэндлер для текстовой информации
async def receive_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id

    step = context.user_data.get('step')

    if context.user_data.get('registering'):
        if step == 'name':
            name = update.message.text
            context.user_data['name'] = name  # Сохраняем имя
            await update.message.reply_text("Имя сохранено. Теперь расскажите немного о себе.")
            context.user_data['step'] = 'info'  # Переходим к следующему шагу
        elif step == 'info':
            info = update.message.text
            context.user_data['info'] = info  # Сохраняем информацию об пользователе

            await update.message.reply_text("Информация сохранена. Теперь отправьте свою фотографию.")
            context.user_data['step'] = 'photo'  # Переходим к следующему шагу
    else:
        await update.message.reply_text("Сначала зарегистрируйтесь с помощью команды /register.")

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

async def show_next_match(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # Получаем список потенциальных совпадений и индекс текущего совпадения
    potential_matches = context.user_data.get('potential_matches')
    match_index = context.user_data.get('match_index', 0)

    if potential_matches and match_index < len(potential_matches):
        # Получаем текущего пользователя
        matched_user = potential_matches[match_index]
        user_photo = matched_user[4]  # Предполагаем, что фото пользователя в 5-й колонке

        # Отправляем фото пользователя
        await context.bot.send_photo(chat_id=update.message.from_user.id, photo=user_photo)

        # Увеличиваем индекс следующего совпадения
        context.user_data['match_index'] += 1

        # Предлагаем следующее действие
        await update.message.reply_text("Введите 'следующий', чтобы увидеть следующего пользователя.")
    else:
        await update.message.reply_text("Это все совпадения. Используйте команду /find_match, чтобы начать заново.")

# Указываем функцию для обработки текстовых сообщений
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if context.user_data.get('potential_matches'):
        await show_next_match(update, context)
    else:
        await update.message.reply_text("Сначала закажите поиск совпадений с помощью команды /find_match.")
    # Обрабатываем текст, либо вызываем обработчики
    if context.user_data.get('registering'):
        await receive_info(update, context)
    else:
        await update.message.reply_text("Команда не распознана. Используйте /register.")

# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("Привет! Я бот для знакомств.", reply_markup=create_menu_keyboard())

# Функция для отображения доступных команд
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    command_list = "\n".join([f"{cmd} - {desc}" for cmd, desc in commands])
    await update.message.reply_text(f"Вам доступны следующие команды:\n{command_list}")

def main() -> None:
    application = ApplicationBuilder().token("7558907076:AAHsIPc9L2zGXMDZDtTrxqH7mhr01eApt2g").build()  # Замените на ваш токен

    # Установка команд
    application.bot.set_my_commands([
        ("start", "Запустить бота"),
        ("help", "Показать доступные команды"),
        ("register", "Зарегистрироваться"),
        ("profile", "Посмотреть свой профиль"),
        ("edit_profile", "Редактировать профиль"),
        ("find_match", "Найти совпадения")
    ])

    # Обработчики команд
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("register", register))
    application.add_handler(CommandHandler("profile", profile))
    application.add_handler(CommandHandler("find_match", find_match))
    application.add_handler(MessageHandler(filters.PHOTO, receive_photo))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    # Запускаем бота
    application.run_polling()

if __name__ == '__main__':
    try:
        main()
    finally:
        conn.close()  # Закрываем соединение с базой данных при завершении