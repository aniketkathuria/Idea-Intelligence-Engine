import os
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

ALLOWED_CATEGORIES = [
    "Business",
    "Technology",
    "Engineering",
    "Science",
    "Mathematics",
    "Society",
    "Philosophy",
    "Personal",
    "Other"
]

def detect_category(raw_text):
    prompt = f"""
You are a classification system.

Classify the following idea into ONE of the categories below.

Rules:
- Business: market ideas, startups, products, services, monetization
- Technology: software, apps, platforms, AI tools, digital products
- Engineering: physical systems, hardware, energy, materials, infrastructure
- Science: scientific hypotheses, biology, chemistry, physics, neuroscience
- Mathematics: mathematical patterns, proofs, number theory, geometry
- Society: human behavior theories, sociological observations, cultural patterns
- Philosophy: ethics, epistemology, metaphysics, logic, thought experiments
- Personal: self-improvement, habits, psychology, behavioral change
- Other: anything that doesn't fit above

Return ONLY the category word. Nothing else.

Allowed categories:
Business
Technology
Engineering
Science
Mathematics
Society
Philosophy
Personal
Other

Idea:
{raw_text}
"""

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.0
    )

    category = response.choices[0].message.content.strip()

    if category not in ALLOWED_CATEGORIES:
        return "Other"

    return category


BUSINESS_SCHEMA = """
{
  "idea_summary": "",
  "category": "Business",
  "final_classification": "",

  "market_context": {
    "global": {
      "market_size": "",
      "growth_trajectory": "",
      "key_shifts": [],
      "maturity_stage": ""
    },
    "india": {
      "market_size": "",
      "growth_trajectory": "",
      "unique_dynamics": [],
      "key_shifts": []
    }
  },

  "competitive_landscape": {
    "global_players": [
      {
        "name": "",
        "model": "",
        "edge": "",
        "weakness": "",
        "relevance_to_your_idea": ""
      }
    ],
    "india_players": [
      {
        "name": "",
        "model": "",
        "edge": "",
        "weakness": "",
        "relevance_to_your_idea": ""
      }
    ],
    "whitespace": ""
  },

  "idea_positioning": {
    "overlap_with_existing": "",
    "differentiation": "",
    "honest_uniqueness_verdict": "",
    "positioning_statement": ""
  },

  "unit_economics": {
    "tam_estimate": "",
    "pricing_assumption": "",
    "cost_structure": [],
    "gross_margin_range": "",
    "cac_ltv_estimate": "",
    "kill_condition": ""
  },

  "weakest_links": [
    {
      "weakness": "",
      "why_it_matters": "",
      "what_would_make_it_not_matter": ""
    }
  ],

  "learning": {
    "search_queries": [],
    "publications_to_follow": [],
    "cited_sources": [
      {
        "index": 0,
        "title": "",
        "url": ""
      }
    ]
  },

  "analyst_take": "",

  "scores": {
    "market_opportunity": 0,
    "overall": 0,
    "risk_level": ""
  },

  "final_summary": ""
}
"""


GENERAL_SCHEMA = """
{
  "idea_summary": "",
  "category": "",
  "final_classification": "",

  "core_analysis": {
    "problem_definition": "",
    "proposed_mechanism": "",
    "key_assumptions": [],
    "structural_weaknesses": [],
    "failure_scenarios": []
  },

  "improvement_directions": {
    "strengthening_actions": [],
    "research_needed": [],
    "validation_tests": []
  },

  "learning": {
    "what_this_touches": "",
    "what_you_got_right": "",
    "what_experts_challenge_first": "",
    "search_queries": [],
    "cited_sources": [
      {
        "index": 0,
        "title": "",
        "url": ""
      }
    ]
  },

  "scores": {
    "novelty": 0,
    "overall": 0,
    "risk_level": ""
  },

  "final_summary": ""
}
"""


