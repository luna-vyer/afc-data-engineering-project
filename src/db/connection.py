import psycopg2
import os
from dotenv import load_dotenv
from pathlib import Path

# Go up to project root (src/db/connection.py → src/db → src → project root)
project_root = Path(__file__).resolve().parent.parent.parent
load_dotenv(project_root / ".env")

def get_connection():
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=os.getenv("DB_PORT", 5432),
        dbname=os.getenv("DB_NAME", "afc_db"),
        user=os.getenv("DB_USER", "afc_user"),
        password=os.getenv("DB_PASSWORD")
    )