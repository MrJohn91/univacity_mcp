import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

def get_connection():
    # Prefer PG_URL 
    pg_url = os.getenv("PG_URL")
    if pg_url:
        return psycopg2.connect(pg_url)

    # Fallback for local dev using separate vars
    return psycopg2.connect(
        host=os.getenv("PG_HOST", "localhost"),
        port=os.getenv("PG_PORT", 5432),
        database=os.getenv("PG_DB"),
        user=os.getenv("PG_USER"),
        password=os.getenv("PG_PASSWORD"),
    )