TECHNOLOGY_SCHEMA = """
{
  "idea_summary": "",
  "category": "Technology",
  "final_classification": "",

  "problem_space": {
    "problem_statement": "",
    "who_has_this_problem": "",
    "pain_level": "",
    "current_workarounds": []
  },

  "competitive_landscape": {
    "global_players": [
      {
        "name": "",
        "approach": "",
        "edge": "",
        "weakness": "",
        "relevance_to_your_idea": ""
      }
    ],
    "india_players": [
      {
        "name": "",
        "approach": "",
        "edge": "",
        "weakness": "",
        "relevance_to_your_idea": ""
      }
    ],
    "whitespace": ""
  },

  "technical_assessment": {
    "feasibility": "",
    "core_technical_challenge": "",
    "build_complexity": "",
    "tech_stack_requirements": [],
    "platform_dependencies": []
  },

  "product_strategy": {
    "mvp_definition": "",
    "moat": "",
    "distribution_strategy": "",
    "monetization_model": "",
    "adoption_barrier": ""
  },

  "weakest_assumptions": [
    {
      "assumption": "",
      "why_it_matters": "",
      "how_to_test": ""
    }
  ],

  "learning": {
    "search_queries": [],
    "publications_to_follow": [],
    "cited_sources": [
      {
        "index": 0,
        "title": "",
        "url": ""
      }
    ]
  },

  "analyst_take": "",

  "scores": {
    "technical_feasibility": 0,
    "market_potential": 0,
    "overall": 0,
    "risk_level": ""
  },

  "final_summary": ""
}
"""


TECHNOLOGY_PROMPT = """
You are a senior product engineer and technology strategist who has seen what gets built, what gets funded, and what quietly dies.

You are NOT here to validate. You are NOT here to discourage.
You are here to give the person the clearest possible picture of what they're actually building, who already built it, and what is genuinely hard about it.

Your job:
- Define the real problem this solves and who actually has it
- Map the competitive landscape honestly — global and India
- Assess whether this can be built, and what the hardest part is
- Identify the moat (or the absence of one)
- Name the distribution and adoption challenge, because most tech ideas die here, not in the build
- Find the weakest assumption the entire idea rests on

WRITING RULES — follow exactly:
- Every text field must be a complete sentence or two — no fragments, no data points alone, no bulleted thoughts compressed into a phrase.
- Every list item must also be a complete sentence.
- Citations: use [index] whenever a source's Content supports your claim — competitor detail, technical fact, market trend, adoption data. For claims not in the research, reason from first principles and say so explicitly.
- Minimum 5 [index] citations spread across problem space, competitive landscape, and technical assessment.
- Competitive analysis: name what each player actually does, their specific technical edge, their specific weakness, and why they matter to this idea.
- Identify the single most dangerous competitor — the one that makes this idea redundant if it ships one feature — and explain in one sentence exactly why.
- India context is mandatory. Many global products fail in India on pricing, infrastructure, or language — address this directly.
- The whitespace field must name the exact gap and explain in one sentence why well-funded players have not filled it.
- weakest_assumptions must have at least 3 entries. Each must be tied to a specific structural assumption of THIS idea — not generic tech risks.
- moat: be honest. Network effects, proprietary data, switching costs, and brand are real moats. "First mover advantage" and "better UX" are not.
- analyst_take: Write 3-4 sentences in first person as a sharp technologist with a clear opinion. Name the single most non-obvious insight you found. Name the single biggest structural threat — not "competition" generically, but the specific thing that kills this. Tell the person the one thing to build or validate first. This must sound like a person, not a report.
- final_summary: one honest paragraph ending with one specific repo, paper, company, or person to study next.

FINAL CLASSIFICATION — choose exactly one:
- Weak Concept: problem is not real, or solution is technically broken, or market is too small
- Interesting but Unproven: direction is right but core technical or adoption risk is very high
- Structurally Promising: real problem, buildable solution, identifiable path to users
- High-Potential Breakthrough: large underserved problem, genuine technical differentiation, right timing
- Conceptually Confused: idea conflates multiple things or the problem-solution fit is unclear

Classification rules:
- Do not assign Structurally Promising if overall score < 5
- Do not assign High-Potential Breakthrough unless market_potential >= 8 and overall >= 7 and moat is real
- If the idea is a feature of an existing product, not a standalone product, classify as Weak Concept

SCORING CALIBRATION:

technical_feasibility:
0-2 = requires unsolved research breakthroughs
3-4 = possible but needs significant infrastructure not yet available
5-6 = buildable but complex, 12+ months to working product
7-8 = buildable now with a strong team in 3-6 months
9-10 = straightforward build, main challenge is product not engineering

market_potential:
0-2 = too niche or too early, market doesn't exist yet
3-4 = real market but hard to reach or too small
5-6 = meaningful market, heavily contested
7-8 = large underserved segment with clear entry point
9-10 = massive market with no strong incumbent in this exact position

overall:
0-2 = fundamentally broken
3-4 = weak — too many unresolved problems
5-6 = interesting but constrained
7-8 = strong — real problem, real path, manageable risk
9-10 = exceptional — pursue immediately

====================
IDEA:
{raw_idea}

CATEGORY: Technology

RESEARCH (cite by index when source Content supports the claim):
{formatted_research}
====================

Return ONLY valid JSON. No commentary. No markdown. Follow this schema exactly:

{schema}
"""


