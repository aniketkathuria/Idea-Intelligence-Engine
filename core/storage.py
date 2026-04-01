from core.db import SessionLocal
from core.models import Idea
import json


def save_idea(raw_text, analysis, embedding):
    db = SessionLocal()
    category = analysis["evaluation"].get("category", "unknown")

    new_idea = Idea(
        user_id=1,  # TEMP
        raw_input=raw_text,
        evaluation_json=json.dumps(analysis),
        embedding_vector=json.dumps(embedding),
        category=category
    )

    db.add(new_idea)
    db.commit()
    db.refresh(new_idea)

    real_id = new_idea.id  # DB-assigned ID
    db.close()
    return real_id


def update_idea_cluster(idea_id, cluster_id, synthesis_output):
    db = SessionLocal()

    idea = db.query(Idea).filter(Idea.id == idea_id).first()
    if idea:
        idea.cluster_id = cluster_id
        idea.synthesis_output = json.dumps(synthesis_output)
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