import pandas as pd
from src.db.connection import get_connection


def load_campaign_products(csv_path: str):
    df = pd.read_csv(csv_path)

    conn = get_connection()
    cur = conn.cursor()

    for _, row in df.iterrows():
        cur.execute("""
            INSERT INTO campaign_product (campaign_id, product)
            VALUES (%s, %s)
        """, (
            row["campaign_id"],
            row["product"],

        ))

    conn.commit()
    cur.close()
    conn.close()


def load_sales(csv_path: str):
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

    conn.commit()
    cur.close()
    conn.close()
