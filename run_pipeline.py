from pathlib import Path
from src.db.schema import create_tables
from src.ingestion.load_csv import load_campaign_products, load_sales
from src.ingestion.load_feedback_json import load_feedback_json

def run():

    print("🔧 Creating tables...")
    create_tables()

    print("📥 Loading CSV files...")
    csv_dir = Path("data/raw/csv")

    for file in csv_dir.glob("*.csv"):
        if "campaign_product" in file.name:
            print(f"Loading {file.name}")
            load_campaign_products(str(file))

        elif "sales" in file.name:
            print(f"Loading {file.name}")
            load_sales(str(file))

    print("📥 Loading JSON feedbacks...")
    json_dir = Path("data/raw/feedbacks")

    for file in json_dir.glob("*.json"):
        print(f"Loading {file.name}")
        load_feedback_json(str(file))

    print("✅ Pipeline finished successfully")

if __name__ == "__main__":
    run()
