from core.storage import initialize_storage, save_idea
from core.evaluator import evaluate_idea_adaptive
from core.researcher import generate_search_queries, search_duckduckgo
from core.parser import parse_json_with_repair
from openai import OpenAI
import os
from core.embedding import generate_embedding, find_similar_ideas
from core.storage import load_all_ideas
from core.cluster_storage import load_clusters
from core.cluster_engine import determine_cluster_action
from config import SIMILARITY_THRESHOLD
from core.cluster_storage import create_new_cluster, update_cluster
from core.synthesis import run_synthesis

def print_idea_report(analysis):
    print("\n================= IDEA REPORT =================\n")

    # --- Summary ---
    print("## SUMMARY")
    print(f"{analysis['idea_summary']}\n")

    print(f"CATEGORY: {analysis['category']}\n")

    # --- Novelty & Feasibility ---
    print("## CORE SCORES")
    print(f"Novelty: {analysis['novelty_analysis']['score']}/10")
    print("##Feasibility Breakdown:")
    print(f"  Technical: {analysis['feasibility_analysis']['technical']['score']}/10")
    print(f"  Economic: {analysis['feasibility_analysis']['economic']['score']}/10")
    print(f"  Market: {analysis['feasibility_analysis']['market']['score']}/10")
    print(f"  Execution Complexity: {analysis['feasibility_analysis']['execution_complexity']['score']}/10\n")

    # --- Landscape ---
    print("## EXISTING LANDSCAPE")

    commercial = analysis["existing_landscape_analysis"]["commercial_landscape"]

    print("\n  Commercial Players:")
    for player in commercial["existing_players"]:
        print(f"   - {player['name']} ({player['similarity_percentage']}% match)")
        print(f"     Difference: {player['key_differences']}")

    print(f"\n  Market State: {commercial['market_state']}")
    print(f"  Market Analysis: {commercial['analysis']}\n")

    print("  Conceptual Parallels:")
    for concept in analysis["existing_landscape_analysis"]["conceptual_parallels"]:
        print(f"   - {concept['concept']} ({concept['domain']})")
        print(f"     Notes: {concept['similarity_notes']}")

    positioning = analysis["existing_landscape_analysis"]["innovation_positioning"]
    print(f"\n  Innovation Position: {positioning['position']}")
    print(f"  Justification: {positioning['justification']}\n")

    # --- Upside ---
    print("## UPSIDE SCENARIO")
    upside = analysis["upside_scenario"]
    print(f"  Maximum Impact: {upside['maximum_impact']}")
    print(f"  Beneficiaries: {', '.join(upside['primary_beneficiaries'])}")
    print(f"  Industries Affected: {', '.join(upside['industries_affected'])}")
    print(f"  Realistic Scale: {upside['realistic_scale']}")
    print(f"  Impact Type: {upside['impact_type']}\n")

    # --- Risk & Structure ---
    print("## RISK & STRUCTURAL ANALYSIS")

    print("\n  Underlying Assumptions:")
    for assumption in analysis["risk_structural_analysis"]["underlying_assumptions"]:
        print(f"   - {assumption['assumption']} ({assumption['classification']})")

    print("\n  Structural Weaknesses:")
    for flaw in analysis["risk_structural_analysis"]["structural_weaknesses"]:
        print(f"   - {flaw}")

    print("\n  Failure Scenarios:")
    for failure in analysis["risk_structural_analysis"]["failure_scenarios"]:
        print(f"   - {failure}")

    print(f"\n  Most Underestimated Risk: {analysis['risk_structural_analysis']['most_underestimated_risk']}")
    print(f"  Most Fragile Stage: {analysis['risk_structural_analysis']['fragile_stage']}\n")

    # --- Improvements ---
    print("## IMPROVEMENT DIRECTIONS")

    print("\n  Strengthening Actions:")
    for action in analysis["improvement_directions"]["strengthening_actions"]:
        print(f"   - {action}")

    print("\n  Research Needed:")
    for research in analysis["improvement_directions"]["research_needed"]:
        print(f"   - {research}")

    print("\n  Cheap Validation Tests:")
    for test in analysis["improvement_directions"]["cheap_validation_tests"]:
        print(f"   - {test}")

    # --- Brutal Truth ---
    print("\n## BRUTAL TRUTH")
    print(analysis["brutal_truth"])

    # --- Meta ---
    print("\n## META SCORES")
    meta = analysis["meta_scores"]
    print(f"  Overall Score: {meta['overall_score']}/10")
    print(f"  Risk Level: {meta['risk_level']}")
    print(f"  Asymmetry Potential: {meta['asymmetry_potential']}")

    print("\n================================================\n")



def main():
    initialize_storage()

    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    print("===== IDEA INTELLIGENCE ENGINE =====")

    raw_idea = input("\nEnter your idea:\n> ")

    print("\nSelect research depth:")
    print("1 Fast")
    print("2 Balanced")
    print("3 Deep")

    depth_choice = input("> ")

    depth_map = {
        "1": "fast",
        "2": "balanced",
        "3": "deep"
    }
    depth = depth_map.get(depth_choice, "balanced")

    print("\nGenerating queries...")
    queries = generate_search_queries(raw_idea, client)

    print("Searching web...")
    research_results = search_duckduckgo(queries, depth)
    if not research_results:
        print("⚠ Warning: No research results found.")
    print("Evaluating idea...")
    raw_analysis = evaluate_idea_adaptive(raw_idea, research_results)

    analysis = parse_json_with_repair(raw_analysis)
    print(analysis)

    #print_idea_report(analysis)    
    
    print("\nGenerating embedding...")
    new_embedding = generate_embedding(raw_idea)


