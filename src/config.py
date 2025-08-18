import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

def get_connection():
    pg_url = os.getenv("PG_URL")
    if pg_url:
        return psycopg2.connect(pg_url)
    
    # fallback if PG_URL is not set
    return psycopg2.connect(
        host=os.getenv("PG_HOST", "localhost"),
        port=os.getenv("PG_PORT", 5432),
        dbname=os.getenv("PG_DB"),
        user=os.getenv("PG_USER"),
        password=os.getenv("PG_PASSWORD"),
    )