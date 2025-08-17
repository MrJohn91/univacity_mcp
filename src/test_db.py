from config import get_db_connection

try:
    conn = get_db_connection()
    with conn.cursor() as cur:
        cur.execute("SELECT 1;")
        print("Connected successfully!")
except Exception as e:
    print("Database connection failed:", e)
