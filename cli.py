from core.storage import initialize_storage, save_idea
from core.evaluator import evaluate_idea
from core.parser import parse_json_with_repair



def main():
    initialize_storage()

    print("===== IDEA INTELLIGENCE ENGINE =====")
    print("Enter your raw idea below:\n")

    raw_idea = input("> ")

    print("\nAnalyzing...\n")

    raw_analysis = evaluate_idea(raw_idea)
    analysis = parse_json_with_repair(raw_analysis)

    print("===== IDEA REPORT =====\n")

    print(f"Summary:\n{analysis['idea_summary']}\n")
    print(f"Category: {analysis['category']}")
    print(f"Novelty Score: {analysis['novelty_score']}/10")
    print(f"Feasibility Score: {analysis['feasibility_score']}/10\n")

    print("Core Flaws:")
    for flaw in analysis["core_flaws"]:
        print(f"- {flaw}")

    print("\nHidden Assumptions:")
    for assumption in analysis["hidden_assumptions"]:
        print(f"- {assumption}")

    print("\nImprovement Directions:")
    for direction in analysis["improvement_directions"]:
        print(f"- {direction}")

    print(f"\nBrutal Truth:\n{analysis['brutal_truth']}")
    save_idea(raw_idea, analysis)

    print("\nIdea saved successfully.")


if __name__ == "__main__":
    true = input("Hey, let's Start writing ideas(Y/N):")
    main()
    true = input("Have a Great and Imaginative Day :)")