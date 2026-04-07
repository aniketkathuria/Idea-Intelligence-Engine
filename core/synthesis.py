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
        # Handle both data shapes:
        # New shape: analysis = {"research": [...], "evaluation": {...}}
        # Old shape: analysis = {"idea_summary": ..., "category": ..., ...}
        ev = idea['analysis'].get('evaluation') or idea['analysis']
        
        formatted_context += f"""
    Idea ID: {idea['id']}
    Raw Idea:
    {idea['raw_idea']}

    Evaluation Summary:
    {ev['idea_summary']}
    -------------------------
    """
        
    # In synthesis.py, for the new_idea passed in:
    ev = new_idea['analysis'].get('evaluation') or new_idea['analysis']

    # Then use ev['idea_summary'] instead of new_idea['analysis']['evaluation']['idea_summary']

    prompt = f"""
You are analyzing structural relationships between ideas written by the same person.

This is not an investor evaluation.
This is a cognitive mapping exercise.

A new idea has been generated.

New Idea:
ID: {new_idea['id']}
Raw Idea:
{new_idea['raw_idea']}

Evaluation Summary:
ev['idea_summary']

Context Ideas:
{formatted_context}

Your tasks:

1. MECHANISM EXTRACTION:
- Identify the core mechanism of the new idea in one sentence.
- Identify the core mechanism of each context idea in one sentence.
- Use mechanism similarity (not theme similarity) as primary merge criterion.

2. OVERLAP ANALYSIS:
- Determine whether the new idea conceptually overlaps with the context ideas.
- Identify the core shared theme (if any).
- Provide structural overlap analysis (not superficial wording similarity).
- Identify distinct conceptual elements of each idea.

3. EVOLUTION CHECK:
Determine whether these ideas represent:
   - Variations of one core idea
   - Evolution of a single idea over time
   - Or separate but related explorations

4. ABSTRACTION & SCOPE CHECK:
- Determine if ideas operate at the same abstraction level.
- Determine if one idea generalizes the other.
- Determine if one idea shifts domain (e.g., from product to meta-system).
- Do NOT merge if abstraction layers differ significantly.
- Do NOT merge if core mechanisms differ even if themes overlap.

5. TRANSITIVE CONSISTENCY CHECK:
- Compare the new idea against the foundational ideas in the cluster.
- If similarity is only with recent additions but not structurally aligned with the core idea, do NOT merge.

6. MERGE RISK CHECK:
- If merging reduces conceptual clarity or increases abstraction vagueness, set should_merge to false.

However:
- If merging creates a clearer, stronger, more coherent conceptual direction, allow the merge.
- Controlled scope expansion is acceptable if mechanism alignment remains strong.

If merging is appropriate:
7. Synthesize a unified "super idea" representing their strongest combined form.
8. Re-evaluate the merged super idea briefly:
   - Conceptual coherence
   - Structural strength
   - Primary constraint
   - Most fragile assumption
   - Whether merge improves or weakens clarity

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
- If should_merge is false, set merged_super_idea_summary and unified_evaluation fields to null.
- Always clearly explain reasoning behind merge decision.
"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2
    )

    return parse_json_with_repair(response.choices[0].message.content)