import logging
import sqlite3
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

from init import conn, cursor, create_menu_keyboard, courses


# Регистрация пользователя
async def register(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.message.from_user.id

    # Проверяем, зарегистрирован ли пользователь
    cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
    user = cursor.fetchone()

    if user is None:
        # Начинаем процесс регистрации
        await update.message.reply_text("😊 Пожалуйста, введите ваше имя.",
                                        reply_markup=ReplyKeyboardRemove())
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
            await update.message.reply_text(" Имя сохранено. Теперь выберете пол.",
                                            reply_markup=await get_gender_keyboard_yourself())
            context.user_data['step'] = 'gender'
        elif step == 'gender':
            gender = update.message.text
            if gender in ["Парень", "Девушка"]:
                context.user_data['gender'] = gender  # Сохраняем пол
                await update.message.reply_text(" Пол сохранен. Теперь расскажите, на каком курсе вы обучаетесь.")
                context.user_data['step'] = 'course'
                await update.message.reply_text("📚 Пожалуйста, введите номер курса (от 1 до 6).",
                                                reply_markup=ReplyKeyboardRemove())
            else:
                await update.message.reply_text(" Выберите из предложенного: 'Парня' или 'Девушку'.")
                return

        elif step == 'course':
            course_input = update.message.text
            try:
                course = int(course_input)  # Преобразуем введенное значение в целое число
                if 1 <= course <= 6:  # Проверяем, находится ли курс в допустимом диапазоне
                    context.user_data['course'] = course
                    await update.message.reply_text(
                        " Информация о курсе сохранена. Теперь расскажите, на каком факультете вы обучаетесь.",
                        reply_markup=await get_course())

                    context.user_data['step'] = 'course_name'
                else:
                    await update.message.reply_text(" Введите курс от 1 до 6.")
            except ValueError:
                await update.message.reply_text(" Пожалуйста, введите корректный номер курса.")
        elif step == 'course_name':
            course_name = update.message.text
            context.user_data['course_name'] = course_name
            if course_name in courses:  # Проверяем валидность выбора
                await update.message.reply_text(" Информация о курсе сохранена. Теперь расскажите, сколько вам лет.",
                                                reply_markup=ReplyKeyboardRemove())
                context.user_data['step'] = 'age'
            else:
                await update.message.reply_text(
                    " Некорректный выбор. Пожалуйста, выберите факультет из предложенных вариантов.")

        elif step == 'age':
            age_input = update.message.text
            try:
                age = int(age_input)  # Преобразуем введенное значение в целое число
                if 15 <= age <= 25:  # Проверяем, попадает ли возраст в допустимый диапазон
                    context.user_data['age'] = age
                    await update.message.reply_text(
                        " Информация о возрасте сохранена. Теперь выберите теги (от 1 до 4).",
                        reply_markup=await get_tag_keyboard())
                    context.user_data['step'] = 'tags'
                else:
                    await update.message.reply_text(" Введите возраст от 15 до 25 лет.")
            except ValueError:
                await update.message.reply_text(" Пожалуйста, введите корректный возраст.")
        elif step == 'tags':
            selected_tag = update.message.text
            if selected_tag == "Готово":
                if 'tags' in context.user_data and context.user_data['tags']:
                    await update.message.reply_text(
                        f" Выбранные теги: {', '.join(context.user_data['tags'])}. Теперь расскажите о своих "
                        f"увлечениях.",
                        reply_markup=await get_interests_keyboard())
                    context.user_data['step'] = 'interests'
                else:
                    await update.message.reply_text(" Вы не выбрали теги! Пожалуйста, выберите хотя бы один тег.")
            else:
                tags = await get_tag_keyboard_options()
                if selected_tag in tags:
                    if 'tags' not in context.user_data:
                        context.user_data['tags'] = []
                    current_tags = context.user_data['tags']

                    if selected_tag in current_tags:
                        current_tags.remove(selected_tag)  # Убрать тег, если он уже выбран
                    elif len(current_tags) < 4:
                        current_tags.append(selected_tag)  # Добавить тег, если меньше 4

                    context.user_data['tags'] = current_tags
                    await update.message.reply_text(
                        f" Выбранные теги: {', '.join(current_tags)}. Выберите ещё или нажмите 'Готово' для завершения.")
                else:
                    await update.message.reply_text(" Нет такого тега, повторите попытку.")

        elif step == 'interests':
            selected_interes = update.message.text
            if selected_interes == "Готово":
                if 'interests' in context.user_data and context.user_data['interests']:
                    await update.message.reply_text(
                        f" Выбранные интересы: {', '.join(context.user_data['interests'])}. Теперь расскажите о себе.",
                        reply_markup=ReplyKeyboardRemove())
                    context.user_data['step'] = 'info'
                else:
                    await update.message.reply_text(" Вы не выбрали интересы! Пожалуйста, выберите хотя бы один тег.")
            else:
                interests = await get_interests_keyboard_options()
                if selected_interes in interests:
                    if 'interests' not in context.user_data:
                        context.user_data['interests'] = []
                    current_interests = context.user_data['interests']

                    if selected_interes in current_interests:
                        current_interests.remove(selected_interes)  # Убрать тег, если он уже выбран
                    elif len(current_interests) < 4:
                        current_interests.append(selected_interes)  # Добавить тег, если меньше 4

                    context.user_data['interests'] = current_interests
                    await update.message.reply_text(
                        f" Выбранные интересы: {', '.join(current_interests)}. Выберите ещё или нажмите 'Готово' для "
                        f"завершения.")
                else:
                    await update.message.reply_text(" Нет такого тега, повторите попытку.")
        elif step == 'info':
            info = update.message.text
            context.user_data['info'] = info
            await update.message.reply_text(" Информация сохранена. Теперь расскажите, кого вы ищете.",
                                            reply_markup=await get_gender_keyboard())
            context.user_data['step'] = 'preferences'
        elif step == 'preferences':
            preferences = update.message.text
            if preferences in ["Парня", "Девушку"]:
                context.user_data['preferences'] = preferences
                await update.message.reply_text(" Информация сохранена. Теперь пришлите фото для вашего профиля.",
                                                reply_markup=ReplyKeyboardRemove())
                context.user_data['step'] = 'photo'
            else:
                await update.message.reply_text(" Выберите из предложенного: 'Парня' или 'Девушку'.")

    elif not context.user_data.get('registering'):
        await update.message.reply_text("❗ Сначала зарегистрируйтесь с помощью команды /register.")


async def get_interests_keyboard():
    tags = ["Спорт", "Музыка", "Путешествия", "Наука", "Искусство", "Технологии", "Кулинария", "Готово"]
    keyboard = ReplyKeyboardMarkup([[tag] for tag in tags], one_time_keyboard=True, resize_keyboard=True)
    return keyboard

async def get_interests_keyboard_options():
    return ["Спорт", "Музыка", "Путешествия", "Наука", "Искусство", "Технологии", "Кулинария", "Готово"]

async def get_tag_keyboard():
    tags = ["На_одну_ночь", "Готово"]
    keyboard = ReplyKeyboardMarkup([[tag] for tag in tags], one_time_keyboard=True, resize_keyboard=True)
    return keyboard

async def get_tag_keyboard_options():
    return ["На_одну_ночь"]


async def get_gender_keyboard():
    keyboard = ReplyKeyboardMarkup([["Парня"], ["Девушку"]], one_time_keyboard=True, resize_keyboard=True)
    return keyboard


async def get_gender_keyboard_yourself():
    keyboard = ReplyKeyboardMarkup([["Парень"], ["Девушка"]], one_time_keyboard=True, resize_keyboard=True)
    return keyboard


async def get_course():
    keyboard = ReplyKeyboardMarkup([[course] for course in courses], one_time_keyboard=False, resize_keyboard=True)
    return keyboard



# Хэндлер для получения фотографии
async def receive_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id

    if context.user_data.get('registering') and context.user_data.get('step') == 'photo':
        # Получение файла фотографии
        photo_file = update.message.photo[-1].file_id
        name = context.user_data.get('name')
        info = context.user_data.get('info')
        course = context.user_data.get('course')
        course_name = context.user_data.get('course_name')
        age = context.user_data.get('age')
        tags = ', '.join(['#' + tag for tag in context.user_data.get('tags', [])])  # Записываем теги в формате #тэг
        interests = ', '.join(
            ['#' + interes for interes in context.user_data.get('interests', [])])  # Записываем теги в формате #тэг
        preferences = context.user_data.get('preferences')
        gender = context.user_data.get('gender')

        # Сохраняем данные в БД
        cursor.execute(
            'INSERT INTO users (id, username, name, course, course_name, age, tags, info, preferences, interests, '
            'gender , photo,'
            'matches) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
            (user_id, update.message.from_user.username, name, course, course_name, age, tags, info, preferences,
             interests, gender, photo_file, '')
        )
        conn.commit()

        # Убираем флаг регистрации
        context.user_data['registering'] = False
        context.user_data['step'] = None  # Сбрасываем шаг

        await update.message.reply_text(
            "🎉 Регистрация завершена! Ваш профиль создан. Теперь вы можете использовать команду /profile."
        )
    else:
        await update.message.reply_text("⚠️ Команда не распознана. Используйте /help.")
