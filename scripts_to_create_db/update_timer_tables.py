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

def drop_and_create_user_timers():
    conn = get_db_connection()
    cur = conn.cursor()

    # Drop the existing user_timers table
    cur.execute("DROP TABLE IF EXISTS user_timers")

    # Create the new user_timers table with chat_id as the primary key
    cur.execute("""
    CREATE TABLE user_timers (
        chat_id BIGINT PRIMARY KEY,
        timer TIME NOT NULL,
        timer_type VARCHAR(50),
        cron_statement VARCHAR(255)
    )
    """)

    conn.commit()
    cur.close()
    conn.close()

if __name__ == '__main__':
    drop_and_create_user_timers()