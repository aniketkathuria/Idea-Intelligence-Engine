# reprocess.py
import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from dotenv import load_dotenv
load_dotenv()


print("DATABASE_URL:", os.getenv("DATABASE_URL")[:50])  # print first 50 chars to confirm


from core.storage import load_all_ideas
ideas = load_all_ideas()
latest = ideas[-1]
print(latest['analysis'].keys())
print(len(latest['analysis'].get('research', [])))
"""
from core.storage import load_all_ideas, update_idea_with_result
from core.evaluator import evaluate_idea_adaptive
from core.parser import parse_json_with_repair
from core.embedding import generate_embedding, find_similar_ideas
from core.cluster_storage import load_clusters, create_new_cluster, update_cluster, assign_ideas_to_cluster
from core.cluster_engine import determine_cluster_action
from core.synthesis import run_synthesis
from config import SIMILARITY_THRESHOLD

def reprocess_all():
    ideas = load_all_ideas()
    print(f"Found {len(ideas)} ideas to reprocess")

    for idea in ideas:
        print(f"\nReprocessing idea #{idea['id']}: {idea['raw_idea'][:60]}...")

        # Pull cached research from DB
        research = idea['analysis'].get('research', [])
        if not research:
            print(f"  ⚠ No cached research found, skipping")
            continue

        # Re-run evaluation with new prompt
        print(f"  Evaluating...")
        raw_analysis = evaluate_idea_adaptive(idea['raw_idea'], research)
        analysis = parse_json_with_repair(raw_analysis)

        # Re-run embedding
        print(f"  Embedding...")
        new_embedding = generate_embedding(idea['raw_idea'])

        # Save updated evaluation
        update_idea_with_result(
            idea['id'],
            idea['raw_idea'],
            {"research": research, "evaluation": analysis},
            new_embedding
        )
        print(f"  ✅ Evaluation updated")

    # Now rerun clustering + synthesis across all ideas fresh
    print(f"\nRerunning clustering and synthesis...")
    rerun_clustering()
    print(f"\nDone.")

def rerun_clustering():
    from core.db import SessionLocal
    from core.models import Idea, Cluster

    # Clear all existing clusters and cluster assignments
    db = SessionLocal()
    db.query(Idea).update({"cluster_id": None, "synthesis_output": None})
    db.query(Cluster).delete()
    db.commit()
    db.close()
    print("  Cleared existing clusters")

    ideas = load_all_ideas()

    for idea in ideas:
        print(f"  Clustering idea #{idea['id']}...")
        new_embedding = idea['embedding']
        if not new_embedding:
            print(f"    ⚠ No embedding, skipping")
            continue

        past_ideas = load_all_ideas()
        similar = find_similar_ideas(new_embedding, past_ideas)
        similar = [s for s in similar if s[0] != idea['id']]
        matched = [s for s in similar if s[2] >= SIMILARITY_THRESHOLD]
        matched_ids = [mid for (mid, _, _) in matched]
        matched_ideas = [i for i in past_ideas if i['id'] in matched_ids]
        clusters = load_clusters()

        decision = determine_cluster_action(
            matched_ideas=matched_ideas,
            clusters=clusters
        )
        print(f"    Decision: {decision['action']}")

        if decision['action'] not in ['create', 'expand']:
            continue

        new_idea_object = {
            "id": idea['id'],
            "raw_idea": idea['raw_idea'],
            "analysis": {"evaluation": idea['analysis'].get('evaluation') or idea['analysis']}
        }

        if decision['action'] == 'expand':
            cluster = decision['cluster']
            context_ideas = [i for i in past_ideas if i['id'] in cluster['idea_ids']]
        else:
            context_ideas = matched_ideas

        synthesis_result = run_synthesis(new_idea_object, context_ideas)

        if synthesis_result and synthesis_result.get('should_merge'):
            if decision['action'] == 'expand':
                cluster_id = decision['cluster_id']
                update_cluster({
                    "cluster_id": cluster_id,
                    "super_idea": synthesis_result.get('super_idea'),
                    "merge_reasoning": synthesis_result.get('merge_reasoning')
                })
                assign_ideas_to_cluster(cluster['idea_ids'], cluster_id)
            else:
                cluster_id = create_new_cluster({
                    "super_idea": synthesis_result.get('super_idea'),
                    "merge_reasoning": synthesis_result.get('merge_reasoning')
                })
                assign_ideas_to_cluster(matched_ids, cluster_id)

            from core.storage import update_idea_cluster
            update_idea_cluster(idea['id'], cluster_id, synthesis_result)
            assign_ideas_to_cluster([idea['id']], cluster_id)
            print(f"    ✅ Clustered into cluster #{cluster_id}")
        else:
            from core.storage import update_idea_cluster
            update_idea_cluster(idea['id'], None, synthesis_result)
            print(f"    Synthesis ran but no merge")

            
if __name__ == "__main__":
    reprocess_all()

"""