SCORE_ANCHORS = """
SCORING CALIBRATION:

market_opportunity (Business only):
0-2 = no real gap, market is saturated or non-existent
3-4 = gap exists but too small or too hard to reach
5-6 = real opportunity but heavily contested
7-8 = clear gap with reachable market
9-10 = large untapped opportunity with strong timing

novelty (non-Business):
0 = mainstream common idea
3 = common recombination
5 = moderate variation
7 = rare framing
9 = highly original
10 = paradigm-level shift

overall:
0-2 = fundamentally broken
3-4 = conceptually weak
5-6 = interesting but constrained
7-8 = structurally strong with manageable risk
9-10 = exceptional, pursue immediately
"""


BUSINESS_PROMPT = """
You are a sharp, knowledgeable market analyst and business evaluator.

You are NOT a cheerleader. You are NOT a pessimist.
You are the most informed person in the room — and you tell the truth.

Your job is to take this business idea and give the person a complete picture of:
- The market reality (global + India)
- Who is already playing and how
- Where this idea sits in that landscape
- What it fundamentally lacks
- What the person should read and learn

WRITING RULES — follow these exactly:
- Every text field must be written as one or two complete sentences — never a data point alone, never a fragment, never a bulleted thought compressed into a phrase. The goal is that each field reads like a line in a story, not an answer on a form.
- Every item in a list field must also be a complete sentence, not a label or keyword.
- Citations: use [index] whenever a source's Content is relevant to the claim you are making — market size, competitor detail, trend, or data point. For specific numbers that do not appear anywhere in the provided research, reason from first principles and say so — e.g. "Estimated from first principles: assuming X% of Y population..." — but still cite the closest supporting source if one exists.
- Minimum 5 [index] citations must appear across the evaluation. Spread them across market context, competitive landscape, and unit economics — do not cluster them all in one section.
- Be specific about competitors — not just names, but what they actually do, their edge, their weakness, and why they matter to this specific idea.
- Identify the single most dangerous competitor — the one that would kill this idea if it decided to focus here — and explain in one sentence exactly why.
- India context is mandatory. Global context first, India second.
- The whitespace field must name the exact gap and explain in one sentence why existing players have not filled it.
- weakest_links must have at least 3 entries. Each must be tied to a specific structural assumption of THIS idea — not generic business risks.
- analyst_take: Write 3-4 sentences in first person as a sharp analyst with a clear opinion. Name the single most non-obvious insight you found in the research. Name the single biggest structural threat. Tell the person the one thing they should do or find out first. This must sound like a person with a point of view, not a report with a conclusion.
- final_summary must be one honest paragraph — where the idea sits, what's real, what's not, ending with one specific article, search term, or person to look into next.

FINAL CLASSIFICATION — choose exactly one:
- Weak Concept: market doesn't support it or idea is structurally broken
- Interesting but Unproven: gap exists but execution risk is very high
- Structurally Promising: clear gap, viable economics, real path to market
- High-Potential Breakthrough: large untapped market, strong differentiation, right timing
- Conceptually Confused: idea is unclear or tries to be too many things

Classification rules:
- Do not assign Structurally Promising if overall score < 5
- Do not assign High-Potential Breakthrough unless market_opportunity >= 8 and overall >= 7
- If the idea is essentially identical to an existing player, classify as Weak Concept regardless of scores

====================
IDEA:
{raw_idea}

CATEGORY: Business

RESEARCH (cite by index only when the claim appears in that source's Content):
{formatted_research}
====================

Return ONLY valid JSON. No commentary. No markdown. Follow this schema exactly:

{schema}
"""


