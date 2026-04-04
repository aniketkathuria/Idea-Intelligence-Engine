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

def create_idea_entry(raw_idea: str):
    from core.db import SessionLocal
    from core.models import Idea

    db = SessionLocal()

    idea = Idea(
        raw_input=raw_idea,
        status="processing"
    )

    db.add(idea)
    db.commit()
    db.refresh(idea)

    db.close()

    return idea.id

def update_idea_status(idea_id: int, status: str, result: dict = None):
    from core.db import SessionLocal
    from core.models import Idea
    import json

    db = SessionLocal()

    idea = db.query(Idea).filter(Idea.id == idea_id).first()

    if not idea:
        db.close()
        return

    idea.status = status

    if result:
        idea.evaluation_json = json.dumps(result.get("evaluation"))
        idea.synthesis_output = json.dumps(result.get("synthesis"))
        idea.cluster_id = result.get("cluster_id")

    db.commit()
    db.close()

def get_idea_by_id(idea_id: int):
    from core.db import SessionLocal
    from core.models import Idea
    import json

    db = SessionLocal()

    idea = db.query(Idea).filter(Idea.id == idea_id).first()

    if not idea:
        db.close()
        return {"error": "Idea not found"}

    result = {
        "id": idea.id,
        "raw_input": idea.raw_input,
        "status": idea.status,
        "evaluation": json.loads(idea.evaluation_json) if idea.evaluation_json else None,
        "synthesis": json.loads(idea.synthesis_output) if idea.synthesis_output else None,
        "cluster_id": idea.cluster_id
    }

    db.close()
    return result