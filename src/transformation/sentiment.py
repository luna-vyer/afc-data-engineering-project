import time
from datetime import datetime
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from src.db.connection import get_connection


def get_sentiment_label(compound_score: float) -> str:
    """Convert VADER compound score to human-readable label."""
    if compound_score >= 0.05:
        return "positive"
    elif compound_score <= -0.05:
        return "negative"
    else:
        return "neutral"


def run_sentiment_analysis():
    """
    Score all silver_feedback rows that haven't been scored yet.
    Updates sentiment_score and sentiment_label in place.
    """
    start = time.time()
    analyzer = SentimentIntensityAnalyzer()
    rows_updated = 0
    status = "SUCCESS"
    error_message = None

    try:
        conn = get_connection()
        cur = conn.cursor()

        # Fetch only unscored rows
        cur.execute("""
            SELECT id, comment
            FROM silver_feedback
            WHERE sentiment_score IS NULL AND comment IS NOT NULL
        """)
        rows = cur.fetchall()

        if not rows:
            print("  ℹ️  No unscored feedback found.")
        else:
            for row_id, comment in rows:
                scores = analyzer.polarity_scores(comment)
                compound = round(scores["compound"], 4)
                label = get_sentiment_label(compound)

                cur.execute("""
                    UPDATE silver_feedback
                    SET sentiment_score = %s, sentiment_label = %s
                    WHERE id = %s
                """, (compound, label, row_id))
                rows_updated += 1

            conn.commit()
            print(f"  ✅ Scored {rows_updated} feedback rows")

        cur.close()
        conn.close()

    except Exception as e:
        status = "FAILED"
        error_message = str(e)
        print(f"  ❌ Sentiment analysis failed: {e}")

    # Log to ingestion_log
    duration = round(time.time() - start, 2)
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO ingestion_log
            (file_name, table_name, rows_inserted, rows_updated, rows_skipped, status, error_message, duration_seconds, ingested_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, ("sentiment", "silver_feedback", 0, rows_updated, 0, status, error_message, duration, datetime.now()))
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        print(f"  Logging failed: {e}")

    return status, rows_updated