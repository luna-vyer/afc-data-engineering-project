from fastapi import FastAPI, Query
from pydantic import BaseModel
from datetime import date
from typing import List, Union, Optional
from src.storage.json_writer import write_feedbacks_raw
from src.db.connection import get_connection

app = FastAPI(title="AFC Feedback API")


# ─────────────────────────────────────────
# Models
# ─────────────────────────────────────────

class Feedback(BaseModel):
    username: str
    feedback_date: date
    campaign_id: str
    comment: str


# ─────────────────────────────────────────
# POST — ingest feedback
# ─────────────────────────────────────────

@app.post("/feedback")
def receive_feedbacks(payload: Union[Feedback, List[Feedback]]):
    if isinstance(payload, Feedback):
        feedbacks = [payload]
    else:
        feedbacks = payload

    feedback_dicts = [fb.model_dump() for fb in feedbacks]
    file_path = write_feedbacks_raw(feedback_dicts)

    return {
        "status": "stored",
        "count": len(feedbacks),
        "file": str(file_path)
    }


# ─────────────────────────────────────────
# GET — Bronze layer
# ─────────────────────────────────────────

@app.get("/data/sales")
def get_sales(limit: int = Query(50, le=500), offset: int = 0):
    """Raw sales data (Bronze)."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM sales ORDER BY id LIMIT %s OFFSET %s", (limit, offset))
    rows = cur.fetchall()
    cols = [desc[0] for desc in cur.description]
    cur.close()
    conn.close()
    return {"count": len(rows), "data": [dict(zip(cols, r)) for r in rows]}


@app.get("/data/feedback")
def get_feedback(limit: int = Query(50, le=500), offset: int = 0):
    """Raw feedback data (Bronze)."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM feedback ORDER BY id LIMIT %s OFFSET %s", (limit, offset))
    rows = cur.fetchall()
    cols = [desc[0] for desc in cur.description]
    cur.close()
    conn.close()
    return {"count": len(rows), "data": [dict(zip(cols, r)) for r in rows]}


@app.get("/data/campaign-products")
def get_campaign_products(limit: int = Query(50, le=500), offset: int = 0):
    """Raw campaign/product mapping (Bronze)."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM campaign_product ORDER BY id LIMIT %s OFFSET %s", (limit, offset))
    rows = cur.fetchall()
    cols = [desc[0] for desc in cur.description]
    cur.close()
    conn.close()
    return {"count": len(rows), "data": [dict(zip(cols, r)) for r in rows]}


# ─────────────────────────────────────────
# GET — Silver layer
# ─────────────────────────────────────────

@app.get("/data/silver/sales")
def get_silver_sales(limit: int = Query(50, le=500), offset: int = 0):
    """Cleaned sales data (Silver)."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM silver_sales ORDER BY id LIMIT %s OFFSET %s", (limit, offset))
    rows = cur.fetchall()
    cols = [desc[0] for desc in cur.description]
    cur.close()
    conn.close()
    return {"count": len(rows), "data": [dict(zip(cols, r)) for r in rows]}


@app.get("/data/silver/feedback")
def get_silver_feedback(limit: int = Query(50, le=500), offset: int = 0):
    """Cleaned and sentiment-scored feedback (Silver)."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM silver_feedback ORDER BY id LIMIT %s OFFSET %s", (limit, offset))
    rows = cur.fetchall()
    cols = [desc[0] for desc in cur.description]
    cur.close()
    conn.close()
    return {"count": len(rows), "data": [dict(zip(cols, r)) for r in rows]}


# ─────────────────────────────────────────
# GET — Gold layer
# ─────────────────────────────────────────

@app.get("/data/gold/sales-by-month")
def get_gold_sales_by_month(
    country: Optional[str] = None,
    product: Optional[str] = None,
    limit: int = Query(50, le=500),
    offset: int = 0
):
    """Aggregated sales by month/country/product (Gold)."""
    conn = get_connection()
    cur = conn.cursor()
    filters = []
    params = []
    if country:
        filters.append("country = %s")
        params.append(country)
    if product:
        filters.append("product = %s")
        params.append(product)
    where = ("WHERE " + " AND ".join(filters)) if filters else ""
    params += [limit, offset]
    cur.execute(f"SELECT * FROM gold_sales_by_month {where} ORDER BY year DESC, month DESC LIMIT %s OFFSET %s", params)
    rows = cur.fetchall()
    cols = [desc[0] for desc in cur.description]
    cur.close()
    conn.close()
    return {"count": len(rows), "data": [dict(zip(cols, r)) for r in rows]}


@app.get("/data/gold/sales-by-product")
def get_gold_sales_by_product():
    """Overall product performance (Gold)."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM gold_sales_by_product ORDER BY total_revenue DESC")
    rows = cur.fetchall()
    cols = [desc[0] for desc in cur.description]
    cur.close()
    conn.close()
    return {"count": len(rows), "data": [dict(zip(cols, r)) for r in rows]}


@app.get("/data/gold/feedback-by-campaign")
def get_gold_feedback_by_campaign():
    """Feedback and sentiment aggregated by campaign (Gold)."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM gold_feedback_by_campaign ORDER BY feedback_count DESC")
    rows = cur.fetchall()
    cols = [desc[0] for desc in cur.description]
    cur.close()
    conn.close()
    return {"count": len(rows), "data": [dict(zip(cols, r)) for r in rows]}


# ─────────────────────────────────────────
# GET — Ingestion log
# ─────────────────────────────────────────

@app.get("/data/ingestion-log")
def get_ingestion_log(limit: int = Query(20, le=200)):
    """Pipeline ingestion and transformation history."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM ingestion_log ORDER BY ingested_at DESC LIMIT %s", (limit,))
    rows = cur.fetchall()
    cols = [desc[0] for desc in cur.description]
    cur.close()
    conn.close()
    return {"count": len(rows), "data": [dict(zip(cols, r)) for r in rows]}