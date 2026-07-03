import os
from openai import OpenAI
from core.parser import parse_json_with_repair

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def _get_summary(ev):
    # Named summary fields across all category schemas
    for key in ['idea_summary', 'conjecture_summary', 'observation_summary', 'argument_summary',
                'hypothesis_summary', 'engineering_summary', 'science_summary']:
        if key in ev:
            return ev[key]
    # Engineering and Science use hook + core narrative format (no dedicated summary field)
    if 'core' in ev:
        hook = ev.get('hook', '')
        core = ev.get('core', '')
        return f"{hook} {core}".strip() or 'No summary available'
    return ev.get('final_summary', 'No summary available')


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
    {_get_summary(ev)}
    -------------------------
    """

    ev = new_idea['analysis'].get('evaluation') or new_idea['analysis']

    prompt = f"""
You are a cognitive cartographer mapping the idea space of a single person.
Your job is NOT to evaluate ideas — that was done separately.
Your job is to understand how ideas RELATE to each other and whether they form something bigger together.

---

NEW IDEA (label: "new"):
{new_idea['raw_idea']}

Summary: {_get_summary(ev)}

---

CONTEXT IDEAS:
{formatted_context}

---

STEP 1 — INDIVIDUAL MECHANISMS
For each idea (new + each context idea), identify in one sentence:
- Core mechanism: What is this idea fundamentally DOING or PROPOSING? (not its topic — its mechanism)
- Unique contribution: What does only this idea bring that the others do not?
- Surface framing: What domain, metaphor, or color does it use to express itself?

STEP 2 — RELATIONSHIP CLASSIFICATION
Classify the relationship between these ideas as exactly one of:
- "complementary": Different mechanisms that together create something neither achieves alone → strong merge candidate
- "evolutionary": The new idea is a direct development or refinement of an older idea → merge if it supersedes
- "variations": Same core mechanism expressed in different domains or framings → do NOT merge (same idea, different color)
- "divergent": Genuinely different ideas that happen to share a surface topic → do NOT merge

CRITICAL DISTINCTION:
Two ideas about "AI in education" where one is about personalized pacing and one is about teacher augmentation → complementary → merge candidate.
Two ideas about "AI in education" where both are essentially about personalized learning but framed differently → variations → do NOT merge.
The test is: do the mechanisms combine into something neither idea alone achieves?

STEP 3 — MERGE DECISION
Merge ONLY if:
- relationship_type is "complementary" or "evolutionary"
- The combined idea is MORE than the sum of its parts
- Merging sharpens clarity rather than diluting it

Do NOT merge if:
- They are variations (same core, different surface)
- They are divergent (different topics that share wording)
- Merging increases abstraction vagueness
- One idea already contains the other

STEP 4 — IF MERGING: SYNTHESIS
Write a super_idea that is NOT a summary of both ideas.
It should be the emergent concept that ONLY exists because these ideas are seen together.
Then write a cluster_narrative: what pattern of thinking does this cluster reveal about the person? What bigger question are they circling?

STEP 5 — IF NOT MERGING
Explain clearly WHY — specifically address whether this is a "same core different color" case or a "genuinely different" case.
Set super_idea and cluster_narrative to null.

---

Return ONLY valid JSON:

{{
  "relationship_type": "complementary | evolutionary | variations | divergent",
  "shared_foundation": "The deepest thing these ideas share, in one sentence",
  "idea_roles": [
    {{
      "idea_id": "new",
      "core_mechanism": "...",
      "unique_contribution": "...",
      "surface_framing": "..."
    }},
    {{
      "idea_id": <id of context idea>,
      "core_mechanism": "...",
      "unique_contribution": "...",
      "surface_framing": "..."
    }}
  ],
  "distinction_analysis": "How these ideas differ — specifically at the mechanism level, not the surface level",
  "should_merge": true/false,
  "merge_reasoning": "Direct explanation of the merge decision. If variations: name the shared core and the differing colors explicitly.",
  "super_idea": "The emergent concept that only exists because these ideas are seen together. NOT a summary. Null if not merging.",
  "cluster_narrative": "What pattern of thinking does this cluster reveal? What bigger question is being explored? Null if not merging."
}}

Rules:
- Do NOT output markdown or explanations outside the JSON.
- idea_roles must include one entry per idea (new + all context ideas).
- Use the exact idea_id values provided ("new" for the new idea, integer IDs for context ideas).
- If should_merge is false, super_idea and cluster_narrative must be null.
- Be precise and analytical. Do not exaggerate connections."""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2
    )

    return parse_json_with_repair(response.choices[0].message.content)