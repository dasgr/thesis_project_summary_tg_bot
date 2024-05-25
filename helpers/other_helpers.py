from telegram import Bot
from utils.config import TELEGRAM_TOKEN
from telethon.tl.types import Message
from utils.config import OPENAI_API_KEY
import logging
from openai import OpenAI


bot = Bot(token=TELEGRAM_TOKEN)

async def send_message(chat_id, text):
    max_length = 4096
    if len(text) > max_length:
        chunks = [text[i:i + max_length] for i in range(0, len(text), max_length)]
        for chunk in chunks:
            await bot.send_message(chat_id=chat_id, text=chunk, parse_mode='HTML')
    else:
        await bot.send_message(chat_id=chat_id, text=text, parse_mode='HTML')

# Function to extract reaction and comment counts from a message
def extract_reactions_and_comments(message: Message):
    # Extract reactions
    reactions = message.reactions
    reaction_counts = {}
    if reactions:
        for reaction in reactions.results:
            emoji = reaction.reaction.emoticon if hasattr(reaction.reaction, 'emoticon') else reaction.reaction.document_id
            reaction_counts[emoji] = reaction.count
    
    # Extract comments count
    comments_count = 0
    if message.replies and message.replies.comments:
        comments_count = message.replies.replies
    
    return reaction_counts, comments_count

def summarize_text(post_text, post_link=None):
    client = OpenAI(api_key=OPENAI_API_KEY)

    prompt = f"Напиши пересказ для этого текста: {post_text}. Структурируй свой ответ так, чтобы пересказ был примерно в 4 раза короче оригинального текста."
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7
        )
        summary = response.choices[0].message.content

        if post_link:
            summary_with_link = f"""{summary} <a href="{post_link}">Оригинал</a>"""
            return summary_with_link

        return summary
    except Exception as e:
        logging.error(f"Error generating summary: {e}")
        return "Error generating summary."
