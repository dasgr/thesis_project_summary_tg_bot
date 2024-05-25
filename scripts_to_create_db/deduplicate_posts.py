import psycopg2
from utils.db import get_db_connection

def deduplicate_posts_table():
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Find duplicates based on channel_id and post_time
    cur.execute("""
    DELETE FROM posts
    WHERE ctid NOT IN (
        SELECT max(ctid)
        FROM posts
        GROUP BY channel_id, post_time
    );
    """)
    
    conn.commit()
    cur.close()
    conn.close()

if __name__ == "__main__":
    deduplicate_posts_table()
    print("Duplicates removed from posts table.")