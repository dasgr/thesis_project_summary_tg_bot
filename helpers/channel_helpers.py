import logging
import re
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import CallbackContext
from utils.db import get_db_connection, fetch_active_channels
from utils.telegram_client import check_and_add_channel

def extract_channel_name(text):
    text = text.strip()
    if text.startswith('@'):
        return text
    if text.startswith('https://t.me/'):
        match = re.match(r'https://t\.me/(\w+)', text)
        if match:
            return "@" + match.group(1)
    return None

async def start_add_channel(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    message = update.message if update.message else update.callback_query.message
    keyboard = [
        [InlineKeyboardButton("В главное меню", callback_data="back_to_main")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await message.reply_text("Напишите название канала через @ или ссылку на канал. Например, @channelname или https://t.me/channelname.", reply_markup=reply_markup)
    logging.info(f"Prompted user {chat_id} to send the channel name.")

async def add_channel(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    message = update.message if update.message else update.callback_query.message
    channel_name = extract_channel_name(message.text.strip())
    logging.info(f"Received channel name from user {chat_id}: {channel_name}")

    # Check if the channel is already linked to the user
    active_channels = fetch_active_channels(chat_id)
    if channel_name in active_channels:
        keyboard = [[InlineKeyboardButton("В главное меню", callback_data="back_to_main")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await message.reply_text(f"{channel_name} уже добавлен в список ваших каналов. Саммари будет отправлено согласно установленному таймеру.", reply_markup=reply_markup)
        return

    # Add the channel if it's not already linked
    if channel_name and await check_and_add_channel(channel_name):
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
        INSERT INTO user_channels (chat_id, channel_id)
        VALUES (%s, %s)
        """, (chat_id, channel_name))
        conn.commit()
        cur.close()
        conn.close()
        
        keyboard = [[InlineKeyboardButton("В главное меню", callback_data="back_to_main")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await message.reply_text(f"Канал {channel_name} успешно добавлен и доступен для чтения.")
        await message.reply_text(f"Саммари по новым сообщениям с момента добавления канала {channel_name} будет отправлено согласно установленному таймеру.", reply_markup=reply_markup)
        logging.info(f"Channel {channel_name} successfully added for user {chat_id}.")
    else:
        keyboard = [[InlineKeyboardButton("В главное меню", callback_data="back_to_main")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await message.reply_text("Канал не существует или бот не имеет к нему доступа. Попробуйте еще раз или перейдите в меню.", reply_markup=reply_markup)
        logging.warning(f"Channel {channel_name} is not accessible for user {chat_id}.")

async def start_delete_channel(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    message = update.message if update.message else update.callback_query.message
    keyboard = [
        [InlineKeyboardButton("В главное меню", callback_data="back_to_main")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await message.reply_text("Напишите команду /delete_channel <канал> для удаления канала. Например, /delete_channel @channelname.", reply_markup=reply_markup)
    logging.info(f"Prompted user {chat_id} to send the channel name for deletion.")

async def delete_channel(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    message = update.message if update.message else update.callback_query.message
    
    # Extract the channel name from the command
    _, channel_name = message.text.split(maxsplit=1)
    channel_name = extract_channel_name(channel_name.strip())
    
    logging.info(f"Received channel name for deletion from user {chat_id}: {channel_name}")

    # Fetch active channels from the database
    active_channels = fetch_active_channels(chat_id)
    if channel_name in active_channels:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
        UPDATE user_channels
        SET is_active = FALSE
        WHERE chat_id = %s AND channel_id = %s
        """, (chat_id, channel_name))
        conn.commit()
        cur.close()
        conn.close()
        
        keyboard = [[InlineKeyboardButton("В главное меню", callback_data="back_to_main")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await message.reply_text(f"Канал {channel_name} успешно удален из списка.", reply_markup=reply_markup)
        logging.info(f"Channel {channel_name} successfully deleted for user {chat_id}.")
    else:
        keyboard = [[InlineKeyboardButton("В главное меню", callback_data="back_to_main")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await message.reply_text(f"Канал {channel_name} не найден в списке. Попробуйте еще раз или перейдите в меню.", reply_markup=reply_markup)
        logging.warning(f"Channel {channel_name} not found for user {chat_id}.")
