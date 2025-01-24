from telegram import Update
from telegram.ext import ContextTypes

from init import cursor, create_menu_keyboard


# Команда для отображения профиля
async def profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id

    cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
    user = cursor.fetchone()

    context.user_data['potential_matches'] = False

    if user:
        name = user[2]  # Имя пользователя
        course = user[3]
        course_name = user[4]
        age = user[5]
        tags = user[6]
        info = user[7]
        preferences = user[8]
        photo = user[9]
        interests = user[11]

        response_message = (f"👤 Ваш профиль:\n")
        await update.message.reply_text(response_message)
        if photo:
            await context.bot.send_photo(chat_id=user_id, photo=photo, reply_markup=create_menu_keyboard(),
                                         caption=f"{name} , {age}\n\n{course} курс, "
                                                 f" {course_name} 🎓\n\n🏷️ {tags} \n📝 {info}\n"
                                                 f"💬 Я ищу: {preferences}\n"
                                                 f"🌟 Интересы: {interests}\n")
        else:
            response_message += "Фотография: не установлена."

    else:
        await update.message.reply_text(
            "Вы еще не создали профиль. Используйте команду /register."
        )
