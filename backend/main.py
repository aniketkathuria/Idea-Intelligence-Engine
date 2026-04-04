import logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)
import sys
import os

from fastapi import FastAPI
from pydantic import BaseModel
from dotenv import load_dotenv
load_dotenv()

# --- Fix import path ---
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# --- Imports ---
from core.pipeline import process_idea
from fastapi import BackgroundTasks
from core.storage import create_idea_entry, get_idea_by_id
from core.pipeline import process_idea_background

# Import your evaluator
from core.evaluator import evaluate_idea_adaptive  # adjust if name differs

app = FastAPI()

class IdeaRequest(BaseModel):
    idea_text: str

#cron establishment
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # allow all for now
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Routes ---

@app.get("/")
def root():
    logger.info("GET / called")
    return {"message": "Idea Intelligence Engine API running"}


@app.post("/submit-idea")
def submit_idea(request: IdeaRequest, background_tasks: BackgroundTasks):
    logger.info("🚀 POST /submit-idea called")
    try:
        idea_id = create_idea_entry(request.idea_text)

        background_tasks.add_task(
            process_idea_background,
            idea_id,
            request.idea_text
        )

        return {
            "status": "processing",
            "idea_id": idea_id
        }

    except Exception as e:
        logger.error(f"❌ Error in submit_idea: {e}", exc_info=True)
        return {"error": str(e)}

@app.get("/ideas")
def get_ideas():
    from core.storage import load_all_ideas
    ideas = load_all_ideas()
    print("Ideas from DB:", ideas)
    return load_all_ideas()

@app.get("/clusters")
def get_clusters():
    from core.cluster_storage import load_clusters
    return load_clusters()