import time
from datetime import datetime
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from langdetect import detect, LangDetectException
from deep_translator import GoogleTranslator
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


def translate_to_english(text: str) -> str:
    """Detect language and translate to English if needed."""
    try:
        lang = detect(text)
        if lang == "en":
            return text
        translated = GoogleTranslator(source="auto", target="en").translate(text)
        return translated if translated else text
    except LangDetectException:
        return text
    except Exception:
        return text


def get_sentiment_label(compound_score: float) -> str:
    if compound_score >= 0.05:
        return "positive"
    elif compound_score <= -0.05:
        return "negative"
    else:
        return "neutral"


def build_silver_sales():
    """
    Silver sales: deduplicated, nulls removed, total_amount recalculated to catch inconsistencies.
    """
    start = time.time()
    status = "SUCCESS"
    error_message = None
    rows_upserted = 0

    try:
        conn = get_connection()
        cur = conn.cursor()

        cur.execute("""
            INSERT INTO silver_sales (
                source_id, username, sale_date, country, product,
                quantity, unit_price, total_amount_raw, total_amount_calc, amount_discrepancy
            )
            SELECT DISTINCT ON (username, sale_date, country, product, quantity, unit_price)
                id,
                TRIM(username),
                sale_date,
                TRIM(country),
                TRIM(product),
                quantity,
                unit_price,
                total_amount,
                ROUND((quantity * unit_price)::NUMERIC, 2),
                ROUND(ABS(total_amount - (quantity * unit_price))::NUMERIC, 2)
            FROM sales
            WHERE username IS NOT NULL
              AND sale_date IS NOT NULL
              AND country IS NOT NULL
              AND product IS NOT NULL
              AND quantity > 0
              AND unit_price > 0
            ORDER BY username, sale_date, country, product, quantity, unit_price, id
            ON CONFLICT (source_id) DO UPDATE SET
                username = EXCLUDED.username,
                sale_date = EXCLUDED.sale_date,
                country = EXCLUDED.country,
                product = EXCLUDED.product,
                quantity = EXCLUDED.quantity,
                unit_price = EXCLUDED.unit_price,
                total_amount_raw = EXCLUDED.total_amount_raw,
                total_amount_calc = EXCLUDED.total_amount_calc,
                amount_discrepancy = EXCLUDED.amount_discrepancy,
                transformed_at = CURRENT_TIMESTAMP
        """)
        rows_upserted = cur.rowcount
        conn.commit()
        cur.close()
        conn.close()

    except Exception as e:
        status = "FAILED"
        error_message = str(e)
        print(f"  ❌ silver_sales failed: {e}")

    duration = round(time.time() - start, 2)
    log_transformation("silver", "silver_sales", rows_upserted, status, error_message, duration)
    return status, rows_upserted


def build_silver_feedback():
    """
    Silver feedback: joined with campaign_product, translated to English, and sentiment scored.
    All enrichment happens here so Gold can aggregate directly.
    """
    start = time.time()
    status = "SUCCESS"
    error_message = None
    rows_upserted = 0
    rows_scored = 0

    try:
        analyzer = SentimentIntensityAnalyzer()
        conn = get_connection()
        cur = conn.cursor()

        # Step 1: upsert new/updated rows from bronze (without sentiment yet)
        cur.execute("""
            INSERT INTO silver_feedback (
                source_id, username, feedback_date, campaign_id, product, comment
            )
            SELECT
                f.id,
                TRIM(f.username),
                f.feedback_date,
                f.campaign_id,
                cp.product,
                TRIM(f.comment)
            FROM feedback f
            LEFT JOIN campaign_product cp ON cp.campaign_id = f.campaign_id
            WHERE f.username IS NOT NULL
              AND f.comment IS NOT NULL
              AND f.comment <> ''
            ON CONFLICT (source_id) DO UPDATE SET
                username = EXCLUDED.username,
                feedback_date = EXCLUDED.feedback_date,
                campaign_id = EXCLUDED.campaign_id,
                product = EXCLUDED.product,
                comment = EXCLUDED.comment,
                sentiment_score = NULL,
                sentiment_label = NULL,
                transformed_at = CURRENT_TIMESTAMP
        """)
        rows_upserted = cur.rowcount
        conn.commit()

        # Step 2: score all unscored rows (translate if needed, then VADER)
        cur.execute("""
            SELECT id, comment FROM silver_feedback
            WHERE sentiment_score IS NULL AND comment IS NOT NULL
        """)
        unscored = cur.fetchall()

        for row_id, comment in unscored:
            english = translate_to_english(comment)
            compound = round(analyzer.polarity_scores(english)["compound"], 4)
            label = get_sentiment_label(compound)
            cur.execute("""
                UPDATE silver_feedback
                SET sentiment_score = %s, sentiment_label = %s
                WHERE id = %s
            """, (compound, label, row_id))
            rows_scored += 1

        conn.commit()
        cur.close()
        conn.close()

        if rows_scored:
            print(f"     → scored {rows_scored} comments")

    except Exception as e:
        status = "FAILED"
        error_message = str(e)
        print(f"  ❌ silver_feedback failed: {e}")

    duration = round(time.time() - start, 2)
    log_transformation("silver", "silver_feedback", rows_upserted, status, error_message, duration)
    return status, rows_upserted


def run_silver():
    print("  🥈 Building silver_sales...")
    status, rows = build_silver_sales()
    print(f"     → {status} ({rows} rows)")

    print("  🥈 Building silver_feedback...")
    status, rows = build_silver_feedback()
    print(f"     → {status} ({rows} rows)")