import logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)
import sys
import os
import uuid
from threading import Thread
from datetime import datetime, timedelta

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv
load_dotenv()

# In-memory job store for async /process-idea polling
_jobs: dict = {}

# --- Fix import path ---
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# --- Imports ---
from core.pipeline import process_idea, process_idea_stateless
from fastapi import BackgroundTasks
from core.storage import create_idea_entry, get_idea_by_id
from core.pipeline import process_idea_background
from core.db import Base, engine
from core.evaluator import evaluate_idea_adaptive
from typing import List, Optional, Any


Base.metadata.create_all(bind=engine)

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
    #print("Ideas from DB:", ideas)
    return load_all_ideas()

@app.get("/idea/{idea_id}")
def get_idea(idea_id: int):
    logger.info(f"GET /idea/{idea_id} called")
    return get_idea_by_id(idea_id)

@app.get("/clusters")
def get_clusters():
    from core.cluster_storage import load_clusters
    return load_clusters()

class PastIdea(BaseModel):
    id: int
    raw_idea: str
    embedding: List[float]
    analysis: dict
    cluster_id: Optional[int] = None
    synthesis: Optional[dict] = None

class ProcessIdeaRequest(BaseModel):
    raw_idea: str
    past_ideas: List[PastIdea] = []
    depth: str = "balanced"
    category: Optional[str] = None

@app.post("/process-idea")
def process_idea_endpoint(request: ProcessIdeaRequest):
    """
    Submits an idea for async processing. Returns job_id immediately.
    Client polls GET /idea-status/{job_id} every 5s for the result.
    This avoids mobile network timeouts on long-running requests (2+ minutes).
    """
    job_id = str(uuid.uuid4())
    _jobs[job_id] = {"status": "processing", "created_at": datetime.utcnow()}
    logger.info(f"POST /process-idea | job_id={job_id} | past_ideas={len(request.past_ideas)}")

    past_ideas = [idea.model_dump() for idea in request.past_ideas]
    raw_idea   = request.raw_idea
    depth      = request.depth
    category   = request.category

    def run():
        try:
            result = process_idea_stateless(
                raw_idea=raw_idea,
                past_ideas=past_ideas,
                depth=depth,
                category=category,
            )
            _jobs[job_id].update({"status": "completed", **result})
            logger.info(f"✅ job {job_id} completed")
        except Exception as e:
            _jobs[job_id].update({"status": "failed", "error": str(e)})
            logger.error(f"❌ job {job_id} failed: {e}", exc_info=True)

    Thread(target=run, daemon=True).start()

    # Clean up jobs older than 1 hour
    cutoff = datetime.utcnow() - timedelta(hours=1)
    stale = [jid for jid, j in _jobs.items() if j.get("created_at", datetime.utcnow()) < cutoff]
    for jid in stale:
        del _jobs[jid]

    return {"job_id": job_id}


@app.get("/idea-status/{job_id}")
def get_idea_status(job_id: str):
    """Poll this after POST /process-idea. Returns status: processing | completed | failed."""
    if job_id not in _jobs:
        raise HTTPException(status_code=404, detail="Job not found or expired")
    job = {k: v for k, v in _jobs[job_id].items() if k != "created_at"}
    return job


@app.on_event("startup")
def startup():
    Base.metadata.create_all(bind=engine)
