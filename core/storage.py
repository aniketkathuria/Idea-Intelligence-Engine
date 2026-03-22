"""import json
import os
from datetime import datetime, UTC
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
VAULT_DIR = os.path.join(BASE_DIR, "spark_vault")
IDEA_FILE = os.path.join(VAULT_DIR, "ideas.json")


def initialize_storage():
    os.makedirs(VAULT_DIR, exist_ok=True)

    if not os.path.exists(IDEA_FILE):
        with open(IDEA_FILE, "w", encoding="utf-8") as f:
            json.dump([], f)


def save_idea(raw_text, analysis, embedding):
    with open(IDEA_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    entry = {
        "id": len(data) + 1,
        "timestamp": datetime.now(UTC).isoformat(),
        "raw_idea": raw_text,
        "embedding": embedding,
        "analysis": analysis
        }

    data.append(entry)

    with open(IDEA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)


def load_all_ideas():
    with open(IDEA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)
"""


from core.db import SessionLocal
from core.models import Idea
import json

def save_idea(raw_text, analysis, embedding,cluster_id,synthesis_output):
    db = SessionLocal()
    category = analysis["evaluation"].get("category", "unknown")
    new_idea = Idea(
        user_id=1,  # TEMP
        raw_input=raw_text,
        evaluation_json=json.dumps(analysis),
        embedding_vector=json.dumps(embedding),
        cluster_id=json.dumps(cluster_id),
        synthesis_output=json.dumps(synthesis_output),
        category=category
    )

    db.add(new_idea)
    db.commit()
    db.close()

def load_all_ideas():
    db = SessionLocal()

    ideas = db.query(Idea).all()

    result = []
    for idea in ideas:
        result.append({
            "id": idea.id,
            "raw_idea": idea.raw_input,
            "embedding": json.loads(idea.embedding_vector),
            "analysis": json.loads(idea.evaluation_json)
        })

    db.close()
    return result