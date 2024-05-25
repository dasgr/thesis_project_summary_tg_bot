import psycopg2
from utils.config import DATABASE_URL

def get_db_connection():
    conn = psycopg2.connect(DATABASE_URL)
    return conn

def create_user_ratings_table():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS user_ratings (
        id SERIAL PRIMARY KEY,
        chat_id BIGINT NOT NULL,
        original_text TEXT NOT NULL,
        summary_text TEXT NOT NULL,
        rating INTEGER NOT NULL CHECK (rating BETWEEN 1 AND 5),
        created_at TIMESTAMPTZ DEFAULT NOW()
    )
    """)
    conn.commit()
    cur.close()
    conn.close()

if __name__ == "__main__":
    create_user_ratings_table()
    print("Table user_ratings created successfully.")
