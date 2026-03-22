import os
from openai import OpenAI

from core.researcher import generate_search_queries, search_duckduckgo
from core.evaluator import evaluate_idea_adaptive
from core.parser import parse_json_with_repair
from core.embedding import generate_embedding, find_similar_ideas
from core.storage import load_all_ideas, save_idea
from core.cluster_storage import load_clusters, create_new_cluster, update_cluster
from core.cluster_engine import determine_cluster_action
from core.synthesis import run_synthesis
from config import SIMILARITY_THRESHOLD


def process_idea(raw_idea: str, depth="balanced"):
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    # --- Research ---
    print("Query Generating and Researching")
    queries = generate_search_queries(raw_idea, client)
    research_results = search_duckduckgo(queries, depth)
    print("Query Generation and Researching Done ✅")

    # --- Evaluation ---
    print("Evaluating Idea")
    raw_analysis = evaluate_idea_adaptive(raw_idea, research_results)
    analysis = parse_json_with_repair(raw_analysis)
    print("Idea Evaluation Done ✅")

    # --- Embedding ---
    print("Embedding")
    new_embedding = generate_embedding(raw_idea)
    print("Embedding Done ✅")

    # --- Similarity ---
    print("Finding Similar past Ideas and loading clusters")
    past_ideas = load_all_ideas()
    similar = find_similar_ideas(new_embedding, past_ideas)
    matched = [s for s in similar if s[2] >= SIMILARITY_THRESHOLD]
    matched_ids = [idea_id for (idea_id, _, _) in matched]
    matched_ideas = [idea for idea in past_ideas if idea["id"] in matched_ids]

    # --- Clustering ---
    clusters = load_clusters()
    print("Similar Ideas and clusters Loaded ✅")   
    cluster_id = None
    
    decision = determine_cluster_action(
        new_idea_id=len(past_ideas) + 1,
        matched_ideas=matched_ideas,
        clusters=clusters
    )

    synthesis_result = None

    if decision["action"] in ["create", "expand"]:
        new_idea_object = {
            "id": len(past_ideas) + 1,
            "raw_idea": raw_idea,
            "analysis": {"evaluation": analysis}
        }

        if decision["action"] == "expand":
            cluster = decision["cluster"]
            cluster_ids = cluster["idea_ids"]
            context_ideas = [idea for idea in past_ideas if idea["id"] in cluster_ids]
        else:
            context_ideas = matched_ideas

        print("Running Synthesis")
        synthesis_result = run_synthesis(new_idea_object, context_ideas)
        print("Synthesis Done ✅")

        if synthesis_result:
            should_merge = synthesis_result.get("should_merge", False)

            if should_merge:
                if decision["action"] == "expand":
                    cluster_id = decision["cluster_id"]

                    update_cluster({
                        "cluster_id": cluster_id,
                        "super_idea": synthesis_result.get("super_idea"),
                        "merge_reasoning": synthesis_result.get("merge_reasoning")
                    })

                else:
                    cluster_id = create_new_cluster({
                        "super_idea": synthesis_result.get("super_idea"),
                        "merge_reasoning": synthesis_result.get("merge_reasoning")
                    })
    else: 
        print("No Similar Ideas/clusters")
        

    # --- Save Idea ---
    save_idea(
    raw_idea,
    {
        "research": research_results,
        "evaluation": analysis
    },
    new_embedding,
    cluster_id=cluster_id,
    synthesis_output=synthesis_result
)

    return {
        "evaluation": analysis,
        "synthesis": synthesis_result,
        "cluster_decision": decision["action"]
    }