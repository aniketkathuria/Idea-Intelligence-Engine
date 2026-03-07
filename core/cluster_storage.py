import os
import json
from datetime import datetime, UTC

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
VAULT_DIR = os.path.join(BASE_DIR, "spark_vault")
CLUSTER_FILE = os.path.join(VAULT_DIR, "idea_clusters.json")

def initialize_cluster_storage():
    os.makedirs(VAULT_DIR, exist_ok=True)
    if not os.path.exists(CLUSTER_FILE):
        with open(CLUSTER_FILE, "w", encoding="utf-8") as f:
            json.dump([], f)

def load_clusters():
    with open(CLUSTER_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_clusters(clusters):
    with open(CLUSTER_FILE, "w", encoding="utf-8") as f:
        json.dump(clusters, f, indent=4)

def update_cluster(updated_cluster):
    clusters = load_clusters()
    for i, cluster in enumerate(clusters):
        if cluster["cluster_id"] == updated_cluster["cluster_id"]:
            clusters[i] = updated_cluster
            break
    save_clusters(clusters)

def create_new_cluster(cluster_data):
    clusters = load_clusters()
    cluster_data["cluster_id"] = len(clusters) + 1
    cluster_data["created_at"] = datetime.now(UTC).isoformat()
    clusters.append(cluster_data)
    save_clusters(clusters)