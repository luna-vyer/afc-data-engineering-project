import json
from pathlib import Path
from src.db.connection import get_connection


def load_feedback_json(json_path: str):
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    conn = get_connection()
    cur = conn.cursor()

    for row in data:
        cur.execute("""
            INSERT INTO feedback (username, feedback_date, campaign_id, comment)
            VALUES (%s, %s, %s, %s)
        """, (
            row["username"],
            row["feedback_date"],
            row["campaign_id"],
            row["comment"]
        ))

    conn.commit()
    cur.close()
    conn.close()
