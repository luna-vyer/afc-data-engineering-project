import psycopg2
import os
from dotenv import load_dotenv
from pathlib import Path

parent_dir = Path(__file__).resolve().parent
grandparent_dir = parent_dir.parent
grandgrandparent_dir = grandparent_dir.parent
print(grandgrandparent_dir)


load_dotenv(f"{grandgrandparent_dir}/.env")

def get_connection():
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=os.getenv("DB_PORT", 6543),
        dbname=os.getenv("POSTGRES_DB", "afc_db"),
        user=os.getenv("POSTGRES_USER", "afc_user"),
        password=os.getenv("POSTGRES_PASSWORD")
    )