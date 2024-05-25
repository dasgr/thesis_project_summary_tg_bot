import psycopg2
from urllib.parse import urlparse
from utils.config import DATABASE_URL
from utils.db import get_db_connection

url = urlparse(DATABASE_URL)
dbname = url.path[1:]
user = url.username
password = url.password
host = url.hostname
port = url.port


def create_tables():
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Create tables
    cur.execute("""
    CREATE TABLE IF NOT EXISTS user_channels (
        id SERIAL PRIMARY KEY,
        chat_id BIGINT NOT NULL,
        channel_id VARCHAR(255) NOT NULL,
        added_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
        is_active BOOLEAN DEFAULT TRUE
    );
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS user_timers (
        id SERIAL PRIMARY KEY,
        chat_id BIGINT NOT NULL,
        timer TIME NOT NULL,
        timer_type VARCHAR(50),
        cron_statement VARCHAR(255)
    );
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS posts (
        id SERIAL PRIMARY KEY,
        channel_id VARCHAR(255) NOT NULL,
        post_time TIMESTAMPTZ NOT NULL,
        post_text TEXT,
        post_link TEXT,
        post_view_count INT,
        post_reactions_count INT,
        post_comment_count INT
    );
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS post_summaries (
        id SERIAL PRIMARY KEY,
        post_id INT REFERENCES posts(id),
        summary_text TEXT,
        summary_time TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
    );
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS last_sent_post (
        chat_id BIGINT NOT NULL,
        channel_id VARCHAR(255) NOT NULL,
        last_post_time TIMESTAMPTZ,
        PRIMARY KEY (chat_id, channel_id)
    );
    """)

    # Create view
    cur.execute("""
    CREATE VIEW active_channels AS
    SELECT DISTINCT channel_id
    FROM user_channels
    WHERE is_active = TRUE;
    """)

    conn.commit()
    cur.close()
    conn.close()

# Example usage
if __name__ == '__main__':
    create_tables()