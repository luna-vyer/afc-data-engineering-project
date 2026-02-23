import json
import time
import os
from pathlib import Path
from datetime import datetime
from src.db.connection import get_connection


def log_ingestion(file_name, table_name, rows_inserted, rows_updated, rows_skipped, status, error_message, duration_seconds):
    conn = get_connection()
    cur = conn.cursor()
    
    try:
        cur.execute("""
            INSERT INTO ingestion_log 
            (file_name, table_name, rows_inserted, rows_updated, rows_skipped, status, error_message, duration_seconds, ingested_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (os.path.basename(file_name), table_name, rows_inserted, rows_updated, rows_skipped, status, error_message, duration_seconds, datetime.now()))
        
        conn.commit()
    except Exception as e:
        print(f"Échec du logging: {e}")
        conn.rollback()
    finally:
        cur.close()
        conn.close()


def load_feedback_json(json_path: str):
    start_time = time.time()
    rows_inserted = 0
    rows_updated = 0
    rows_skipped = 0
    status = "SUCCESS"
    error_message = None

    try:
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        conn = get_connection()
        cur = conn.cursor()

        for row in data:
            cur.execute("""
                INSERT INTO feedback (username, feedback_date, campaign_id, comment)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (username, campaign_id, feedback_date)
                DO UPDATE SET comment = EXCLUDED.comment
                RETURNING (xmax = 0) AS inserted
            """, (
                row["username"],
                row["feedback_date"],
                row["campaign_id"],
                row["comment"]
            ))
            
            result = cur.fetchone()
            if result and result[0]:
                rows_inserted += 1
            elif result:
                rows_updated += 1
            else:
                rows_skipped += 1

        conn.commit()
        cur.close()
        conn.close()
        
    except Exception as e:
        status = "FAILED"
        error_message = str(e)

    duration = round(time.time() - start_time, 2)
    log_ingestion(json_path, "feedback", rows_inserted, rows_updated, rows_skipped, status, error_message, duration)
