from core.storage import initialize_storage, save_idea
from core.evaluator import evaluate_idea
from core.researcher import generate_search_queries, search_duckduckgo
from core.parser import parse_json_with_repair
from openai import OpenAI
import os


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
    print(depth_map)
    depth = depth_map.get(depth_choice, "balanced")

    print("\nGenerating queries...")
    queries = generate_search_queries(raw_idea, client)

    print("Searching web...")
    research_results = search_duckduckgo(queries, depth)
    print(research_results)
    if not research_results:
        print("⚠ Warning: No research results found.")
    print("Evaluating idea...")
    raw_analysis = evaluate_idea(raw_idea, research_results)

    analysis = parse_json_with_repair(raw_analysis)

    print("\n===== IDEA REPORT =====\n")
    print(f"Summary: {analysis['idea_summary']}")
    print(f"Novelty: {analysis['novelty_score']}/10")
    print(f"Feasibility: {analysis['feasibility_score']}/10")
    print("Core Flaws:")
    for flaw in analysis["core_flaws"]:
        print(f"- {flaw}")

    print("\nHidden Assumptions:")
    for assumption in analysis["hidden_assumptions"]:
        print(f"- {assumption}")

    print("\nImprovement Directions:")
    for direction in analysis["improvement_directions"]:
        print(f"- {direction}")

    print(f"Brutal Truth: {analysis['brutal_truth']}")

    save_idea(raw_idea, {
        "research": research_results,
        "evaluation": analysis
    })

    print("\nSaved to Spark Vault.")


if __name__ == "__main__":
    true = input("Hey, let's Start writing ideas(Y/N):")
    main()
    true = input("Have a Great and Imaginative Day :)")