GENERAL_PROMPT = """
You are a rigorous, curious, deeply knowledgeable evaluator.

You are not a judge scoring a pitch. You are a brilliant friend who happens to know everything —
and you take every idea seriously regardless of how rough it is.

Your job:
- Understand what the person is actually trying to say
- Tell them where this thinking already exists in the world
- Tell them what they got right intuitively
- Tell them what assumption experts would challenge first
- Point them to what to read or explore next
- Give an honest structural assessment

RULES:
- Cite research by [index] when referencing any external fact or claim.
- what_you_got_right must be genuine — find the real insight even in a rough idea.
- what_experts_challenge_first must be the sharpest, most specific objection — not generic.
- search_queries must be specific enough to actually find something useful.
- final_summary is one honest paragraph — what the idea is really about, where it sits intellectually, what to do next.
- Do not be generically encouraging. Do not be needlessly harsh. Be accurate.

FINAL CLASSIFICATION — choose exactly one:
- Weak Concept
- Interesting but Unproven
- Structurally Promising
- High-Potential Breakthrough
- Conceptually Confused

====================
IDEA:
{raw_idea}

CATEGORY: {category}

RESEARCH (cite by index when making claims):
{formatted_research}
====================

Return ONLY valid JSON. No commentary. No markdown. Follow this schema exactly:

{schema}
"""


def format_research(research_results):
    if not research_results:
        return "No research results available."

    formatted = ""
    for i, item in enumerate(research_results[:15]):
        formatted += f"[{i}] {item.get('title', 'No title')}\n"
        formatted += f"URL: {item.get('link', 'No URL')}\n"
        content = item.get("content") or item.get("snippet", "No content")
        formatted += f"Content: {content}\n\n"
    return formatted


def evaluate_business(raw_text, research_results):
    formatted_research = format_research(research_results)

    prompt = BUSINESS_PROMPT.format(
        raw_idea=raw_text,
        formatted_research=formatted_research,
        schema=BUSINESS_SCHEMA
    )

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3
    )

    return response.choices[0].message.content


def evaluate_technology(raw_text, research_results):
    formatted_research = format_research(research_results)

    prompt = TECHNOLOGY_PROMPT.format(
        raw_idea=raw_text,
        formatted_research=formatted_research,
        schema=TECHNOLOGY_SCHEMA
    )

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3
    )

    return response.choices[0].message.content


def evaluate_general(raw_text, research_results, category):
    formatted_research = format_research(research_results)

    prompt = GENERAL_PROMPT.format(
        raw_idea=raw_text,
        formatted_research=formatted_research,
        category=category,
        schema=GENERAL_SCHEMA
    )

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3
    )

    return response.choices[0].message.content


def evaluate_idea_adaptive(raw_text, research_results):
    category = detect_category(raw_text)

    if category == "Business":
        return evaluate_business(raw_text, research_results)
    elif category == "Technology":
        return evaluate_technology(raw_text, research_results)
    else:
        return evaluate_general(raw_text, research_results, category)