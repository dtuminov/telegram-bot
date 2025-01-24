import logging
import sqlite3

from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ContextTypes

from handlers.profile import profile
from handlers.registration import get_tag_keyboard_options, get_tag_keyboard, get_gender_keyboard, \
    get_interests_keyboard
from init import create_menu_keyboard, cursor, conn

logger = logging.getLogger(__name__)

def check_user_exists(user_id):
    cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
    return cursor.fetchone() is not None

def update_data_in_db(user_id, column_name, new_value):
    logger.info(f'Попытка обновления {column_name} пользователя. User ID: {user_id}, Новое значение: {new_value}')

    if not check_user_exists(user_id):
        logger.warning(f'Пользователь с ID {user_id} не найден.')
        return

    try:
        cursor.execute(f'UPDATE users SET {column_name} = ? WHERE id = ?', (new_value, user_id))
        conn.commit()

        if cursor.rowcount == 0:
            logger.warning(f'Данные пользователя с ID {user_id} не были обновлены.')
        else:
            logger.info(f'{column_name} пользователя с ID {user_id} обновлено на {new_value}.')

    except Exception as e:
        logger.error(f'Ошибка обновления данных пользователя: {e}')

async def edit_profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
    user = cursor.fetchone()
    if user:
        options = [['Описание', 'Предпочтения'], ['Теги', 'Фото'], ['Интересы', 'Выход']]
        reply_markup = ReplyKeyboardMarkup(options, one_time_keyboard=True, resize_keyboard=True)

        await update.message.reply_text('Что вы хотите изменить?', reply_markup=reply_markup)

        context.user_data['edit_mode'] = True
        context.user_data['user_id'] = user_id
    else:
        await update.message.reply_text(
            "Вы еще не создали профиль. Используйте команду /register."
        )

