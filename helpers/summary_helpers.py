from datetime import datetime, timedelta, timezone
from utils.db import fetch_user_timers, fetch_active_channels, fetch_posts_for_summary, store_summary, save_final_message, get_db_connection, fetch_channel_addition_time, fetch_summary_by_post_id
from helpers.other_helpers import summarize_text
from croniter import croniter
import logging

# Set up logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

def summarize_and_store_posts():
    logging.info("Starting summarization process.")
    user_timers = fetch_user_timers()
    now = datetime.now(timezone.utc)
    summaries_by_channel = {}

    for chat_id, cron_statement in user_timers:
        logging.debug(f"Processing user timer for chat_id: {chat_id}, cron_statement: {cron_statement}")
        try:
            cron = croniter(cron_statement, now)
            next_run_time = cron.get_next(datetime)
            summary_time = next_run_time - timedelta(minutes=10)
            logging.debug(f"Next run time: {next_run_time}, Summary time: {summary_time}")

            if now >= summary_time and now <= next_run_time - timedelta(minutes=5):
                active_channels = fetch_active_channels(chat_id)
                logging.debug(f"Active channels for chat_id {chat_id}: {active_channels}")

                for channel_id in active_channels:
                    conn = get_db_connection()
                    cur = conn.cursor()
                    cur.execute("""
                    SELECT last_post_time FROM last_sent_post
                    WHERE chat_id = %s AND channel_id = %s
                    """, (chat_id, channel_id))
                    result = cur.fetchone()
                    last_post_time = result[0] if result else None
                    cur.close()
                    conn.close()

                    if not last_post_time:
                        last_post_time = fetch_channel_addition_time(chat_id, channel_id)
                    logging.debug(f"Last post time for channel {channel_id}, chat_id {chat_id}: {last_post_time}")

                    posts = fetch_posts_for_summary(channel_id, last_post_time, last_post_time)
                    logging.debug(f"Number of posts fetched: {len(posts)}")

                    if posts:
                        last_post_time = posts[-1][1]
                        summary_texts = []

                        for post in posts:
                            post_id, post_link, post_time, post_text = post
                            
                            # Check if the summary already exists in the database
                            existing_summary = fetch_summary_by_post_id(post_id)
                            if existing_summary:
                                summary = existing_summary
                                logging.debug(f"Summary for post_id {post_id} already exists.")
                            else:
                                # Generate a new summary if it doesn't exist
                                summary = summarize_text(post_text, post_link)
                                store_summary(post_id, summary)
                                logging.debug(f"Generated and stored new summary for post_id {post_id}.")

                            summary_texts.append(summary)

                        summaries_by_channel[channel_id] = summary_texts

                current_date = now.strftime("%Y-%m-%d")
                final_message = f"Привет! Вот саммари постов из твоих каналов на {current_date}:\n\n"
                for channel_id, summaries in summaries_by_channel.items():
                    final_message += f"**Канал {channel_id}**:\n"
                    final_message += "\n".join(summaries)
                    final_message += "\n\n"

                logging.debug(f"Final message for chat_id {chat_id}: {final_message}")
                save_final_message(chat_id, final_message, next_run_time, cron_statement)

        except Exception as e:
            logging.error(f"Error processing user timer for chat_id {chat_id}: {e}")

if __name__ == '__main__':
    summarize_and_store_posts()
