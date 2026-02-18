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
        comment TEXT
    );
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS campaign_product (
        id SERIAL PRIMARY KEY,
        campaign_id TEXT,
        product TEXT
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

    conn.commit()
    cur.close()
    conn.close()
