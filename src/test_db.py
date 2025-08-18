from dotenv import load_dotenv
import os
from psycopg2 import connect, OperationalError

# Load .env from project root
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env"))

def test_connection():
    try:
        conn = connect(
            dbname=os.getenv("PG_DB"),
            user=os.getenv("PG_USER"),
            password=os.getenv("PG_PASSWORD"),
            host=os.getenv("PG_HOST"),
            port=os.getenv("PG_PORT")
        )
        print("✅ Connected to Render Postgres!")
        conn.close()
    except OperationalError as e:
        print("❌ Connection failed:", e)

if __name__ == "__main__":
    test_connection()