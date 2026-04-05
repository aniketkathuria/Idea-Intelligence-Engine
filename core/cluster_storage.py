import os
import json
from datetime import datetime, UTC
from core.db import SessionLocal
from core.models import Cluster, Idea
from core.db import SessionLocal
from core.models import Idea

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
VAULT_DIR = os.path.join(BASE_DIR, "spark_vault")
CLUSTER_FILE = os.path.join(VAULT_DIR, "idea_clusters.json")




def assign_ideas_to_cluster(idea_ids, cluster_id):
    db = SessionLocal()

    for idea_id in idea_ids:
        idea = db.query(Idea).filter(Idea.id == idea_id).first()
        if idea:
            idea.cluster_id = cluster_id

    db.commit()
    db.close()

def load_clusters():
    db = SessionLocal()

    clusters = db.query(Cluster).all()

    result = []
    for cluster in clusters:
        ideas = db.query(Idea).filter(Idea.cluster_id == cluster.id).all()

        result.append({
            "cluster_id": cluster.id,
            "idea_ids": [idea.id for idea in ideas],
            "super_idea": cluster.super_idea,
            "merge_reasoning": cluster.merge_reasoning
        })

    db.close()
    return result

def initialize_cluster_storage():
    os.makedirs(VAULT_DIR, exist_ok=True)
    if not os.path.exists(CLUSTER_FILE):
        with open(CLUSTER_FILE, "w", encoding="utf-8") as f:
            json.dump([], f)

def save_clusters(clusters):
    with open(CLUSTER_FILE, "w", encoding="utf-8") as f:
        json.dump(clusters, f, indent=4)

def update_cluster(updated_cluster):
    db = SessionLocal()

    cluster = db.query(Cluster).filter(Cluster.id == updated_cluster["cluster_id"]).first()

    if cluster:
        cluster.super_idea = updated_cluster.get("super_idea", cluster.super_idea)
        cluster.merge_reasoning = updated_cluster.get("merge_reasoning", cluster.merge_reasoning)

        db.commit()

    db.close()

def create_new_cluster(cluster_data):
    db = SessionLocal()

    new_cluster = Cluster(
        #user_id=1,
        super_idea=cluster_data.get("super_idea"),
        merge_reasoning=cluster_data.get("merge_reasoning")
    )

    db.add(new_cluster)
    db.commit()
    db.refresh(new_cluster)

    db.close()
    return new_cluster.id