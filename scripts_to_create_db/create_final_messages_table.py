import psycopg2
from utils.db import get_db_connection
from datetime import datetime

def drop_initial_table():

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
    """
    DROP TABLE IF EXISTS final_messages;
    """)
    conn.commit()
    cur.close()
    conn.close()

def initialize_final_message_table():

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
    """
    CREATE TABLE IF NOT EXISTS final_messages (
    chat_id BIGINT,
    message TEXT NOT NULL,
    scheduled_time TIMESTAMPTZ NOT NULL,
    next_run_time TIMESTAMPTZ NOT NULL,
    cron_expression TEXT NOT NULL,
    isSent BOOL DEFAULT FALSE,
    PRIMARY KEY (chat_id, next_run_time)
    );
    """)
    conn.commit()
    cur.close()
    conn.close()

if __name__ == '__main__':
    drop_initial_table()
    initialize_final_message_table()

