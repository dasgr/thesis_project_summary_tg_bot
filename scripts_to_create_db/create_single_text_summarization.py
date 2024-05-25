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

def create_tables():
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Create single_text_summaries table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS single_text_summaries (
        id SERIAL PRIMARY KEY,
        chat_id BIGINT NOT NULL,
        original_text TEXT NOT NULL,
        summary_text TEXT NOT NULL,
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
    );
    """)
    
    # Alter user_ratings table to add a foreign key to single_text_summaries
    cur.execute("""
    ALTER TABLE user_ratings
    ADD COLUMN IF NOT EXISTS single_text_id INT,
    ADD CONSTRAINT fk_single_text_summary
    FOREIGN KEY (single_text_id)
    REFERENCES single_text_summaries(id);
    """)
    
    conn.commit()
    cur.close()
    conn.close()

create_tables()