#############################################################################################

    print("Checking similarity with past ideas...")
    past_ideas = load_all_ideas()
    # Get top similar (already top K from embedding logic)
    similar = find_similar_ideas(new_embedding, past_ideas)
    #print("All similarity scores:")
    #for s in similar:
    #    print(s)
    # Filter by threshold
    matched = [s for s in similar if s[2] >= SIMILARITY_THRESHOLD]

    # Extract IDs
    matched_ids = [idea_id for (idea_id, _, _) in matched]

    # Convert to full idea objects
    matched_ideas = [idea for idea in past_ideas if idea["id"] in matched_ids]

    if matched:
        print("\n===== SIMILAR PAST IDEAS =====")
        for idea_id, idea_text, score in matched:
            print(f"\nIdea #{idea_id}")
            print(f"Similarity: {round(score, 3)}")
            print(f"Text: {idea_text[:100]}...")
    else:
        print("\nNo strongly similar past ideas found.")

    clusters = load_clusters()

    decision = determine_cluster_action(
        new_idea_id=len(past_ideas) + 1,
        matched_ideas= matched_ideas,
        clusters=clusters
    )

    #print("Cluster Decision:", decision)

    if decision["action"] in ["create", "expand"]:

        # Prepare new idea object (temporary, not yet saved)
        new_idea_object = {
            "id": len(past_ideas) + 1,
            "raw_idea": raw_idea,
            "analysis": {
                "evaluation": analysis
            }
        }

        # Determine context ideas
        if decision["action"] == "expand":
            cluster = decision["cluster"]
            cluster_ids = cluster["idea_ids"]
            context_ideas = [idea for idea in past_ideas if idea["id"] in cluster_ids]

        else:  # create
            context_ideas = matched_ideas

        # Run LLM synthesis
        print("\n===== STRUCTURAL SYNTHESIS =====\n")
        synthesis_result = run_synthesis(new_idea_object, context_ideas)
        print(synthesis_result)
        """
        print(f"Core Shared Theme:\n{synthesis_result['core_shared_theme']}\n")

        print("Overlap Analysis:")
        if isinstance(synthesis_result["overlap_analysis"], dict):
            for item in synthesis_result["overlap_analysis"].get("overlap_details", []):
                print(f"- Idea {item['idea_id']}: {', '.join(item['shared_elements'])}")
        else:
            print(synthesis_result["overlap_analysis"])

        print("\nDistinct Elements Per Idea:")
        for idea_id, details in synthesis_result["distinct_elements_per_idea"].items():
            print(f"- Idea {idea_id}: {details}")
        idea_Evolutionary = "Yes" if synthesis_result['are_these_evolutionary'] else "No"
        print(f"\nIs Idea Evolutionary: {idea_Evolutionary}")
        print(f"Should Merge: {synthesis_result['should_merge']}")
        print("\nMerge Reasoning:")
        #print(synthesis_result["merge_reasoning"])

        if synthesis_result.get("should_merge"):
            print("\n===== MERGED IDEA =====\n")
            print(synthesis_result["merged_super_idea_summary"])
        if synthesis_result.get("unified_evaluation"):
            print("\n===== EVALUATION of Merged Idea =====\n")
            unified = synthesis_result["unified_evaluation"]

            print(f"Novelty Estimate: {unified.get('novelty_estimate')}")
            print(f"Feasibility Estimate: {unified.get('feasibility_estimate')}")
            print(f"Key Risk: {unified.get('key_risk')}")
            print(f"Upside Potential: {unified.get('upside_potential')}")

            print("\nStrategic Recommendation:")
            print(synthesis_result["strategic_recommendation"])

            print("\nConversational Reflection:")
            print(synthesis_result["conversational_reflection"])


        if synthesis_result.get("should_merge"):

            cluster_data = {
                "idea_ids": (
                    decision["matched_ids"] + [len(past_ideas) + 1]
                    if decision["action"] == "create"
                    else cluster_ids + [len(past_ideas) + 1]
                ),
                "core_shared_theme": synthesis_result["core_shared_theme"],
                "merged_super_idea_summary": synthesis_result["merged_super_idea_summary"],
                "overlap_analysis": synthesis_result["overlap_analysis"],
                "strategic_recommendation": synthesis_result["strategic_recommendation"],
                "conversational_reflection": synthesis_result["conversational_reflection"]
            }

            if decision["action"] == "create":
                create_new_cluster(cluster_data)
                print("New cluster created with synthesis.")
            else:
                cluster_data["cluster_id"] = cluster["cluster_id"]
                cluster_data["created_at"] = cluster["created_at"]
                update_cluster(cluster_data)
                print(f"Cluster {cluster['cluster_id']} expanded with synthesis.")

        else:
            print("LLM determined ideas should not merge.")
        """

    
#################################################################################################

    save_idea(raw_idea, {
        "research": research_results,
        "evaluation": analysis
    }, new_embedding)

    print("\nSaved to Spark Vault.")


if __name__ == "__main__":
    choice = input("Hey, let's Start writing ideas (Y/N): ").strip().lower()

    if choice == "y":
        main()
        input("Have a Great and Imaginative Day :)")
    else:
        input("Alright. Come back with better ideas.") 