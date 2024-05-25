from telethon import TelegramClient
from utils.config import API_ID, API_HASH
from utils.logger import setup_logger

logger = setup_logger()

telethon_client = TelegramClient('new_heroku_session_for_bot', API_ID, API_HASH)

async def start_telethon_client():
    try:
        await telethon_client.start()
        logger.info("Telethon client started successfully using new_heroku_session.session")
    except Exception as e:
        logger.error(f"Failed to start Telethon client: {str(e)}")

async def check_and_add_channel(channel_name):
    try:
        logger.info(f"Attempting to access channel: {channel_name}")
        entity = await telethon_client.get_entity(channel_name)
        messages = await telethon_client.get_messages(entity, limit=1)
        if messages:
            logger.info(f"Channel {channel_name} is accessible and has messages.")
            return True
        logger.info(f"Channel {channel_name} has no messages.")
        return False
    except Exception as e:
        logger.error(f"Failed to access channel {channel_name}: {str(e)}")
        return False

async def fetch_post_text_from_link(post_link):
    try:
        # Extract the message ID from the post link
        message_id = int(post_link.split('/')[-1])
        
        # Extract the channel name from the post link
        channel_name = post_link.split('/')[-2]

        logger.info(f"Attempting to access channel: {channel_name} and message ID: {message_id}")
        entity = await telethon_client.get_entity(channel_name)
        messages = await telethon_client.get_messages(entity, ids=message_id)

        if messages:
            post_text = messages.message
            logger.info(f"Fetched message: {post_text}")
            return post_text

        logger.info(f"Message with ID {message_id} not found in channel {channel_name}.")
        return None
    except Exception as e:
        logger.error(f"Failed to fetch message from {post_link}: {str(e)}")
        return None

import asyncio
asyncio.get_event_loop().run_until_complete(start_telethon_client())
