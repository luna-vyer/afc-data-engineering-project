import pandas as pd
import time
import os
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




def load_campaign_products(csv_path: str):
    start_time = time.time()
    rows_inserted = 0
    rows_skipped = 0
    status = "SUCCESS"
    error_message = None

    try:
        df = pd.read_csv(csv_path)
        conn = get_connection()
        cur = conn.cursor()

        for _, row in df.iterrows():
            cur.execute("""
                INSERT INTO campaign_product (campaign_id, product)
                VALUES (%s, %s)
                ON CONFLICT (campaign_id, product) DO NOTHING
            """, (
                row["campaign_id"],
                row["product"],
            ))
            if cur.rowcount > 0:
                rows_inserted += 1
            else:
                rows_skipped += 1

        conn.commit()
        cur.close()
        conn.close()
        
    except Exception as e:
        status = "FAILED"
        error_message = str(e)

    duration = round(time.time() - start_time, 2)
    log_ingestion(csv_path, "campaign_product", rows_inserted, 0, rows_skipped, status, error_message, duration)


def load_sales(csv_path: str):
    start_time = time.time()
    rows_inserted = 0
    rows_skipped = 0
    status = "SUCCESS"
    error_message = None

    try:
        df = pd.read_csv(csv_path)
        conn = get_connection()
        cur = conn.cursor()

        for _, row in df.iterrows():
            cur.execute("""
                INSERT INTO sales (username, sale_date, country, product, quantity, unit_price, total_amount)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (
                row["username"],
                row["sale_date"],
                row["country"],
                row["product"],
                int(row["quantity"]),
                float(row["unit_price"]),
                float(row["total_amount"])
            ))
            rows_inserted += 1

        conn.commit()
        cur.close()
        conn.close()
        
    except Exception as e:
        status = "FAILED"
        error_message = str(e)

    duration = round(time.time() - start_time, 2)
    log_ingestion(csv_path, "sales", rows_inserted, 0, rows_skipped, status, error_message, duration)
