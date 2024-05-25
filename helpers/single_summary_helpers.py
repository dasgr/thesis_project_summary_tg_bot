import logging
import re
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext
from utils.telegram_client import fetch_post_text_from_link
from helpers.other_helpers import summarize_text
from helpers.menu_helpers import start
from utils.db import save_rating_to_db, store_single_text_summary, fetch_single_text_summary

# Extract text or link from the message
async def extract_text_or_link(message_text):
    input_text = message_text.strip()
    if input_text.startswith("https://t.me"):
        # Assume it's a post link and fetch the post text
        post_text = await fetch_post_text_from_link(input_text)
        return post_text, input_text
    else:
        return input_text, None

# Handle text or link summarization
async def summarize_text_command(update: Update, context: CallbackContext):
    chat_id = update.message.chat_id
    message_text = update.message.text

    if message_text.startswith('/summarize_text '):
        message_text = message_text.strip('/summarize_text ')

    original_text, post_link = await extract_text_or_link(message_text)
    text_summary = summarize_text(original_text)
    
    # Save the summary in the database
    single_text_id = store_single_text_summary(chat_id, original_text, text_summary)
    
    await send_summary_text(update, chat_id, text_summary, post_link, single_text_id)
    await send_rating_buttons(update, chat_id, single_text_id)

# Send the summarized text
async def send_summary_text(update: Update, chat_id, text_summary, post_link, single_text_id):
    if post_link:
        response_text = f"Саммари вашего текста: {text_summary}\n[Оригинал]({post_link})."
    else:
        response_text = f"Саммари вашего текста: {text_summary}"
    await update.message.reply_text(response_text, parse_mode='Markdown')

# Send rating buttons
async def send_rating_buttons(update: Update, chat_id, single_text_id):
    keyboard = [
        [InlineKeyboardButton("1", callback_data=f"rate_1_{single_text_id}")],
        [InlineKeyboardButton("2", callback_data=f"rate_2_{single_text_id}")],
        [InlineKeyboardButton("3", callback_data=f"rate_3_{single_text_id}")],
        [InlineKeyboardButton("4", callback_data=f"rate_4_{single_text_id}")],
        [InlineKeyboardButton("5", callback_data=f"rate_5_{single_text_id}")],
        [InlineKeyboardButton("Назад", callback_data="back_to_main")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Оцените качество суммаризации от 1 до 5, где 5 - идеально.", reply_markup=reply_markup)
    logging.info(f"Requested rating for summarized text for user {chat_id}. Single Text ID: {single_text_id}")

# Handle user rating
async def handle_rating(update: Update, context: CallbackContext):
    query = update.callback_query
    data = query.data
    logging.info(f"Rating received: {data}")

    if data.startswith("rate_"):
        _, rating, single_text_id = data.split("_")
        rating = int(rating)
        chat_id = query.message.chat_id
        
        # Fetch the original text and summary from the database
        original_text, summary_text = fetch_single_text_summary(single_text_id)
        
        # Save the rating to the database
        save_rating_to_db(chat_id, original_text, summary_text, rating, single_text_id)
        
        await query.answer("Спасибо за вашу оценку!")
        logging.info(f"User {chat_id} rated single text {single_text_id} with {rating}")

    await start(update, context)  # Take user back to main menu
