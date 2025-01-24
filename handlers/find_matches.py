import logging
import sqlite3
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

from handlers.profile import profile
from init import conn, cursor
from init import create_menu_keyboard


async def find_match(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.message.from_user.id

    cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
    user = cursor.fetchone()

    if user is None:
        await update.message.reply_text("Сначала зарегистрируйся с помощью команды /register.")
        return

    # Извлечь предпочтения по полу
    user_preferences = user[8]

    if user_preferences == 'Парня':
        user_preferences = 'Парень'
    elif user_preferences == 'Девушку':
        user_preferences = 'Девушка'

    # Получаем потенциальные совпадения по полу
    cursor.execute('SELECT * FROM users WHERE id != ? AND gender = ?', (user_id, user_preferences))
    potential_matches = cursor.fetchall()

    if not potential_matches:
        await update.message.reply_text("Пока нет совпадений.")
        return

    context.user_data['potential_matches'] = potential_matches
    context.user_data['match_index'] = 0

    await show_next_match(update, context)


async def show_next_match(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    potential_matches = context.user_data.get('potential_matches')
    match_index = context.user_data.get('match_index', 0)

    if potential_matches and match_index < len(potential_matches):
        matched_user = potential_matches[match_index]
        user_photo = matched_user[9]
        name = matched_user[2]
        course = matched_user[3]
        faculty_name = matched_user[4]
        age = matched_user[5]
        tags = matched_user[6]
        info = matched_user[7]
        preferences = matched_user[8]



        reply_markup = ReplyKeyboardMarkup(
            [["❤️", "💔"], ["✉️", "🚪"]],
            resize_keyboard=True,
            one_time_keyboard=True
        )

        profile_info = (
            f"Имя: {name}, {age} лет\n\n"
            f"Курс: {course} курс, {faculty_name} 🎓\n\n"
            f"🏷️ Теги: {tags}\n"
            f"📝 Информация: {info}\n"
            f"💬 Я ищу: {preferences}\n"
        )

        await context.bot.send_photo(
            chat_id=update.message.from_user.id,
            photo=user_photo,
            caption=profile_info,
            reply_markup=reply_markup
        )

        # Increase the index for the next match
        context.user_data['match_index'] += 1
    else:
        await update.message.reply_text("Это все совпадения. Используйте команду /find_match, чтобы начать заново.",
                                        reply_markup=create_menu_keyboard())


async def handle_user_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_input = update.message.text.lower()
    user_id = update.message.from_user.id

    potential_matches = context.user_data.get('potential_matches')
    match_index = context.user_data.get('match_index', 0)

    if user_input == '❤️':
        await handle_like(update, context, potential_matches, match_index, user_id)
    elif user_input == '💔':
        await handle_dislike(update, context)
    elif user_input == "✉️":
        await update.message.reply_text("Какое сообщение вы хотите отправить?")
        context.user_data['awaiting_message'] = True
    elif user_input == '🚪':
        await update.message.reply_text("Выход из режима поиска. Возвращение к вашему профилю...",
                                        reply_markup=create_menu_keyboard())
        context.user_data['potential_matches'] = False
        await profile(update, context)
    else:
        await update.message.reply_text("Нет такого варианта ответа.")


async def handle_like(update, context, potential_matches, match_index, user_id):
    if potential_matches and match_index > 0:
        liked_user_id = potential_matches[match_index - 1][0]
        cursor.execute('INSERT OR IGNORE INTO likes (user_id, liked_user_id) VALUES (?, ?)', (user_id, liked_user_id))
        conn.commit()

        await context.bot.send_message(chat_id=liked_user_id, text="Вас лайкнули!")

        my_profile_data = cursor.execute(
            'SELECT name, age, course, course_name, tags, info, preferences, photo FROM users WHERE id = ?',
            (user_id,)).fetchone()

        if my_profile_data:
            my_name, my_age, my_course, my_course_name, my_tags, my_info, my_preferences, my_photo = my_profile_data
            my_profile_info = (
                f"Имя: {my_name}, {my_age} лет\n\n"
                f"Курс: {my_course} курс, {my_course_name} 🎓\n\n"
                f"🏷️ Теги: {my_tags}\n"
                f"📝 Информация: {my_info}\n"
                f"💬 Я ищу: {my_preferences}\n"
            )

            reply_markup = ReplyKeyboardMarkup([["❤️", "💔"]], resize_keyboard=True, one_time_keyboard=True)
            await context.bot.send_photo(chat_id=liked_user_id, photo=my_photo, caption=my_profile_info,
                                         reply_markup=reply_markup)

            await check_for_match(update, context, liked_user_id)

        await show_next_match(update, context)
    else:
        await update.message.reply_text("Ошибка: не удалось обработать лайк.")


async def handle_dislike(update: Update, context: ContextTypes.DEFAULT_TYPE):
    #await update.message.reply_text("Вы дизлайкнули пользователя. Перейдем к следующему!")
    await show_next_match(update, context)


async def check_for_match(update: Update, context: ContextTypes.DEFAULT_TYPE, liked_user_id: int) -> None:
    user_id = update.message.from_user.id

    cursor.execute('SELECT liked_user_id FROM likes WHERE user_id = ? AND liked_user_id = ?', (liked_user_id, user_id))
    match_check = cursor.fetchone()

    if match_check:
        await context.bot.send_message(chat_id=user_id, text="У вас мэч! 🎉 Поздравляем!")
        await context.bot.send_message(chat_id=liked_user_id, text="У вас мэч! 🎉 Поздравляем!")


# Обработка текстовых сообщений и других введенных данных
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.message.from_user.id
    if context.user_data.get('awaiting_message'):
        user_message = update.message.text
        potential_matches = context.user_data.get('potential_matches')
        match_index = context.user_data.get('match_index', 0)

        if potential_matches and match_index > 0:
            recipient_user_id = potential_matches[match_index - 1][0]
            await context.bot.send_message(chat_id=recipient_user_id,
                                           text=f"Пользователь {update.message.from_user.username} отправил вам сообщение 📥: {user_message}")
            await update.message.reply_text("Сообщение отправлено 📤 пользователю, ждем ответа.")
            context.user_data['awaiting_message'] = False
            await show_next_match(update, context)
