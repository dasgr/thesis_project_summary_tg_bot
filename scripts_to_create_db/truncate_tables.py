import psycopg2
from urllib.parse import urlparse
from utils.config import DATABASE_URL

# Database connection parameters
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

def truncate_tables():
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        # Truncate the tables
        cur.execute("TRUNCATE TABLE final_messages RESTART IDENTITY CASCADE;")
        cur.execute("TRUNCATE TABLE last_sent_post RESTART IDENTITY CASCADE;")
        conn.commit()
        print("Tables truncated successfully.")
    except Exception as e:
        conn.rollback()
        print(f"Error truncating tables: {e}")
    finally:
        cur.close()
        conn.close()

if __name__ == '__main__':
    truncate_tables()
