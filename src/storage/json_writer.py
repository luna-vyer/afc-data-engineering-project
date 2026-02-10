import json
from datetime import date, datetime
from pathlib import Path

RAW_DIR = Path("data/raw/feedbacks")
RAW_DIR.mkdir(parents=True, exist_ok=True)


def serialize(obj):
    if isinstance(obj, (date, datetime)):
        return obj.isoformat()
    raise TypeError(f"Type {type(obj)} not serializable")


def write_feedbacks_raw(feedbacks: list[dict]) -> Path:
    file_path = RAW_DIR / "feedbacks_raw.json"

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(
            feedbacks,
            f,
            indent=2,
            ensure_ascii=False,
            default=serialize
        )

    return file_path
