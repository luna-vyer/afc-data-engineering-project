from src.db.connection import get_connection

def create_tables():
    conn = get_connection()
    cur = conn.cursor()

    # ─────────────────────────────────────────
    # BRONZE — raw ingested data (unchanged)
    # ─────────────────────────────────────────

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

    # ─────────────────────────────────────────
    # SILVER — cleaned & enriched
    # ─────────────────────────────────────────

    cur.execute("""
    CREATE TABLE IF NOT EXISTS silver_sales (
        id SERIAL PRIMARY KEY,
        source_id INTEGER NOT NULL,
        username TEXT NOT NULL,
        sale_date DATE NOT NULL,
        country TEXT NOT NULL,
        product TEXT NOT NULL,
        quantity INTEGER NOT NULL,
        unit_price NUMERIC NOT NULL,
        total_amount_raw NUMERIC,
        total_amount_calc NUMERIC,       -- quantity * unit_price (recalculated)
        amount_discrepancy NUMERIC,      -- |raw - calc| to flag bad data
        transformed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        CONSTRAINT unique_silver_sales UNIQUE (source_id)
    );
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS silver_feedback (
        id SERIAL PRIMARY KEY,
        source_id INTEGER NOT NULL,
        username TEXT NOT NULL,
        feedback_date DATE,
        campaign_id TEXT,
        product TEXT,                    -- enriched from campaign_product join
        comment TEXT,
        sentiment_score NUMERIC,         -- filled in by sentiment analysis step
        sentiment_label TEXT,            -- 'positive', 'neutral', 'negative'
        transformed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        CONSTRAINT unique_silver_feedback UNIQUE (source_id)
    );
    """)

    # ─────────────────────────────────────────
    # GOLD — aggregated, dashboard-ready
    # ─────────────────────────────────────────

    cur.execute("""
    CREATE TABLE IF NOT EXISTS gold_sales_by_month (
        id SERIAL PRIMARY KEY,
        year INTEGER NOT NULL,
        month INTEGER NOT NULL,
        country TEXT NOT NULL,
        product TEXT NOT NULL,
        total_revenue NUMERIC,
        total_quantity BIGINT,
        avg_unit_price NUMERIC,
        num_transactions BIGINT,
        aggregated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        CONSTRAINT unique_gold_sales_month UNIQUE (year, month, country, product)
    );
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS gold_sales_by_product (
        id SERIAL PRIMARY KEY,
        product TEXT NOT NULL,
        total_revenue NUMERIC,
        total_quantity BIGINT,
        avg_unit_price NUMERIC,
        num_transactions BIGINT,
        aggregated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        CONSTRAINT unique_gold_sales_product UNIQUE (product)
    );
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS gold_feedback_by_campaign (
        id SERIAL PRIMARY KEY,
        campaign_id TEXT NOT NULL,
        product TEXT,
        feedback_count BIGINT,
        avg_sentiment_score NUMERIC,     -- NULL until sentiment analysis runs
        aggregated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        CONSTRAINT unique_gold_feedback_campaign UNIQUE (campaign_id, product)
    );
    """)

    conn.commit()
    cur.close()
    conn.close()