import os
from openai import OpenAI
from core.parser import parse_json_with_repair

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def run_synthesis(new_idea, context_ideas):
    """
    Perform structural comparison and conceptual synthesis
    between a new idea and context ideas (matched or cluster).

    Returns structured JSON.
    """

    # Build structured context block
    formatted_context = ""

    for idea in context_ideas:
        formatted_context += f"""
Idea ID: {idea['id']}
Raw Idea:
{idea['raw_idea']}

Evaluation Summary:
{idea['analysis']['evaluation']['idea_summary']}
-------------------------
"""

    prompt = f"""
You are analyzing structural relationships between ideas written by the same person.

A new idea has been generated.

New Idea:
ID: {new_idea['id']}
Raw Idea:
{new_idea['raw_idea']}

Evaluation Summary:
{new_idea['analysis']['evaluation']['idea_summary']}

Context Ideas:
{formatted_context}

Your tasks:

1. Determine whether the new idea conceptually overlaps with the context ideas.
2. Identify the core shared theme (if any).
3. Provide structural overlap analysis (not superficial wording similarity).
4. Identify distinct conceptual elements of each idea.
5. Determine whether these ideas represent:
   - Variations of one core idea
   - Evolution of a single idea over time
   - Or separate but related explorations
6. Decide whether these ideas should be merged into a single conceptual cluster.

If merging is appropriate:
7. Synthesize a unified "super idea" representing their strongest combined form.
8. Re-evaluate this unified idea as if it were a single fresh idea.

Return ONLY valid JSON with this structure:

{{
  "core_shared_theme": "...",
  "overlap_analysis": "...",
  "distinct_elements_per_idea": {{
      "idea_id": "distinct element description"
  }},
  "are_these_evolutionary": true/false,
  "should_merge": true/false,
  "merge_reasoning": "...",
  "merged_super_idea_summary": "...",
  "unified_evaluation": {{
      "novelty_estimate": "...",
      "feasibility_estimate": "...",
      "key_risk": "...",
      "upside_potential": "..."
  }},
  "strategic_recommendation": "...",
  "conversational_reflection": "..."
}}

Rules:
- Be structurally analytical.
- Do NOT exaggerate similarity.
- Only recommend merge if conceptual overlap is strong.
- If overlap is weak, set should_merge to false.
- Do NOT output markdown.
- Do NOT add explanations outside JSON.
- If should_merge is false, still return all fields but set merged_super_idea_summary to null and unified_evaluation fields to null.
- Always clearly explain the reasoning behind the merge decision in "merge_reasoning".
- If should_merge is false, explain why conceptual differences justify keeping them separate.
"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2
    )

    return parse_json_with_repair(response.choices[0].message.content)