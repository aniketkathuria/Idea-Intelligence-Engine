import json
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


def save_idea(raw_text, analysis,embedding):
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