import os
import logging
from openai import OpenAI

from core.researcher import generate_search_queries, search_duckduckgo
from core.evaluator import evaluate_idea_adaptive
from core.parser import parse_json_with_repair
from core.embedding import generate_embedding, find_similar_ideas
from core.storage import load_all_ideas, save_idea, update_idea_cluster
from core.cluster_storage import load_clusters, create_new_cluster, update_cluster, assign_ideas_to_cluster
from core.cluster_engine import determine_cluster_action
from core.synthesis import run_synthesis
from config import SIMILARITY_THRESHOLD


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)


def process_idea_background(idea_id: int, raw_idea: str):
    from core.storage import update_idea_status
    import logging

    logger = logging.getLogger(__name__)

    try:
        logger.info(f"Processing idea {idea_id}")

        result = process_idea(raw_idea)

        update_idea_status(idea_id, "completed", result)

        logger.info(f"Idea {idea_id} completed")

    except Exception as e:
        logger.error(f"Idea {idea_id} failed: {e}", exc_info=True)

        update_idea_status(idea_id, "failed", {"error": str(e)})


def process_idea(raw_idea: str, depth="balanced"):
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    # --- Research ---
    logging.info("Query Generating and Researching")
    try:
        queries = generate_search_queries(raw_idea, client)

        try:
            research_results = search_duckduckgo(queries, depth)
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Research step failed: {e}")

            research_results = []  # fallback
        logging.info("Query Generation and Researching Done ✅")
    except Exception as e:
        logging.error(f"Research step failed: {e}")
        raise

    # --- Evaluation ---
    logging.info("Evaluating Idea")
    try:
        raw_analysis = evaluate_idea_adaptive(raw_idea, research_results)
        analysis = parse_json_with_repair(raw_analysis)
        logging.info("Idea Evaluation Done ✅")
    except Exception as e:
        logging.error(f"Evaluation failed: {e}")
        raise

    # --- Embedding ---
    logging.info("Embedding")
    try:
        new_embedding = generate_embedding(raw_idea)
        logging.info("Embedding Done ✅")
    except Exception as e:
        logging.error(f"Embedding failed: {e}")
        raise

    # --- Save Idea First (get real DB-assigned ID) ---
    logging.info("Saving idea to database")
    try:
        idea_id = save_idea(
            raw_idea,
            {
                "research": research_results,
                "evaluation": analysis
            },
            new_embedding
        )
        logging.info(f"Idea saved with DB ID: {idea_id} ✅")
    except Exception as e:
        logging.error(f"DB save failed: {e}")
        raise

    # --- Similarity ---
    logging.info("Finding Similar past Ideas and loading clusters")
    try:
        past_ideas = load_all_ideas()
        similar = find_similar_ideas(new_embedding, past_ideas)

        # Exclude the idea we just saved from similarity results
        similar = [s for s in similar if s[0] != idea_id]

        matched = [s for s in similar if s[2] >= SIMILARITY_THRESHOLD]
        matched_ids = [mid for (mid, _, _) in matched]
        matched_ideas = [idea for idea in past_ideas if idea["id"] in matched_ids]
        clusters = load_clusters()
        logging.info("Similar Ideas and clusters Loaded ✅")
    except Exception as e:
        logging.error(f"Similarity/Loading failed: {e}")
        raise

    # --- Clustering Decision ---
    cluster_id = None
    try:
        decision = determine_cluster_action(
            matched_ideas=matched_ideas,
            clusters=clusters
        )
        logging.info(f"Cluster decision: {decision['action']}")
    except Exception as e:
        logging.error(f"Cluster decision failed: {e}")
        raise

    synthesis_result = None

    # --- Clustering + Synthesis ---
    if decision["action"] in ["create", "expand"]:
        new_idea_object = {
            "id": idea_id,  # Real DB ID
            "raw_idea": raw_idea,
            "analysis": {"evaluation": analysis}
        }

        if decision["action"] == "expand":
            cluster = decision["cluster"]
            cluster_ids = cluster["idea_ids"]
            context_ideas = [idea for idea in past_ideas if idea["id"] in cluster_ids]
        else:
            context_ideas = matched_ideas

        logging.info("Running Synthesis")
        try:
            synthesis_result = run_synthesis(new_idea_object, context_ideas)
            logging.info("Synthesis Done ✅")
        except Exception as e:
            logging.error(f"Synthesis failed: {e}")
            synthesis_result = None

        if synthesis_result:
            should_merge = synthesis_result.get("should_merge", False)

            if should_merge:
                try:
                    if decision["action"] == "expand":
                        cluster_id = decision["cluster_id"]

                        update_cluster({
                            "cluster_id": cluster_id,
                            "super_idea": synthesis_result.get("merged_super_idea_summary"),
                            "merge_reasoning": synthesis_result.get("merge_reasoning")
                        })

                        existing_ids = decision["cluster"]["idea_ids"]
                        assign_ideas_to_cluster(existing_ids, cluster_id)

                    else:
                        cluster_id = create_new_cluster({
                            "super_idea": synthesis_result.get("merged_super_idea_summary"),
                            "merge_reasoning": synthesis_result.get("merge_reasoning")
                        })
                        logging.info(f"Backfilling cluster {cluster_id} to ideas: {matched_ids}")  
                        assign_ideas_to_cluster(matched_ids, cluster_id)


                    logging.info(f"Cluster assigned: {cluster_id}")

                except Exception as e:
                    logging.error(f"Cluster update/create failed: {e}")
                    raise
        else:
            logging.warning("No synthesis result returned")
    else:
        logging.warning("No Similar Ideas/clusters")

    # --- Update idea with cluster and synthesis ---
    if cluster_id or synthesis_result:
        logging.info("Updating idea with cluster and synthesis data")
        try:
            update_idea_cluster(idea_id, cluster_id, synthesis_result)
            logging.info("Idea updated ✅")
        except Exception as e:
            logging.error(f"Idea update failed: {e}")
            raise

    logging.info("Pipeline completed successfully")

    return {
        "evaluation": analysis,
        "synthesis": synthesis_result,
        "cluster_decision": decision["action"]
    }