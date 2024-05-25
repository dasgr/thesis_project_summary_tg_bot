from telethon import TelegramClient, events
from helpers.other_helpers import extract_reactions_and_comments
from utils.config import API_ID, API_HASH
from utils.logger import setup_logger
from utils.db import fetch_all_active_channels_to_listen, save_post_to_db, get_last_listener_run_time, update_last_listener_run_time
from datetime import datetime, UTC
import asyncio

logger = setup_logger()
telethon_client = TelegramClient('new_heroku_session_for_listener', API_ID, API_HASH)

async def main():
    await telethon_client.start()

    async with telethon_client:
        channels = fetch_all_active_channels_to_listen()

        if not channels:
            logger.info("No active channels found.")
            return

        last_run_time = get_last_listener_run_time()
        print(last_run_time)
        
        time_now = datetime.now(UTC)
        print(time_now)

        for channel in channels:
            channel_entity = await telethon_client.get_entity(channel)
            messages = await telethon_client.get_messages(channel_entity, offset_date=time_now)

            for message in messages:
                if message.date > last_run_time:
                    post_time = message.date
                    post_text = message.message
                    post_link = f"https://t.me/{channel}/{message.id}"
                    post_view_count = message.views if message.views else 0

                    reaction_counts, comments_count = extract_reactions_and_comments(message=message)
                    
                    save_post_to_db(
                        channel_id=channel,
                        post_time=post_time,
                        post_text=post_text,
                        post_link=post_link,
                        post_view_count=post_view_count,
                        post_reactions_count=sum(reaction_counts.values()),  # Sum of all reactions
                        post_comment_count=comments_count
                    )

                # logger.info(f"Saved post from {channel} at {post_time}")

        update_last_listener_run_time()

if __name__ == '__main__':
    asyncio.run(main())
