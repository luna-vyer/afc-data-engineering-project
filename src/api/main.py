from fastapi import FastAPI
from pydantic import BaseModel
from datetime import date
from typing import List, Union
from src.storage.json_writer import write_feedbacks_raw

app = FastAPI(title="AFC Feedback API")

class Feedback(BaseModel):
    username: str
    feedback_date: date
    campaign_id: str
    comment: str

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
