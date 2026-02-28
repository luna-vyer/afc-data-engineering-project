import time
from datetime import datetime
from src.db.connection import get_connection


def log_transformation(layer: str, table_name: str, rows_upserted: int, status: str, error_message: str, duration_seconds: float):
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            INSERT INTO ingestion_log
            (file_name, table_name, rows_inserted, rows_updated, rows_skipped, status, error_message, duration_seconds, ingested_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (layer, table_name, rows_upserted, 0, 0, status, error_message, duration_seconds, datetime.now()))
        conn.commit()
    except Exception as e:
        print(f"Logging failed: {e}")
        conn.rollback()
    finally:
        cur.close()
        conn.close()


def build_gold_sales_by_month():
    """
    Gold: total revenue and quantity sold, grouped by year/month, country, product.
    Ready for the sales dashboard.
    """
    start = time.time()
    status = "SUCCESS"
    error_message = None
    rows_upserted = 0

    try:
        conn = get_connection()
        cur = conn.cursor()

        cur.execute("""
            INSERT INTO gold_sales_by_month (
                year, month, country, product,
                total_revenue, total_quantity, avg_unit_price, num_transactions
            )
            SELECT
                EXTRACT(YEAR FROM sale_date)::INT AS year,
                EXTRACT(MONTH FROM sale_date)::INT AS month,
                country,
                product,
                ROUND(SUM(total_amount_calc)::NUMERIC, 2) AS total_revenue,
                SUM(quantity) AS total_quantity,
                ROUND(AVG(unit_price)::NUMERIC, 2) AS avg_unit_price,
                COUNT(*) AS num_transactions
            FROM silver_sales
            GROUP BY year, month, country, product
            ON CONFLICT (year, month, country, product) DO UPDATE SET
                total_revenue = EXCLUDED.total_revenue,
                total_quantity = EXCLUDED.total_quantity,
                avg_unit_price = EXCLUDED.avg_unit_price,
                num_transactions = EXCLUDED.num_transactions,
                aggregated_at = CURRENT_TIMESTAMP
        """)
        rows_upserted = cur.rowcount
        conn.commit()
        cur.close()
        conn.close()

    except Exception as e:
        status = "FAILED"
        error_message = str(e)
        print(f"  ❌ gold_sales_by_month failed: {e}")

    duration = round(time.time() - start, 2)
    log_transformation("gold", "gold_sales_by_month", rows_upserted, status, error_message, duration)
    return status, rows_upserted


def build_gold_sales_by_product():
    """
    Gold: overall product performance across all time.
    """
    start = time.time()
    status = "SUCCESS"
    error_message = None
    rows_upserted = 0

    try:
        conn = get_connection()
        cur = conn.cursor()

        cur.execute("""
            INSERT INTO gold_sales_by_product (
                product, total_revenue, total_quantity, avg_unit_price, num_transactions
            )
            SELECT
                product,
                ROUND(SUM(total_amount_calc)::NUMERIC, 2),
                SUM(quantity),
                ROUND(AVG(unit_price)::NUMERIC, 2),
                COUNT(*)
            FROM silver_sales
            GROUP BY product
            ON CONFLICT (product) DO UPDATE SET
                total_revenue = EXCLUDED.total_revenue,
                total_quantity = EXCLUDED.total_quantity,
                avg_unit_price = EXCLUDED.avg_unit_price,
                num_transactions = EXCLUDED.num_transactions,
                aggregated_at = CURRENT_TIMESTAMP
        """)
        rows_upserted = cur.rowcount
        conn.commit()
        cur.close()
        conn.close()

    except Exception as e:
        status = "FAILED"
        error_message = str(e)
        print(f"  ❌ gold_sales_by_product failed: {e}")

    duration = round(time.time() - start, 2)
    log_transformation("gold", "gold_sales_by_product", rows_upserted, status, error_message, duration)
    return status, rows_upserted


def build_gold_feedback_by_campaign():
    """
    Gold: feedback volume per campaign and product.
    Sentiment score column is left NULL for now — filled in after sentiment analysis step.
    """
    start = time.time()
    status = "SUCCESS"
    error_message = None
    rows_upserted = 0

    try:
        conn = get_connection()
        cur = conn.cursor()

        cur.execute("""
            INSERT INTO gold_feedback_by_campaign (
                campaign_id, product, feedback_count, avg_sentiment_score
            )
            SELECT
                campaign_id,
                product,
                COUNT(*) AS feedback_count,
                AVG(sentiment_score) AS avg_sentiment_score
            FROM silver_feedback
            GROUP BY campaign_id, product
            ON CONFLICT (campaign_id, product) DO UPDATE SET
                feedback_count = EXCLUDED.feedback_count,
                avg_sentiment_score = EXCLUDED.avg_sentiment_score,
                aggregated_at = CURRENT_TIMESTAMP
        """)
        rows_upserted = cur.rowcount
        conn.commit()
        cur.close()
        conn.close()

    except Exception as e:
        status = "FAILED"
        error_message = str(e)
        print(f"  ❌ gold_feedback_by_campaign failed: {e}")

    duration = round(time.time() - start, 2)
    log_transformation("gold", "gold_feedback_by_campaign", rows_upserted, status, error_message, duration)
    return status, rows_upserted


def run_gold():
    print("  🥇 Building gold_sales_by_month...")
    status, rows = build_gold_sales_by_month()
    print(f"     → {status} ({rows} rows)")

    print("  🥇 Building gold_sales_by_product...")
    status, rows = build_gold_sales_by_product()
    print(f"     → {status} ({rows} rows)")

    print("  🥇 Building gold_feedback_by_campaign...")
    status, rows = build_gold_feedback_by_campaign()
    print(f"     → {status} ({rows} rows)")