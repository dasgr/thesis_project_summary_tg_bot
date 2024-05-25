import asyncio
from datetime import datetime, timezone, timedelta
from utils.db import fetch_final_messages, mark_message_as_sent, fetch_active_channels, update_last_summary_generation
from croniter import croniter
from helpers.other_helpers import send_message
import logging

# Set up logging to use the new-style formatting
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

async def send_summaries():
    logging.info("Starting send_summaries function.")
    try:
        final_messages = fetch_final_messages()
        now = datetime.now(timezone.utc)

        logging.debug("Fetched final messages: {}".format(final_messages))

        for record in final_messages:
            chat_id, message, scheduled_time, next_run_time, cron_expression, is_sent = record
            logging.debug("Processing chat_id: {}, cron_expression: {}".format(chat_id, cron_expression))

            try:
                if now >= next_run_time and now < next_run_time + timedelta(minutes=4):
                    logging.debug("Current time {} is within the range of next run time for chat_id: {}".format(now, chat_id))
                    
                    # Send the final message
                    await send_message(chat_id, message)
                    logging.info("Sent final message for chat_id: {}".format(chat_id))

                    # Mark the message as sent
                    mark_message_as_sent(chat_id, next_run_time)
                    logging.info("Marked message as sent for chat_id: {}".format(chat_id))

                    channels = fetch_active_channels(chat_id)
                    for channel_id in channels:
                        update_last_summary_generation(chat_id, channel_id)
            
            except Exception as e:
                logging.error("Error processing timer for chat_id {}: {}".format(chat_id, e))

    except Exception as e:
        logging.error("Error fetching final messages: {}".format(e))

if __name__ == '__main__':
    asyncio.run(send_summaries())
