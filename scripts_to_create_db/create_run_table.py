import psycopg2
from utils.db import get_db_connection
from datetime import datetime

def initialize_last_run_time_table():
    """Initialize the last_listener_run_time table if it doesn't exist."""
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS last_listener_run_time (
        id SERIAL PRIMARY KEY,
        last_run TIMESTAMPTZ NOT NULL
    );
    """)
    cur.execute("""
    INSERT INTO last_listener_run_time (last_run)
    SELECT NOW()
    WHERE NOT EXISTS (SELECT 1 FROM last_listener_run_time WHERE id = 1);
    """)
    conn.commit()
    cur.close()
    conn.close()

if __name__ == "__main__":
    # Initialize the table (run this only once or whenever you need to ensure the table exists)
    initialize_last_run_time_table()