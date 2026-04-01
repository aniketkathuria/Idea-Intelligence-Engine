import logging
import sys
import os

from fastapi import FastAPI
from pydantic import BaseModel
from dotenv import load_dotenv



# --- Setup logging ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# --- Load env ---
load_dotenv()

# --- Fix import path ---
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# --- Imports ---
from core.pipeline import process_idea
from core.db import Base, engine
from core.evaluator import evaluate_idea_adaptive  # (kept as is)

# --- Ensure DB tables exist ---
try:
    Base.metadata.create_all(bind=engine)
    logger.info("✅ Database initialized")
except Exception as e:
    logger.error(f"❌ DB init failed: {e}")

# --- FastAPI app ---
app = FastAPI(root_path="/")

# --- Request model ---
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
def submit_idea(request: IdeaRequest):
    logger.info("🚀 POST /submit-idea called")

    try:
        logger.info(f"Input idea: {request.idea_text}")

        result = process_idea(request.idea_text)

        logger.info("✅ Idea processed successfully")
        return result

    except Exception as e:
        logger.error(f"❌ Error in /submit-idea: {e}", exc_info=True)
        return {"error": str(e)}


@app.get("/ideas")
def get_ideas():
    logger.info("📥 GET /ideas called")

    try:
        from core.storage import load_all_ideas

        ideas = load_all_ideas()

        logger.info(f"✅ Retrieved {len(ideas)} ideas")
        return ideas

    except Exception as e:
        logger.error(f"❌ Error in /ideas: {e}", exc_info=True)
        return {"error": str(e)}


@app.get("/clusters")
def get_clusters():
    logger.info("📥 GET /clusters called")

    try:
        from core.cluster_storage import load_clusters

        clusters = load_clusters()

        logger.info(f"✅ Retrieved {len(clusters)} clusters")
        return clusters

    except Exception as e:
        logger.error(f"❌ Error in /clusters: {e}", exc_info=True)
        return {"error": str(e)}
    
@app.get("/health")
def health():
    return {"status": "ok"}