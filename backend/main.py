from fastapi import FastAPI
from pydantic import BaseModel
from dotenv import load_dotenv
load_dotenv()
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from core.pipeline import process_idea

# Import your evaluator
from core.evaluator import evaluate_idea_adaptive  # adjust if name differs

app = FastAPI()

class IdeaRequest(BaseModel):
    idea_text: str

@app.get("/")
def root():
    return {"message": "Idea Intelligence Engine API running"}

@app.post("/submit-idea")
def submit_idea(request: IdeaRequest):
    result = process_idea(request.idea_text)
    return result