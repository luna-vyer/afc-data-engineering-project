from src.db.connection import get_connection

def create_tables():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS feedback (
        id SERIAL PRIMARY KEY,
        username TEXT,
        feedback_date DATE,
        campaign_id TEXT,
        comment TEXT,
        CONSTRAINT unique_feedback UNIQUE (username, campaign_id, feedback_date)
    );
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS campaign_product (
        id SERIAL PRIMARY KEY,
        campaign_id TEXT,
        product TEXT,
        CONSTRAINT unique_campaign_product UNIQUE (campaign_id, product)
    );
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS sales (
        id SERIAL PRIMARY KEY,
        username TEXT,
        sale_date DATE,
        country TEXT,
        product TEXT,
        quantity INTEGER,
        unit_price NUMERIC,
        total_amount NUMERIC
        
    );
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS ingestion_log (
        id SERIAL PRIMARY KEY,
        file_name TEXT,
        table_name TEXT,
        rows_inserted INTEGER,
        rows_updated INTEGER,
        rows_skipped INTEGER,
        status TEXT,
        error_message TEXT,
        duration_seconds NUMERIC,
        ingested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    conn.commit()
    cur.close()
    conn.close()
