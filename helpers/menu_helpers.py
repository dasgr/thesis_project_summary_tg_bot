import logging
import re
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext
import datetime
from datetime import timedelta
from helpers.channel_helpers import start_add_channel, start_delete_channel
from utils.db import save_timer_to_db, delete_timer_from_db, check_timer_in_db

# Helper function to extract channel name
def extract_channel_name(text):
    text = text.strip()
    if text.startswith('@'):
        return text
    if text.startswith('https://t.me/'):
        match = re.match(r'https://t\.me/(\w+)', text)
        if match:
            return "@" + match.group(1)
    return None

# Start function to display the main menu
async def start(update: Update, context: CallbackContext) -> None:
    message = update.message if update.message else update.callback_query.message
    keyboard = [
        [InlineKeyboardButton("Как работает этот бот? 🤔", callback_data="about_bot")],
        [InlineKeyboardButton("Что умеет этот бот? 💡", callback_data="help_menu")],
        [InlineKeyboardButton("Таймер для саммари ⏰", callback_data="set_timer")],
        [InlineKeyboardButton("Удалить таймер ❌", callback_data="remove_timer")],
        [InlineKeyboardButton("Добавить канал 📝", callback_data='channel_add_start')],
        [InlineKeyboardButton("Удалить канал 🗑️", callback_data='channel_delete_start')],
        [InlineKeyboardButton("Сделать саммари ✍️", callback_data="summarize_text_start")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await message.reply_text('Выберите действие:', reply_markup=reply_markup)
    logging.info("Displayed start menu.")

# Handle menu selection from callback queries
async def handle_menu_selection(update: Update, context: CallbackContext):
    query = update.callback_query
    data = query.data
    logging.info(f"Menu selection: {data}")

    await query.answer()

    if data == "about_bot":
        await query.edit_message_text(text="Этот бот делает саммари из постов, используя модель GPT-3.5. "
                                           "Больше о его функциях можно узнать в меню.")
        keyboard = [[InlineKeyboardButton("Назад", callback_data="back_to_main")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.message.reply_text("Чтобы вернуться в меню, нажмите на кнопку:", reply_markup=reply_markup)
    elif data == "set_timer":
        await new_summary_timer(update, context)
    elif data == "remove_timer":
        await remove_timer(update, context)
    elif data == "summarize_text_start":
        await start_summarize_text(update, context)
    elif data == "back_to_main":
        await start(update, context)
    elif data.startswith("new_set"):
        await handle_default_timer_setting(update, context)
    elif data == "channel_add_start":
        await start_add_channel(update, context)
    elif data == "channel_delete_start":
        await start_delete_channel(update, context)
    elif data == "help_menu":
        await help_menu(update, context)
    elif data == "confirm_remove_timer":
        await confirm_remove_timer(update, context)
    elif data == 'cancel_remove_timer':
        await cancel_remove_timer(update, context)

# Display timer selection menu
async def new_summary_timer(update: Update, context: CallbackContext):
    message = update.message if update.message else update.callback_query.message
    keyboard = [
        [InlineKeyboardButton("🕘 9:00", callback_data="new_set_09:00"),
         InlineKeyboardButton("🕛 12:00", callback_data="new_set_12:00")],
        [InlineKeyboardButton("🕕 18:00", callback_data="new_set_18:00"),
         InlineKeyboardButton("🕘 21:00", callback_data="new_set_21:00")],
        [InlineKeyboardButton("Я хочу другое время!", callback_data="new_set_custom_time")],
        [InlineKeyboardButton("Меню", callback_data="back_to_main")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await message.reply_text('Когда вы хотите получать сводку новостей из своих телеграм каналов? Выберите один из предложенных вариантов по часовому поясу Москвы или задайте свой:', reply_markup=reply_markup)
    logging.info("Displayed timer selection menu.")

# Handle setting default timer
async def handle_default_timer_setting(update: Update, context: CallbackContext):
    query = update.callback_query
    data = query.data
    logging.info(f"Default timer setting: {data}")

    await query.answer()

    if data == "new_set_custom_time":
        await query.edit_message_text(
            text='Отправьте сообщение в формате "ЧЧ:ММ", чтобы установить таймер на любое время по Москве.'
        )
    else:
        _, _, time = data.split("_")
        timer = datetime.datetime.strptime(time, '%H:%M')
        timer = timer - timedelta(hours=3)
        timer = timer.time()
        cron_expression = f"{timer.minute} {timer.hour} * * *"
        chat_id = query.message.chat_id

        save_timer_to_db(chat_id, timer, 'predefined', cron_expression)

        await query.edit_message_text(text=f"Сообщения с саммари будут приходить в {time} по московскому времени.")
        logging.info(f"Timer set for user {chat_id} at {time}.")
        await start(update, context)

# Handle custom timer input
async def handle_custom_timer_input(update: Update, context: CallbackContext):
    message = update.message if update.message else update.callback_query.message
    custom_time = message.text.strip()
    try:
        timer = datetime.datetime.strptime(custom_time, '%H:%M')
        timer = timer - timedelta(hours=3)
        timer = timer.time()
        cron_expression = f"{timer.minute} {timer.hour} * * *"
        chat_id = update.effective_chat.id

        save_timer_to_db(chat_id, timer, 'custom', cron_expression)

        await message.reply_text(f"Сообщения с саммари будут приходить в {custom_time} по московскому времени.")
        logging.info(f"Custom timer set for user {chat_id} at {custom_time}.")
        await start(update, context)
    except ValueError:
        keyboard = [
            [InlineKeyboardButton("К предложенным значениям ⏰", callback_data="set_timer")],
            [InlineKeyboardButton("В главное меню", callback_data="back_to_main")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await message.reply_text(
            'Неправильный формат времени. Отправьте время в формате "ЧЧ:ММ" (24-часовой формат).',
            reply_markup=reply_markup
        )

# Handle timer removal
async def remove_timer(update: Update, context: CallbackContext):
    query = update.callback_query
    chat_id = query.message.chat_id

    if check_timer_in_db(chat_id):
        keyboard = [
            [InlineKeyboardButton("Да", callback_data="confirm_remove_timer")],
            [InlineKeyboardButton("Нет, вернуться в меню", callback_data="cancel_remove_timer")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text="У вас есть активный таймер. Вы хотите его удалить?", reply_markup=reply_markup)
    else:
        keyboard = [
            [InlineKeyboardButton("Установить таймер", callback_data="set_timer")],
            [InlineKeyboardButton("Главное меню", callback_data="back_to_main")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text="У вас нет активных таймеров.", reply_markup=reply_markup)

# Confirm timer removal
async def confirm_remove_timer(update: Update, context: CallbackContext):
    query = update.callback_query
    chat_id = query.message.chat_id

    delete_timer_from_db(chat_id)
    await query.edit_message_text(text="Ваш таймер был удален.")
    logging.info(f"Timer removed for user {chat_id}.")
    await start(update, context)

# Cancel timer removal
async def cancel_remove_timer(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.edit_message_text(text="Удаление таймера отменено.")
    await start(update, context)

# Status command handler
async def status(update: Update, context: CallbackContext) -> None:
    message = update.message if update.message else update.callback_query.message
    await message.reply_text('OK')

async def help_menu(update: Update, context: CallbackContext):
    message = update.message if update.message else update.callback_query.message
    help_text = (
        "Основные действия:\n"
        "- Отправьте время в формате 'ЧЧ:ММ' для установки пользовательского таймера для получения саммари\n"
        "- Отправьте @channelname или ссылку на канал для добавления канала для получения саммари по таймеру\n"
        "- Отправьте ссылку на пост в формате 'https://t.me/channelname/postID' для саммари поста\n"
        "Описание кнопок меню:\n"
        "Как работает этот бот? 🤔 - На чем работает суммаризация.\n"
        "Что умеет этот бот? 💡 - Показать это сообщение.\n"
        "Таймер для саммари ⏰ - Установить таймер для регулярного получения саммари. Можно выбрать предопределенные значения.\n"
        "Удалить таймер ❌ - Удалить установленный таймер.\n"
        "Добавить канал 📝 - Добавить канал для получения саммари.\n"
        "Удалить канал 🗑️ - Удалить канал из списка мониторинга.\n"
        "Сделать саммари ✍️ - Начать процесс суммирования текста или поста.\n"
        "Список прямых команд:\n"
        "/start - Запуск бота и отображение главного меню\n"
        "/delete_channel <канал> - Удалить канал из мониторинга и отправки саммари по таймер\n"
        "/remove_timer - Удалить активный таймер\n"
        "/summarize_text <текст> - Получить саммари текста\n"
        "/status - Проверка работоспособности бота\n"
        "/help - Показать это сообщение"
    )
    await message.reply_text(help_text)
    logging.info("Displayed help menu.")


# Start summarize text handler
async def start_summarize_text(update: Update, context: CallbackContext):
    message = update.message if update.message else update.callback_query.message
    text = "Чтобы оценить качество суммаризации на примере одного текста напишите команду /summarize_text 'Ваш текст' или отправьте ссылку на пост в телеграм."
    keyboard = [
        [InlineKeyboardButton("Назад", callback_data="back_to_main")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await message.reply_text(text, reply_markup=reply_markup)
    logging.info("Displayed summarize text instructions.")