async def receive_new_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = context.user_data.get('user_id')

    if context.user_data.get('edit_mode'):
        selected_option = update.message.text

        if selected_option == 'Выход':
            context.user_data['edit_mode'] = False
            await update.message.reply_text('Вы вышли из режима редактирования.')
            await profile(update, context)
            return

        match selected_option:
            case 'Теги':
                await update.message.reply_text('Выберите новый тег:',
                                                reply_markup=await get_tag_keyboard())
                context.user_data['selected_field'] = selected_option
                return

            case 'Предпочтения':
                await update.message.reply_text('Выберите ваш предпочитаемый пол:',
                                                reply_markup=await get_gender_keyboard())
                context.user_data['selected_field'] = selected_option
                return

            case 'Описание':
                await update.message.reply_text('Введите ваше описание:')
                context.user_data['selected_field'] = selected_option
                return

            case 'Интересы':
                await update.message.reply_text('Выберите новые интересы:',
                                                reply_markup=await get_interests_keyboard())
                context.user_data['selected_field'] = selected_option
                return

            case 'Фото':
                await update.message.reply_text('Отправьте новое фото:')
                return

        new_value = update.message.text
        selected_field = context.user_data.get('selected_field')

        column_name_mapping = {
            'Описание': 'info',
            'Предпочтения': 'preferences',
            'Теги': 'tags',
            'Интересы': 'interests',
            'Фото': 'photo'
        }
        column_name = column_name_mapping.get(selected_field)

        if selected_field == 'Теги':
            selected_tag = update.message.text
            if selected_tag == "Готово":
                if 'tags' in context.user_data and context.user_data['tags']:
                    tags_new = ', '.join(['#' + tag for tag in context.user_data.get('tags', [])])
                    update_data_in_db(user_id, 'tags', tags_new)
                    await update.message.reply_text(
                        f"Ваши теги были обновлены на: {', '.join(context.user_data['tags'])}.",
                        reply_markup=create_menu_keyboard())
                    context.user_data['edit_mode'] = False
                    context.user_data.pop('selected_field', None)
                    context.user_data.pop('tags', None)
                    await profile(update, context)
                    return
                else:
                    await update.message.reply_text("Вы не выбрали теги! Пожалуйста, выберите хотя бы один тег.")
                    return

            tags = await get_tag_keyboard_options()
            if selected_tag in tags:
                if 'tags' not in context.user_data:
                    context.user_data['tags'] = []
                current_tags = context.user_data['tags']

                if selected_tag in current_tags:
                    current_tags.remove(selected_tag)
                elif len(current_tags) < 4:
                    current_tags.append(selected_tag)

                context.user_data['tags'] = current_tags
                await update.message.reply_text(
                    f"Выбранные теги: {', '.join(current_tags)}. Выберите ещё или нажмите 'Готово' для завершения.")
                return
            else:
                await update.message.reply_text("Нет такого тега, повторите попытку.")
                return

        if selected_field == 'Интересы':
            if 'interests' not in context.user_data:
                context.user_data['interests'] = []
            current_interests = context.user_data['interests']

            if new_value.lower() == 'готово':
                interests_string = ', '.join(f'#{interest}' for interest in current_interests)
                update_data_in_db(update.message.from_user.id, 'interests', interests_string)

                await update.message.reply_text(
                    f"Ваши интересы обновлены: {interests_string}. Процесс добавления интересов завершен.")
                context.user_data['interests'] = []
                await profile(update, context)
                return

            if new_value in current_interests:
                current_interests.remove(new_value)
            elif len(current_interests) < 5:
                current_interests.append(new_value)

            context.user_data['interests'] = current_interests
            await update.message.reply_text(
                f"Выбранные интересы: {', '.join(current_interests)}. Выберите ещё или напишите 'Готово', чтобы "
                f"завершить.")
            return

        if check_user_exists(user_id):
            update_data_in_db(user_id, column_name, new_value)
            await update.message.reply_text(f'Ваше поле "{selected_field}" было обновлено на: {new_value}')
            await profile(update, context)
        else:
            await update.message.reply_text('Пользователь не найден в базе данных. Пожалуйста, зарегистрируйтесь.',
                                            reply_markup=create_menu_keyboard())

        context.user_data['edit_mode'] = False
        context.user_data.pop('selected_field', None)
        return

    await update.message.reply_text('Вы не находитесь в режиме редактирования. Начните с команды /edit_profile.',
                                    reply_markup=create_menu_keyboard())

async def receive_photo_edit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id

    if context.user_data.get('edit_mode'):
        if update.message.photo:
            photo_file = update.message.photo[-1].file_id

            logger.info(f'Пользователь {user_id} обновляет фото. Новое фото: {photo_file}')
            try:
                cursor.execute('UPDATE users SET photo = ? WHERE id = ?', (photo_file, user_id))
                conn.commit()

                if cursor.rowcount > 0:
                    await update.message.reply_text("Ваше фото успешно обновлено!")
                    logger.info(f'Фото пользователя с ID {user_id} успешно обновлено в базе данных.')
                    await profile(update, context)  # Вызов функции profile после обновления фото
                else:
                    await update.message.reply_text(
                        "Не удалось обновить ваше фото. Пользователь не найден или фото не изменилось.")
                    logger.warning(f'Не удалось обновить фото для пользователя с ID {user_id} — не найдено изменений.')
            except Exception as e:
                await update.message.reply_text(
                    "Произошла ошибка при обновлении информации. Пожалуйста, повторите попытку позже.")
                logger.error(f'Ошибка обновления данных пользователя: {e}')
        else:
            await update.message.reply_text("Вы не прикрепили фото. Пожалуйста, попробуйте еще раз.")
            logger.warning(f'Попытка обновления без прикрепленного фото пользователем с ID {user_id}.')

async def get_existing_tags():
    cursor.execute('SELECT tag_name FROM tags_table')
    return [row[0] for row in cursor.fetchall()]