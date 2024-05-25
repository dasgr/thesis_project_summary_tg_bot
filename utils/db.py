import psycopg2
from urllib.parse import urlparse
from utils.config import DATABASE_URL

url = urlparse(DATABASE_URL)
dbname = url.path[1:]
user = url.username
password = url.password
host = url.hostname
port = url.port

def get_db_connection():
    conn = psycopg2.connect(
        dbname=dbname,
        user=user,
        password=password,
        host=host,
        port=port
    )
    return conn

def fetch_user_timers():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT chat_id, cron_statement FROM user_timers")
    user_timers = cur.fetchall()
    cur.close()
    conn.close()
    return user_timers

def fetch_active_channels(chat_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
    SELECT channel_id FROM user_channels
    WHERE chat_id = %s AND is_active = TRUE
    """, (chat_id,))
    channels = cur.fetchall()
    cur.close()
    conn.close()
    return [channel[0] for channel in channels]

def fetch_posts_for_summary(channel_id, last_post_time, channel_addition_time):
    conn = get_db_connection()
    cur = conn.cursor()
    if last_post_time:
        cur.execute("""
        SELECT id, post_link, post_time, post_text FROM posts
        WHERE channel_id = %s AND post_time > %s
        """, (channel_id, last_post_time))
    else:
        cur.execute("""
        SELECT id, post_link, post_time, post_text FROM posts
        WHERE channel_id = %s AND post_time > %s
        """, (channel_id, channel_addition_time))
    posts = cur.fetchall()
    cur.close()
    conn.close()
    return posts

def fetch_channel_addition_time(chat_id, channel_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
    SELECT added_at FROM user_channels
    WHERE chat_id = %s AND channel_id = %s and is_active
    ORDER BY added_at DESC
    LIMIT 1
    """, (chat_id, channel_id))
    result = cur.fetchone()
    cur.close()
    conn.close()
    return result[0] if result else None

def update_last_summary_generation(chat_id, channel_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
    INSERT INTO last_sent_post (chat_id, channel_id, last_post_time)
    VALUES (%s, %s, NOW())
    ON CONFLICT (chat_id, channel_id) DO UPDATE
    SET last_post_time = EXCLUDED.last_post_time
    """, (chat_id, channel_id))
    conn.commit()
    cur.close()
    conn.close()

def store_summary(post_id, summary_text):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
    INSERT INTO post_summaries (post_id, summary_text)
    VALUES (%s, %s)
    """, (post_id, summary_text))
    conn.commit()
    cur.close()
    conn.close()

def save_timer_to_db(chat_id, timer, timer_type, cron_statement):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
    INSERT INTO user_timers (chat_id, timer, timer_type, cron_statement)
    VALUES (%s, %s, %s, %s)
    ON CONFLICT (chat_id) DO UPDATE SET
        timer = EXCLUDED.timer,
        timer_type = EXCLUDED.timer_type,
        cron_statement = EXCLUDED.cron_statement
    """, (chat_id, timer, timer_type, cron_statement))
    conn.commit()
    cur.close()
    conn.close()

def check_timer_in_db(chat_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT 1 FROM user_timers WHERE chat_id = %s", (chat_id,))
    result = cur.fetchone()
    cur.close()
    conn.close()
    return result is not None

def delete_timer_from_db(chat_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM user_timers WHERE chat_id = %s", (chat_id,))
    conn.commit()
    cur.close()
    conn.close()

def save_post_to_db(channel_id, post_time, post_text, post_link, post_view_count, post_reactions_count, post_comment_count):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
    INSERT INTO posts (channel_id, post_time, post_text, post_link, post_view_count, post_reactions_count, post_comment_count)
    VALUES (%s, %s, %s, %s, %s, %s, %s)
    """, (channel_id, post_time, post_text, post_link, post_view_count, post_reactions_count, post_comment_count))
    conn.commit()
    cur.close()
    conn.close()

def get_last_listener_run_time():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT last_run FROM last_listener_run_time WHERE id = 1")
    last_run = cur.fetchone()[0]
    cur.close()
    conn.close()
    return last_run

def update_last_listener_run_time():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("UPDATE last_listener_run_time SET last_run = NOW() WHERE id = 1")
    conn.commit()
    cur.close()
    conn.close()

def fetch_all_active_channels_to_listen():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT DISTINCT channel_id FROM active_channels")
    active_channels = cur.fetchall()
    conn.commit()
    cur.close()
    conn.close()
    return [channel[0] for channel in active_channels]

def save_final_message(chat_id, message, next_run_time, cron_expression):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
    INSERT INTO final_messages (chat_id, message, scheduled_time, next_run_time, cron_expression)
    VALUES (%s, %s, NOW(), %s, %s)
    ON CONFLICT (chat_id, next_run_time) DO UPDATE SET
        message = EXCLUDED.message,
        scheduled_time = EXCLUDED.scheduled_time,
        cron_expression = EXCLUDED.cron_expression
    """, (chat_id, message, next_run_time, cron_expression))
    conn.commit()
    cur.close()
    conn.close()

def fetch_final_message(chat_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
    SELECT message FROM final_messages
    WHERE chat_id = %s
    """, (chat_id,))
    result = cur.fetchone()
    cur.close()
    conn.close()
    return result[0] if result else None

def delete_final_message(chat_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
    DELETE FROM final_messages
    WHERE chat_id = %s
    """, (chat_id,))
    conn.commit()
    cur.close()
    conn.close()

def store_single_text_summary(chat_id, original_text, summary_text):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
    INSERT INTO single_text_summaries (chat_id, original_text, summary_text, created_at)
    VALUES (%s, %s, %s, NOW())
    RETURNING id
    """, (chat_id, original_text, summary_text))
    single_text_id = cur.fetchone()[0]
    conn.commit()
    cur.close()
    conn.close()
    return single_text_id

def fetch_single_text_summary(single_text_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
    SELECT original_text, summary_text FROM single_text_summaries
    WHERE id = %s
    """, (single_text_id,))
    result = cur.fetchone()
    cur.close()
    conn.close()
    return result

def save_rating_to_db(chat_id, original_text, summary_text, rating, single_text_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
    INSERT INTO user_ratings (chat_id, single_text_id, original_text, summary_text, rating, created_at)
    VALUES (%s, %s, %s, %s, %s, NOW())
    """, (chat_id, single_text_id, original_text, summary_text, rating))
    conn.commit()
    cur.close()
    conn.close()
    
def fetch_summary_by_post_id(post_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
    SELECT summary_text FROM post_summaries
    WHERE post_id = %s
    """, (post_id,))
    result = cur.fetchone()
    cur.close()
    conn.close()
    return result[0] if result else None

def fetch_final_messages():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
    SELECT chat_id, message, scheduled_time, next_run_time, cron_expression, isSent
    FROM final_messages
    WHERE isSent = FALSE
    """)
    final_messages = cur.fetchall()
    cur.close()
    conn.close()
    return final_messages

def mark_message_as_sent(chat_id, next_run_time):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
    UPDATE final_messages
    SET isSent = TRUE
    WHERE chat_id = %s and next_run_time = %s
    """, (chat_id, next_run_time))
    conn.commit()
    cur.close()
    conn.close()
