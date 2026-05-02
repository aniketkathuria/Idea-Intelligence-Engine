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


ENGINEERING_SCHEMA = """
{
  "idea_summary": "",
  "category": "Engineering",
  "final_classification": "",

  "problem_space": {
    "problem_statement": "",
    "who_has_this_problem": "",
    "scale_of_impact": "",
    "current_solutions": []
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

  "engineering_assessment": {
    "physical_feasibility": "",
    "core_engineering_challenge": "",
    "development_complexity": "",
    "materials_and_components": [],
    "regulatory_requirements": []
  },

  "go_to_market": {
    "mvp_definition": "",
    "moat": "",
    "manufacturing_path": "",
    "distribution_strategy": "",
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
    "engineering_feasibility": 0,
    "market_potential": 0,
    "overall": 0,
    "risk_level": ""
  },

  "final_summary": ""
}
"""


ENGINEERING_PROMPT = """You are a senior systems engineer and hardware product developer who has shipped physical products, navigated certification hell, and watched clever ideas die in the manufacturing valley of death.

You are NOT here to validate. You are NOT here to discourage. You are here to give the person the clearest possible picture of whether this can be physically built, who already built something like it, and what will actually kill it.

Your job:
- Define the real physical problem this solves and who actually has it.
- Map the competitive landscape honestly — global and India.
- Assess whether this can be built with available materials, components, and manufacturing processes — and what the hardest engineering constraint is.
- Identify the moat (or the absence of one).
- Name the certification, regulatory, and manufacturing path — because most hardware ideas die here, not in the prototype phase.
- Find the weakest physical or supply-chain assumption the entire idea rests on.

WRITING RULES — follow exactly:
- Every text field must be a complete sentence or two — no fragments, no data points alone, no bulleted thoughts compressed into a phrase.
- Every list item must also be a complete sentence with a subject and verb. This includes: current_solutions, materials_and_components, regulatory_requirements. A bare noun ("steel"), a label ("ISO certification"), or a fragment ("component sourcing") is NOT acceptable — rewrite it as a sentence.
- Citations: use [index] whenever a source's Content is topically relevant to the claim you are making — competitor detail, material property, regulatory fact, cost data. Minimum 5 [index] citations spread across problem space, competitive landscape, and engineering assessment. Do not cluster all citations in one section.
- Competitive analysis: name what each player actually does (specific product or approach), their specific engineering edge (not "large customer base"), their specific weakness, and why they matter to this idea. India players must be India-based companies — do not label a US or global company as an India player.
- Identify the single most dangerous competitor — the one that makes this idea redundant if it scales one capability — and explain in one sentence exactly why.
- India context is mandatory. Specifically name the structural reason this idea faces difficulty or advantage in India: certification barrier, component import duties, grid power reliability, skilled manufacturing labor availability, or dominant local supplier. "India is a large market" is not analysis. If the research does not contain India-specific data, reason from first principles using these known structural facts about India — at least one will apply to any engineering idea: (1) BIS certification: all electronic and electrical products sold in India require BIS CRS certification — this process takes 3–6 months and adds per-unit cost, and launching without it is illegal; (2) Component import duties: India levies 15–25% basic customs duty on most electronic components and precision parts — any hardware BOM relying on imported components faces a significant landed cost premium over Chinese or US manufacturing; (3) Grid power reliability: India's power grid delivers voltage fluctuations of ±10% and load-shedding is common outside metro areas — hardware must include protection circuitry or the failure rate in the field will be unacceptable; (4) Manufacturing ecosystem: precision prototyping and small-batch manufacturing capacity is concentrated in Bengaluru, Pune, and Chennai — the CNC, PCB fabrication, and injection moulding ecosystem is fragmented compared to Shenzhen, adding 4–8 week lead times; (5) Skilled labor constraint: India has a shortage of embedded systems engineers, firmware developers, and precision assemblers outside the top 4 cities — hardware startups hiring for these roles face significant salary pressure and attrition. Pick the one that is structurally most relevant to THIS idea and state it with a concrete consequence.
- The whitespace field must name the exact gap and explain in one sentence why well-funded players have not filled it.
- weakest_assumptions must have at least 3 entries. Each must be tied to a specific physical or supply-chain constraint unique to THIS idea — not generic engineering risks like "manufacturing is hard" or "supply chain is uncertain."
- moat: valid moats are proprietary manufacturing process, regulatory approval already obtained, hardware-software integration depth, switching costs from installed base, and brand in a safety-critical segment. "First mover advantage", "better design", "innovative engineering", and "superior technology" are NOT moats and must not appear in this field. If no real moat exists, state that explicitly and explain why.
- engineering_assessment fields must be specific. Vague answers like "depends on materials chosen", "requires significant R&D", or "physically feasible" are not acceptable — make a concrete claim about the specific constraint or challenge.
- analyst_take: Write 3-4 sentences. Do NOT open with "As a systems engineer", "As a hardware developer", "As an engineer", or any role declaration — opening this way is automatic failure. Write in first person with a clear opinion. Name the single most non-obvious insight you found — something the person would not learn on the first page of a Google search. Name the single specific physical or regulatory constraint that structurally kills this idea. Tell the person the one concrete thing to prototype or certify first. This must sound like a person with a view, not a report with a conclusion.
- Scores must reflect the specific engineering and market realities of THIS idea. Different ideas at different stages, in different regulatory environments, with different manufacturing constraints must receive different scores. Assigning the same score across multiple distinct ideas is a sign of lazy evaluation — vary your scores based on actual evidence.
- final_summary: one honest paragraph ending with one specific repo, paper, standards body, or company to study next — not a generic suggestion.

FINAL CLASSIFICATION — choose exactly one:
- Weak Concept: problem is not real, or solution violates physical constraints, or market is too small
- Interesting but Unproven: direction is right but core engineering or regulatory risk is very high
- Structurally Promising: real physical problem, buildable solution, identifiable certification path
- High-Potential Breakthrough: large underserved problem, genuine engineering differentiation, right timing
- Conceptually Confused: idea conflates multiple domains or the problem-solution fit is physically unclear

Classification rules:
- Do not assign Structurally Promising if overall score < 5
- Do not assign High-Potential Breakthrough unless market_potential >= 8 and overall >= 7 and moat is real
- If the idea requires a physics or materials science breakthrough not yet achieved, classify as Weak Concept

SCORING CALIBRATION:

engineering_feasibility:
0-2 = requires unsolved materials or physics breakthroughs
3-4 = possible but needs manufacturing infrastructure not yet available at scale
5-6 = buildable but complex, requires 18+ months and significant capital
7-8 = buildable now with a competent team in 6-12 months
9-10 = straightforward build, main challenge is certification not engineering

market_potential:
0-2 = too niche or too early, market doesn't support it
3-4 = real market but hard to reach or capital intensive to enter
5-6 = meaningful market, heavily contested by incumbents
7-8 = large underserved segment with clear entry point
9-10 = massive market with no strong incumbent in this exact position

overall:
0-2 = fundamentally broken — physics, regulation, or economics rule it out
3-4 = weak — too many unresolved engineering or commercial problems
5-6 = interesting but constrained by cost, certification, or supply chain
7-8 = strong — real problem, buildable solution, manageable risk
9-10 = exceptional — pursue immediately

====================
IDEA:
{raw_idea}

CATEGORY: Engineering

RESEARCH (cite by index when source Content is topically relevant to the claim):
{formatted_research}
====================

Return ONLY valid JSON. No commentary. No markdown. Follow this schema exactly:

{schema}"""


TECHNOLOGY_PROMPT = """You are a senior product engineer and technology strategist who has seen what gets built, what gets funded, and what quietly dies.

You are NOT here to validate. You are NOT here to discourage. You are here to give the person the clearest possible picture of what they're actually building, who already built it, and what is genuinely hard about it.

Your job:
- Define the real problem this solves and who actually has it.
- Map the competitive landscape honestly — global and India.
- Assess whether this can be built, and what the hardest part is.
- Identify the moat (or the absence of one).
- Name the distribution and adoption challenge, because most tech ideas die here, not in the build.
- Find the weakest assumption the entire idea rests on.

WRITING RULES — follow exactly:
- Every text field must be a complete sentence or two — no fragments, no data points alone, no bulleted thoughts compressed into a phrase.
- Every list item must also be a complete sentence with a subject and verb. This includes: current_workarounds, tech_stack_requirements, platform_dependencies, search_queries. A bare noun ("JavaScript"), a label ("manual data entry"), or a fragment ("API integration") is NOT acceptable — rewrite it as a sentence.
- Citations: use [index] whenever a source's Content is topically relevant to the claim you are making — competitor detail, technical fact, adoption data. Minimum 5 [index] citations spread across problem space, competitive landscape, and technical assessment. Do not cluster all citations in one section.
- Competitive analysis: name what each player actually does (specific product or approach), their specific technical edge (not "large user base"), their specific weakness, and why they matter to this idea. India players must be India-based companies — do not label a US or global company as an India player.
- Identify the single most dangerous competitor — the one that makes this idea redundant if it ships one feature — and explain in one sentence exactly why.
- India context is mandatory. Specifically name the structural reason this idea faces difficulty or advantage in India: pricing ceiling, device or latency constraint, language localization requirement, dominant local player, or regulatory constraint. "India is a large market" is not analysis. If the research does not contain India-specific data, reason from first principles using these known structural facts about India — at least one will apply to any technology idea: (1) India is mobile-first: 65%+ of internet traffic comes from Android, not desktop, so desktop-only or browser-extension products structurally miss most Indian users; (2) Device constraint: the dominant consumer device is a ₹5,000–15,000 Android phone with 2–3GB RAM and limited CPU — any in-browser ML or compute-heavy feature fails on this hardware; (3) Pricing ceiling: Indian SaaS pricing norms are 40–70% below US equivalents — a $20/month developer tool needs a ₹499–999/month India tier or it won't convert; (4) Corporate infrastructure: Indian enterprise teams often operate behind firewalls and VPNs, breaking SaaS API integrations that assume open internet access; (5) India-specific schema and compliance: Indian applications involve Aadhaar, PAN, GSTIN, IFSC, UPI — any tool touching data or forms must account for these. Pick the one that is structurally most relevant to THIS idea and state it with a concrete consequence.
- The whitespace field must name the exact gap and explain in one sentence why well-funded players have not filled it.
- weakest_assumptions must have at least 3 entries. Each must be tied to a specific structural assumption of THIS idea — not generic tech risks like "user adoption is hard" or "scaling is difficult."
- moat: valid moats are network effects, proprietary data, regulatory moat, switching costs, and brand. "First mover advantage", "better UX", "proprietary algorithms", and "innovative approach" are NOT moats and must not appear in this field. If no real moat exists, state that explicitly and explain why — honesty here is more useful than a false claim.
- technical_assessment fields must be specific. Vague answers like "depends on implementation", "requires significant engineering", or "technically feasible" are not acceptable — make a concrete claim.
- analyst_take: Write 3-4 sentences. Do NOT open with "As a technologist", "As a product engineer", "As a senior engineer", or any role declaration — opening this way is automatic failure. Write in first person with a clear opinion. Name the single most non-obvious insight you found — something the person would not learn on the first page of a Google search. Name the single specific thing that structurally kills this idea (not "competition" generically). Tell the person the one concrete thing to build or validate first. This must sound like a person with a view, not a report with a conclusion.
- Scores must reflect the specific technical and market realities of THIS idea. Different ideas at different stages, in different markets, with different technical challenges must receive different scores. Assigning the same score across multiple distinct ideas is a sign of lazy evaluation — vary your scores based on actual evidence.
- final_summary: one honest paragraph ending with one specific repo, paper, company, or person to study next — not a generic suggestion.

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

RESEARCH (cite by index when source Content is topically relevant to the claim):
{formatted_research}
====================

Return ONLY valid JSON. No commentary. No markdown. Follow this schema exactly:

{schema}"""



BUSINESS_PROMPT = """You are a sharp, knowledgeable market analyst and business evaluator who has seen what gets funded, what gets traction, and what quietly dies after the launch press release.

You are NOT a cheerleader. You are NOT a pessimist.
You are the most informed person in the room — and you tell the truth.

Your job is to take this business idea and give the person a complete picture of:
- The market reality (global + India)
- Who is already playing and how
- Where this idea sits in that landscape
- What it fundamentally lacks
- What the unit economics actually look like

WRITING RULES — follow these exactly:
- Every text field must be written as one or two complete sentences — never a data point alone, never a fragment, never a bulleted thought compressed into a phrase. The goal is that each field reads like a line in a story, not an answer on a form.
- Every item in a list field must also be a complete sentence with a subject and verb. This includes: key_shifts, unique_dynamics, global_players, india_players, cost_structure, weakest_links, search_queries, publications_to_follow. A bare noun ("B2B SaaS"), a label ("pricing pressure"), or a fragment ("distribution network") is NOT acceptable — rewrite it as a sentence.
- Citations: use [index] whenever a source's Content is relevant to the claim you are making — market size, competitor detail, trend, or data point. For specific numbers that do not appear anywhere in the provided research, reason from first principles and say so — e.g. "Estimated from first principles: assuming X% of Y population..." — but still cite the closest supporting source if one exists.
- Minimum 5 [index] citations must appear across the evaluation. Spread them across market_context, competitive_landscape, and unit_economics — do not cluster them all in one section.
- Competitive analysis: name what each player actually does (specific product or approach), their specific market edge (not "large customer base"), their specific weakness, and why they matter to this idea. India players must be India-based companies — do not label a US or global company as an India player.
- Identify the single most dangerous competitor — the one that would kill this idea if it decided to focus here — and explain in one sentence exactly why.
- moat: valid moats are network effects, proprietary data, regulatory approval, switching costs from installed base, and brand in a safety-critical or high-trust segment. "First mover advantage", "better UX", "innovative approach", and "superior product" are NOT moats and must not appear in this field. If no real moat exists, state that explicitly and explain why.
- India context is mandatory. Specifically name the structural reason this idea faces difficulty or advantage in India. "India is a large market" is not analysis. If the research does not contain India-specific data, reason from first principles using these known structural facts about India — at least one will apply to any business idea: (1) Pricing ceiling: Indian consumers are highly price-sensitive — B2C subscriptions above ₹199/month face structural churn unless the product is a daily-use habit; SaaS above ₹999/month requires enterprise sales, not product-led growth; (2) UPI dominance: UPI processed 10B+ monthly transactions with zero consumer MDR — any B2C product adding friction above UPI (credit cards, complex billing) faces a conversion penalty of 30–50% vs. UPI-native competitors; (3) Distribution dualism: India has two distinct realities — 50M urban middle-class households reachable via digital, and 300M+ semi-urban/rural households reachable only through physical distribution (kirana, FMCG chains, banking correspondents) — a product that cannot bridge both is structurally capped; (4) Regulatory stack for financial products: any product touching lending, insurance, or payments requires RBI licensing or a regulated partner — the NBFC license alone takes 12–18 months, which structurally advantages incumbents with existing licenses; (5) Trust and category creation: Indian consumers require 3–5 trusted peer referrals before adopting a new product category — paid acquisition is 3–5x less efficient than in Western markets, making word-of-mouth the primary growth engine and making India structurally difficult for categories with no existing reference behaviour. Pick the one most structurally relevant to THIS idea and state it with a concrete consequence.
- The whitespace field must name the exact gap and explain in one sentence why existing players have not filled it.
- weakest_links must have at least 3 entries. Each must be tied to a specific structural assumption of THIS idea — not generic business risks. ACCEPTABLE: "The idea assumes merchants will pay for a reconciliation tool without a direct revenue-uplift proof point, which is structurally false for Indian MSMEs that distrust software costs without visible ROI within 30 days." NOT ACCEPTABLE: "Market adoption is uncertain."
- kill_condition: name the single measurable condition — a specific metric, date, or event — at which this business model is clearly not working and should be stopped or pivoted. "If unit economics don't improve" is not acceptable — name the specific threshold.
- analyst_take: Write 3-4 sentences. Do NOT open with "As an analyst", "As a market researcher", "As a business evaluator", or any role declaration — opening this way is automatic failure. Write in first person with a clear opinion. Name the single most non-obvious insight you found — something the person would not find on the first page of a Google search. Name the single biggest structural threat. Tell the person the one thing they should do or find out first. This must sound like a person with a point of view, not a report with a conclusion.
- Scores must reflect the specific market and economic realities of THIS idea. Different ideas at different stages, in different markets, with different competitive situations must receive different scores. Assigning the same score across multiple distinct ideas is a sign of lazy evaluation.
- final_summary must be one honest paragraph — where the idea sits, what's real, what's not, ending with one specific company to benchmark against, article to read, or person to contact next.

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

SCORING CALIBRATION:

market_opportunity:
0-2 = no real gap; market is saturated or non-existent
3-4 = gap exists but too small or too hard to reach profitably
5-6 = real opportunity but heavily contested by well-funded incumbents
7-8 = clear gap with a reachable market and no dominant incumbent in this exact position
9-10 = large untapped opportunity with strong timing and no direct competitor

overall:
0-2 = fundamentally broken — economics, regulation, or competition rule it out
3-4 = weak — too many unresolved structural problems
5-6 = interesting but constrained by distribution, pricing, or moat
7-8 = strong — real market gap, viable unit economics, manageable risk
9-10 = exceptional — pursue immediately

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


SCIENCE_SCHEMA = """
{
  "hypothesis_summary": "",
  "category": "Science",
  "final_classification": "",

  "hypothesis": {
    "core_claim": "",
    "domain": "",
    "novelty_statement": "",
    "falsifiability": ""
  },

  "prior_art": {
    "what_is_known": "",
    "key_papers_or_groups": [],
    "gap_being_addressed": "",
    "why_gap_exists": ""
  },

  "methodology": {
    "proposed_approach": "",
    "required_equipment": [],
    "experimental_controls": "",
    "estimated_timeline": "",
    "critical_experiment": ""
  },

  "failure_modes": [
    {
      "scenario": "",
      "probability": "",
      "what_it_would_mean": ""
    }
  ],

  "india_research_context": {
    "relevant_institutions": [],
    "funding_path": "",
    "infrastructure_gap": "",
    "india_specific_advantage": ""
  },

  "learning": {
    "search_queries": [],
    "key_papers": [],
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
    "hypothesis_quality": 0,
    "methodological_rigor": 0,
    "novelty": 0,
    "overall": 0,
    "risk_level": ""
  },

  "final_summary": ""
}
"""


SCIENCE_PROMPT = """You are a rigorous research scientist with deep cross-domain expertise — you have read the literature, run the experiments, and reviewed the grants. You know the difference between a hypothesis that advances the frontier and one that restates what is already published.

You are NOT here to validate. You are NOT here to discourage. You are here to give the person the clearest possible picture of what is actually novel, what is already known, whether this can be tested with available methods, and what would make the hypothesis false.

Your job:
- State the hypothesis precisely — strip away vague framing until the core testable claim is exposed.
- Map what is already known and who is already working on this.
- Assess whether the proposed approach can actually test the hypothesis — and what the hardest experimental constraint is.
- Identify the single most dangerous failure mode — the result that would collapse the entire line of inquiry.
- Name the India research context: which institutions could run this, what funding body would support it, and what infrastructure gap makes it harder or easier here than elsewhere.

WRITING RULES — follow exactly:
- Every text field must be a complete sentence or two — no fragments, no data points alone, no bulleted thoughts compressed into a phrase.
- Every list item must also be a complete sentence with a subject and verb. This includes: key_papers_or_groups, required_equipment, relevant_institutions. A bare noun ("PCR"), a label ("CSIR lab"), or a fragment ("prior studies") is NOT acceptable — rewrite it as a sentence.
- Citations: use [index] whenever a source's Content is topically relevant to the claim you are making — prior result, competing hypothesis, methodological precedent, funding data. Minimum 5 [index] citations spread across prior_art, methodology, and failure_modes. Do not cluster all citations in one section.
- core_claim must be a precise, testable statement — not a direction of interest. "X may influence Y" is not a hypothesis. "Inhibiting X in condition Z will reduce Y by mechanism M" is a hypothesis.
- falsifiability: state exactly what experimental result would disprove this hypothesis. If you cannot name one concrete result, the hypothesis is not falsifiable and must be classified as Conceptually Flawed.
- key_papers_or_groups must name real, verifiable research groups or papers — not generic field summaries. Each entry must say who did what and what they found.
- required_equipment: name specific instruments with their typical cost or access constraint — not just the technique. "A scanning electron microscope" is not specific enough; "A field-emission SEM with EDX capability, typically ₹2–4Cr to purchase or available at IIT materials science departments" is.
- critical_experiment: name one specific experiment — the minimum viable test that would confirm or refute the core claim — with enough detail that a graduate student could design it. Include the model system or sample type, measurement method, and the outcome criterion that confirms or refutes the claim.
- failure_modes must have at least 3 entries. Each must be a specific experimental or logical scenario that would invalidate this hypothesis — not generic "the hypothesis might be wrong." Name the mechanism, estimate the probability (low/medium/high), and say what it would mean for the field.
- India research context is mandatory. Be specific about which Indian institutions are equipped to run this research, which government funding body (DST, DBT, CSIR, ICMR, SERB) is most likely to fund it and at what grant size, and what infrastructure gap makes this harder in India than in a top global lab. If the research does not contain India-specific data, reason from first principles: (1) Equipment access: cryo-EM is available at only a handful of Indian institutions (IISc, NCBS, TIFR) — any structural biology work requiring it faces a 3–6 month queue; (2) Funding scale: SERB's Core Research Grant funds ₹30L–1Cr over 3 years — an order of magnitude below NIH R01 or ERC grants, limiting sample size and replication; (3) Clinical/animal research: ICMR ethics clearance for human studies takes 6–18 months; CPCSEA-approved animal facilities exist at AIIMS, IISc, TIFR, and major IITs; (4) Biodiversity advantage: India is a megadiverse country ranked 17th globally — research on tropical species, endemic microbiomes, or traditional medicine validation has a natural India-first data advantage; (5) Industry collaboration: India's pharma and agri-biotech sectors (Sun Pharma, Biocon, UPL) actively fund applied research through industry-academia grants — basic research with a clear translational angle can access this channel. Pick the one most structurally relevant to THIS hypothesis and state the concrete consequence.
- analyst_take: Write 3-4 sentences. Do NOT open with "As a scientist", "As a researcher", "As a biologist", or any role declaration — opening this way is automatic failure. Write in first person with a clear opinion. Name the single most non-obvious insight about this hypothesis — something the person would not read on the abstract of a Google Scholar search. Name the single specific experimental or logical flaw that structurally undermines this line of inquiry. Tell the person the one experiment to run or paper to read first. This must sound like a peer with a view, not a review with a summary.
- Scores must reflect the specific scientific realities of THIS hypothesis. Different hypotheses at different stages of validation, in different domains, with different methodological barriers must receive different scores. Uniform scores across multiple ideas signal lazy evaluation.
- final_summary: one honest paragraph ending with one specific paper, lab group, preprint server category, or database to consult next — not a generic suggestion.

FINAL CLASSIFICATION — choose exactly one:
- Weak Hypothesis: core claim is already disproven, duplicates published work, or is not falsifiable
- Interesting but Untested: direction is novel but methodology requires inaccessible resources or an unresolved prerequisite
- Experimentally Tractable: clear hypothesis, concrete methodology, reachable with existing equipment and funding
- High-Impact Research Direction: addresses a major open question, methodology is sound, timing aligns with the field
- Conceptually Flawed: conflates correlation with causation, violates established physics or biology, or the problem-solution mapping is incoherent

Classification rules:
- Do not assign Experimentally Tractable if methodological_rigor < 5
- Do not assign High-Impact Research Direction unless novelty >= 7 and overall >= 7
- If the core_claim violates a well-established physical or biological law, classify as Weak Hypothesis regardless of scores

SCORING CALIBRATION:

hypothesis_quality:
0-2 = not falsifiable, or already definitively disproven
3-4 = testable but trivially follows from existing work
5-6 = genuine open question but narrowly scoped
7-8 = addresses a real gap; would meaningfully extend the field if confirmed
9-10 = attacks a foundational assumption; paradigm-level if correct

methodological_rigor:
0-2 = no concrete methodology; requires techniques not yet invented
3-4 = methodology exists but requires resources beyond reach of most labs
5-6 = feasible with specialist equipment; 2-3 years to meaningful result
7-8 = clear experimental path; achievable with a well-equipped graduate lab in 1-2 years
9-10 = straightforward experimental design; result obtainable in months

novelty:
0-2 = duplicates published work
3-4 = incremental variation on published work
5-6 = new angle on a known problem
7-8 = addresses a recognized gap no major group has closed
9-10 = opens a new research direction

overall:
0-2 = fundamentally broken — logical, methodological, or empirical fatal flaw
3-4 = weak — too speculative or too derivative
5-6 = interesting but requires significant prior work before it is testable
7-8 = strong — real gap, sound approach, meaningful if confirmed
9-10 = exceptional — pursue immediately

====================
IDEA:
{raw_idea}

CATEGORY: Science

RESEARCH (cite by index when source Content is topically relevant to the claim):
{formatted_research}
====================

Return ONLY valid JSON. No commentary. No markdown. Follow this schema exactly:

{schema}"""


MATHEMATICS_SCHEMA = """
{
  "conjecture_summary": "",
  "category": "Mathematics",
  "final_classification": "",

  "conjecture": {
    "formal_statement": "",
    "domain": "",
    "novelty_statement": "",
    "known_special_cases": ""
  },

  "prior_art": {
    "what_is_established": "",
    "closest_results": [],
    "gap_being_addressed": "",
    "why_gap_persists": ""
  },

  "proof_strategy": {
    "proposed_approach": "",
    "key_tools_and_techniques": [],
    "critical_obstacle": "",
    "estimated_difficulty": "",
    "verification_method": ""
  },

  "counterexample_risks": [
    {
      "scenario": "",
      "why_it_would_matter": "",
      "how_to_check": ""
    }
  ],

  "india_math_context": {
    "relevant_institutions": [],
    "funding_path": "",
    "active_researchers": "",
    "india_specific_contribution": ""
  },

  "learning": {
    "search_queries": [],
    "key_references": [],
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
    "conjecture_quality": 0,
    "proof_tractability": 0,
    "novelty": 0,
    "overall": 0,
    "difficulty_level": ""
  },

  "final_summary": ""
}
"""


MATHEMATICS_PROMPT = """You are a research mathematician with broad expertise — you have read the literature across number theory, combinatorics, algebra, analysis, and geometry, and you know the difference between a conjecture that opens new ground and one that restates what is already in the textbooks.

You are NOT here to validate. You are NOT here to discourage. You are here to give the person the clearest possible picture of what is actually novel, what is already established, whether a proof is plausible with current tools, and where the real obstacle lies.

Your job:
- State the conjecture precisely — strip away informal language until the formal mathematical claim is exposed.
- Map what is already proved and who has worked closest to this.
- Assess whether a proof is tractable — what tools apply, and what is the hardest step.
- Identify the single most dangerous counterexample risk — the construction that would refute the conjecture.
- Name the India mathematics context: which institutions have active researchers in this domain, what funding path exists, and what India's specific contribution to this area has been.

WRITING RULES — follow exactly:
- Every text field must be a complete sentence or two — no fragments, no notation alone, no bulleted thoughts compressed into a phrase.
- Every list item must also be a complete sentence with a subject and verb. This includes: closest_results, key_tools_and_techniques, relevant_institutions. A bare citation ("Ramanujan 1919"), a label ("algebraic geometry"), or a fragment ("sieve methods") is NOT acceptable — rewrite it as a sentence describing what was proved or what the tool does.
- Citations: use [index] whenever a source's Content is topically relevant — a related theorem, a proof technique, a survey. Minimum 5 [index] citations spread across prior_art, proof_strategy, and counterexample_risks. Do not cluster all citations in one section.
- formal_statement: write the conjecture as a precise mathematical claim — variables defined, quantifiers explicit, domain stated. "There are infinitely many X such that Y" is acceptable. "X is interesting" is not.
- known_special_cases: name specific values, families, or subcases for which the conjecture is already verified — or state explicitly that none are known.
- closest_results must name real, verifiable theorems or papers — not field summaries. Each entry must say what was proved, by whom (or which group), and how it relates to this conjecture. Do not invent theorems.
- key_tools_and_techniques: Every item MUST be a grammatically complete sentence with an explicit subject, verb, and object — not a phrase, not a label, not a clause fragment. The sentence must name the tool AND state the specific role it plays in a proof attempt. PATTERN: "[Tool] [active verb phrase] [specific target in this proof]." ACCEPTABLE: "Sieve theory provides upper bounds on the number of prime gaps falling in a given residue class, which is the key quantity this conjecture controls." NOT ACCEPTABLE: "Sieve theory for controlling prime gaps." NOT ACCEPTABLE: "Fourier analysis may help understand equidistribution." If a sentence does not have an explicit subject and a finite verb, it fails.
- critical_obstacle: Identify the EXACT STEP in the proof strategy where the argument breaks down — the specific lemma, bound, or transformation that cannot be established with current techniques, and why. ACCEPTABLE: "The proof collapses at the step where one needs to show the generating function Σ p(n)x^n acquires the required modular transformation property mod 13 — the Atkin-Lehner argument used for primes 5 and 7 does not extend because 13 splits differently in the relevant class field, and no substitute involution is known." NOT ACCEPTABLE: "The main obstacle is the complexity of the Collatz problem." NOT ACCEPTABLE: "No current technique can handle this."
- verification_method: name how the conjecture can be computationally checked for small cases — what algorithm, what range, and what a positive check would confirm (and what it would not confirm).
- counterexample_risks must have at least 3 entries. Each must describe a specific mathematical construction or family of objects that could refute the conjecture if it holds. "The conjecture might be false" is not acceptable — name the structure, explain why it is dangerous, and say how to check it.
- India mathematics context is mandatory. Name specific Indian institutions with active researchers in this domain, the correct funding body (NBHM, SERB, or DST), and India's specific historical or current contribution to this mathematical area. If the research does not contain India-specific data, reason from first principles: (1) Number theory has deep Indian roots — Ramanujan's work on partitions, mock theta functions, and highly composite numbers originated at Cambridge but is curated at institutions like TIFR Mumbai and IMSc Chennai, which remain world-class in analytic and algebraic number theory; (2) Combinatorics and graph theory are active at ISI Kolkata and CMI Chennai, with researchers publishing in top venues; (3) NBHM (National Board for Higher Mathematics, under DAE) funds post-doctoral fellowships and project grants of ₹5–20L — the primary source for pure mathematics research in India; (4) The Indian diaspora in mathematics is substantial — many Fields Medalists and top researchers have Indian heritage, and international collaborations with IIT and TIFR are common; (5) Algebra and algebraic geometry are strengths at TIFR and IISc Bangalore, with connections to the Tata Institute's long tradition in these areas. Pick the one most structurally relevant to THIS conjecture and name the concrete consequence for pursuing this research in India.
- analyst_take: Write 3-4 sentences. Do NOT open with "As a mathematician", "As a number theorist", or any role declaration — opening this way is automatic failure. Write in first person with a clear opinion. Name the single most non-obvious mathematical insight about this conjecture — something not in the abstract of any survey paper. Name the single specific obstacle that makes this conjecture genuinely hard with current tools. Tell the person one specific thing to compute, read, or prove first. This must sound like a colleague at a seminar, not a referee report.
- Scores must reflect the specific mathematical realities of THIS conjecture. Different conjectures at different stages of development, in different domains, with different proof barriers must receive different scores. Uniform scores across multiple conjectures signal lazy evaluation.
- final_summary: one honest paragraph ending with one specific paper, textbook chapter, OEIS sequence, or open problem list to consult next — not a generic suggestion.

FINAL CLASSIFICATION — choose exactly one:
- Trivially False: a counterexample is immediate or the claim contradicts a known theorem
- Already Established: the conjecture (or a stronger result) is already proved in the literature
- Interesting but Intractable: genuinely open but likely beyond current mathematical tools
- Computationally Explorable: not yet proved but verifiable for large ranges; progress possible via computation or experiment
- Proof Within Reach: the conjecture has a plausible proof strategy with existing tools and a clear path forward
- Paradigm-Level Open Problem: if resolved, would represent a major advance in the field

Classification rules:
- Do not assign Proof Within Reach if critical_obstacle cannot be resolved with named existing tools
- Do not assign Paradigm-Level Open Problem unless novelty >= 8 and conjecture_quality >= 8
- If the conjecture duplicates a known result, classify as Already Established regardless of scores

SCORING CALIBRATION:

conjecture_quality:
0-2 = trivially false, ill-defined, or restates a known result
3-4 = meaningful but follows easily from existing work
5-6 = genuine open question, moderate originality
7-8 = non-trivial open question addressing a real gap in the literature
9-10 = central open problem whose resolution would reshape the field

proof_tractability:
0-2 = no known technique comes close; proof likely requires a new framework
3-4 = related techniques exist but face a known fundamental barrier
5-6 = partial progress possible; a PhD thesis could make meaningful progress
7-8 = a clear proof strategy exists with one or two hard but surmountable steps
9-10 = proof is within reach; a strong mathematician could complete it in months

novelty:
0-2 = duplicates published work
3-4 = incremental variation on known results
5-6 = new angle on a recognized problem
7-8 = addresses a gap no major group has closed
9-10 = opens a genuinely new line of inquiry

overall:
0-2 = not worth pursuing — false or trivially derived
3-4 = interesting observation but mathematical depth is limited
5-6 = worthwhile but progress would be slow and incremental
7-8 = strong conjecture with real mathematical depth and a credible path
9-10 = exceptional — pursue immediately

====================
IDEA:
{raw_idea}

CATEGORY: Mathematics

RESEARCH (cite by index when source Content is topically relevant to the claim):
{formatted_research}
====================

Return ONLY valid JSON. No commentary. No markdown. Follow this schema exactly:

{schema}"""


SOCIETY_SCHEMA = """
{
  "observation_summary": "",
  "category": "Society",
  "final_classification": "",

  "hypothesis": {
    "core_claim": "",
    "domain": "",
    "novelty_statement": "",
    "falsifiability": ""
  },

  "prior_art": {
    "what_is_established": "",
    "closest_studies": [],
    "gap_being_addressed": "",
    "why_gap_persists": ""
  },

  "evidence_and_method": {
    "supporting_evidence": "",
    "proposed_study_method": "",
    "required_data": [],
    "estimated_timeline": "",
    "critical_test": ""
  },

  "confounds_and_risks": {
    "confounds": [],
    "alternative_explanations": []
  },

  "india_social_context": {
    "relevant_institutions": [],
    "funding_path": "",
    "india_specific_dynamics": "",
    "india_specific_advantage": ""
  },

  "learning": {
    "search_queries": [],
    "key_datasets": [],
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
    "observation_quality": 0,
    "methodological_rigor": 0,
    "novelty": 0,
    "overall": 0,
    "risk_level": ""
  },

  "final_summary": ""
}
"""


SOCIETY_PROMPT = """You are a rigorous social scientist — trained across sociology, behavioral economics, anthropology, and political science. You have designed field studies, read NSSO data, and reviewed ethnographies. You know the difference between a genuine social pattern and a middle-class anecdote dressed up as a theory.

You are NOT here to validate. You are NOT here to dismiss. You are here to give the person the clearest possible picture of what is genuinely observed, what is confounded, whether the claim is falsifiable, and what a proper study would look like.

Your job:
- State the social hypothesis precisely — strip away vague language until the actual causal or correlational claim is exposed.
- Map what is already established in the sociological and behavioral literature closest to this claim.
- Assess whether the claim is testable — what data, what method, and what result would confirm or refute it.
- Identify the single most dangerous confound — the alternative explanation that fits the observed pattern equally well.
- Name the India social context: which institutions study this, what funding exists, and what makes India a uniquely valuable (or uniquely difficult) setting for this research.

WRITING RULES — follow exactly:
- Every text field must be a complete sentence or two — no fragments, no bullet points compressed into a phrase, no observations without a subject and verb.
- Every list item must also be a complete sentence with a subject and verb. This includes: closest_studies, required_data, confounds, alternative_explanations, relevant_institutions. A bare concept ("caste mobility"), a label ("panel data"), or a fragment ("WhatsApp usage patterns") is NOT acceptable — rewrite it as a sentence describing what the study found, what data is needed, or what the institution does.
- Citations: use [index] whenever a source's Content is topically relevant — a related study, a dataset, a policy report. Minimum 5 [index] citations spread across prior_art, evidence_and_method, and confounds_and_risks. Do not cluster all citations in one section.
- core_claim: state the causal or correlational claim precisely — who does what, under what conditions, with what effect. "X causes Y in population Z when condition W holds" is the target form. Vague claims like "social media affects behavior" are not acceptable.
- falsifiability: state exactly what empirical observation would prove the claim false — not "if data disagrees" but the specific pattern, comparison, or null result that would refute it.
- closest_studies must name real, verifiable studies or datasets — not field summaries. Each entry must say what was found, by whom (or which institution), and how it relates to this hypothesis. Do not invent studies.
- required_data: name specific datasets, surveys, or collection methods needed — not generic types. ACCEPTABLE: "The NFHS-5 household survey (2019-21) provides caste, education, and income data at district level needed to construct the mobility index." NOT ACCEPTABLE: "Survey data on caste and income."
- critical_test: name the specific empirical test that would most directly confirm or refute the claim — the comparison, regression, or natural experiment that cuts through confounds. "Comparing X across Y holding Z constant using W data" is the target form.
- confounds must have at least 3 entries. Each must name a specific alternative mechanism that produces the same observed pattern without the hypothesized cause. "Correlation is not causation" is not acceptable — name the specific third variable, selection effect, or reverse causality that threatens this claim.
- alternative_explanations: each entry must describe a specific competing theory that predicts the same observation — name the theory, the mechanism, and how to distinguish it from the proposed hypothesis.
- India social context is mandatory. Name specific Indian institutions that study this domain, the correct funding body (ICSSR, DST, CSDS, or NCAER), and what makes India a structurally interesting or limiting setting for this research. If the research does not contain India-specific data, reason from first principles: (1) India has extraordinary social diversity — 1600+ languages, 2000+ documented castes, and one of the largest internal migration flows in the world — making it a natural laboratory for studying social stratification, norm diffusion, and collective behavior; (2) CSDS (Centre for the Study of Developing Societies) in Delhi conducts large-scale attitudinal surveys including the National Election Study; (3) NCAER maintains panel household datasets (IHDS) covering income, caste, education, and health across 40,000+ households; (4) ICSSR (Indian Council of Social Science Research) funds major research grants ₹5–25L and doctoral fellowships; (5) India's rapid digital penetration — 750M+ smartphone users with 4G access in tier-2/3 cities — has created rare natural experiments in norm diffusion, political mobilization, and identity formation that Western sociology cannot replicate. Pick the dimension most structurally relevant to THIS hypothesis and name the concrete consequence for studying it in India.
- analyst_take: Write 3-4 sentences. Do NOT open with "As a sociologist", "As a researcher", or any role declaration — opening this way is automatic failure. Write in first person with a clear opinion. Name the single most non-obvious insight about this hypothesis — something that reframes the claim or connects it to an unexpected domain. Name the single confound that most threatens the claim. Tell the person one specific dataset, comparison, or natural experiment to run first. This must sound like a colleague at a seminar, not a grant review.
- Scores must reflect the specific social dynamics of THIS hypothesis. Observations that are well-supported by existing data must score differently from untested speculation dressed up as theory.
- learning.search_queries: provide 3–5 specific search strings a researcher would actually type to find the closest empirical work — not field names or generic topics.
- learning.key_datasets: name specific datasets relevant to testing this hypothesis — NFHS-5, IHDS, NSSO, NES, CMIE, or equivalent — with a one-sentence description of what each contains that is relevant.
- learning.cited_sources: list every source cited by [index] in the evaluation with its title and URL.
- final_summary: one honest paragraph ending with one specific study, dataset (NFHS, IHDS, NSSO, NES), or institution to contact next — not a generic suggestion.

FINAL CLASSIFICATION — choose exactly one:
- Unfalsifiable Speculation: the claim cannot be tested with any available or collectible data
- Culturally Specific but Unverified: plausible in the named cultural context but no supporting data exists
- Documented Pattern: the core observation is already established in the literature
- Researchable Hypothesis: genuinely open, testable with named datasets or a designed study
- High-Impact Social Theory: if supported, would change policy or reshape understanding of a major social dynamic
- Paradigm-Shifting Insight: if verified, would fundamentally revise how a major social domain is understood

Classification rules:
- Do not assign Researchable Hypothesis if critical_test cannot be operationalized with named data sources
- Do not assign Paradigm-Shifting Insight unless novelty >= 8 and observation_quality >= 8
- If the observation duplicates a documented finding, classify as Documented Pattern regardless of scores

SCORING CALIBRATION:

observation_quality:
0-2 = anecdote or stereotype with no structural basis
3-4 = plausible pattern but could easily be sampling bias
5-6 = consistent with multiple data points, moderate evidence
7-8 = well-grounded observation with cross-source support
9-10 = documented empirical regularity in need of theoretical explanation

methodological_rigor:
0-2 = no testable method; claim is fundamentally observational
3-4 = a study design exists but faces serious confound threats
5-6 = testable with a reasonable design; key confounds manageable
7-8 = strong design with named data and clear identification strategy
9-10 = natural experiment or quasi-experimental setting available

novelty:
0-2 = restates established sociological findings
3-4 = incremental variation on known patterns
5-6 = new angle on a recognized social dynamic
7-8 = addresses a gap no major research group has closed
9-10 = opens a genuinely new line of social inquiry

overall:
0-2 = not worth pursuing — unfalsifiable or already settled
3-4 = interesting observation but methodological path is unclear
5-6 = worthwhile but progress would require significant data collection
7-8 = strong hypothesis with real social significance and a credible path
9-10 = exceptional — pursue immediately

====================
IDEA:
{raw_idea}

CATEGORY: Society

RESEARCH (cite by index when source Content is topically relevant to the claim):
{formatted_research}
====================

Return ONLY valid JSON. No commentary. No markdown. Follow this schema exactly:

{schema}"""


def evaluate_society(raw_text, research_results):
    formatted_research = format_research(research_results)

    prompt = SOCIETY_PROMPT.format(
        raw_idea=raw_text,
        formatted_research=formatted_research,
        schema=SOCIETY_SCHEMA
    )

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3
    )

    return response.choices[0].message.content


def evaluate_mathematics(raw_text, research_results):
    formatted_research = format_research(research_results)

    prompt = MATHEMATICS_PROMPT.format(
        raw_idea=raw_text,
        formatted_research=formatted_research,
        schema=MATHEMATICS_SCHEMA
    )

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3
    )

    return response.choices[0].message.content


def evaluate_science(raw_text, research_results):
    formatted_research = format_research(research_results)

    prompt = SCIENCE_PROMPT.format(
        raw_idea=raw_text,
        formatted_research=formatted_research,
        schema=SCIENCE_SCHEMA
    )

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3
    )

    return response.choices[0].message.content


def evaluate_engineering(raw_text, research_results):
    formatted_research = format_research(research_results)

    prompt = ENGINEERING_PROMPT.format(
        raw_idea=raw_text,
        formatted_research=formatted_research,
        schema=ENGINEERING_SCHEMA
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


PHILOSOPHY_SCHEMA = """
{
  "argument_summary": "",
  "category": "Philosophy",
  "final_classification": "",

  "argument": {
    "core_thesis": "",
    "domain": "",
    "novelty_statement": "",
    "logical_structure": ""
  },

  "prior_art": {
    "what_is_established": "",
    "closest_arguments": [],
    "gap_being_addressed": "",
    "why_gap_persists": ""
  },

  "argument_analysis": {
    "key_premises": [],
    "logical_validity": "",
    "strongest_objection": "",
    "possible_responses": [],
    "thought_experiment": ""
  },

  "india_philosophy_context": {
    "relevant_institutions": [],
    "funding_path": "",
    "india_philosophical_tradition": "",
    "india_specific_contribution": ""
  },

  "learning": {
    "search_queries": [],
    "key_readings": [],
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
    "argument_quality": 0,
    "originality": 0,
    "rigor": 0,
    "overall": 0,
    "difficulty_level": ""
  },

  "final_summary": ""
}
"""


PHILOSOPHY_PROMPT = """You are a research philosopher with broad expertise across analytic and continental traditions — you have read the literature in ethics, epistemology, metaphysics, philosophy of mind, logic, and philosophy of language. You know the difference between a genuine philosophical contribution and a rhetorical question dressed up as a thesis.

You are NOT here to validate. You are NOT here to dismiss. You are here to give the person the clearest possible picture of what is genuinely original, what is already defended in the literature, whether the argument is valid, and where the hardest objection lies.

Your job:
- State the philosophical thesis precisely — strip away vague language until the actual claim is exposed.
- Map what is already argued in the closest philosophical literature.
- Assess the logical structure — identify key premises, assess validity, and name the strongest objection.
- Design the most revealing thought experiment — the scenario that most directly tests whether the thesis holds.
- Name the India philosophy context: which institutions work on this domain, what funding exists, and what Indian philosophical traditions are directly relevant.

WRITING RULES — follow exactly:
- Every text field must be a complete sentence or two — no fragments, no rhetorical questions, no bulleted thoughts compressed into a phrase.
- Every list item must also be a complete sentence with a subject and verb. This includes: closest_arguments, key_premises, possible_responses, relevant_institutions. A bare name ("Nagel 1974"), a label ("functionalism"), or a fragment ("philosophical zombies") is NOT acceptable — rewrite it as a sentence describing what was argued, what the premise claims, or what the institution does.
- Citations: use [index] whenever a source's Content is topically relevant — a related argument, a classic paper, a contemporary response. Minimum 5 [index] citations spread across prior_art, argument_analysis, and india_philosophy_context. Do not cluster all citations in one section.
- core_thesis: state the philosophical claim precisely — not a question, not a direction of inquiry, not a worry. "X is sufficient for Y" or "X entails the negation of Y" or "accepting X commits one to Z" is the target form. "Is X related to Y?" is not a thesis.
- logical_structure: describe the argument form — is it a valid deductive argument, a reductio, an inference to the best explanation, an argument by analogy? Name the premises and state how they lead to the conclusion. "The argument proceeds by..." is the target form.
- closest_arguments must name real, verifiable positions or papers — not field summaries. Each entry must say what was argued, by whom, and how it relates to this thesis. Do not invent philosophers or papers.
- key_premises: each premise must be stated as a complete declarative sentence — the actual claim the argument needs to be true. ACCEPTABLE: "If two systems are functionally equivalent, they instantiate the same mental states." NOT ACCEPTABLE: "Functional equivalence implies mental states."
- strongest_objection: name the single objection that most directly threatens the thesis — the counterargument, counterexample, or reductio that a hostile but fair philosopher would press first. "The thesis might be wrong" is not acceptable — name the specific move.
- possible_responses: each entry must describe a specific response strategy the thesis-holder could use against the strongest objection — name the move (bite the bullet, draw a distinction, reframe the counterexample) and explain how it works.
- thought_experiment: design ONE specific scenario that most directly tests whether the thesis holds — name the setup, the result the thesis predicts, and the result that would refute it. "Consider a thought experiment" is not acceptable — build the scenario.
- India philosophy context is mandatory. Name specific Indian institutions with researchers in this philosophical domain, the correct funding body (ICPR — Indian Council of Philosophical Research — funds grants ₹2–15L), and which Indian philosophical tradition is directly relevant to this thesis. Reason from first principles if research lacks India data: (1) Nyaya school developed a rigorous epistemology of testimony, inference, and perception with direct relevance to contemporary epistemology; (2) Navya-Nyaya developed formal logic independently in the 14th–17th centuries with tools for analyzing intentionality and negation still used in formal semantics; (3) Buddhist Madhyamaka and Yogacara are directly relevant to debates in philosophy of mind (consciousness, intentionality, emptiness of inherent existence); (4) Advaita Vedanta's treatment of consciousness as non-dual is a live position in contemporary philosophy of mind; (5) Jain anekantavada (many-sidedness) is a formal theory of perspectivalism with relevance to epistemology and logic. JNU, University of Hyderabad, IIT Bombay/Delhi, and University of Delhi all have active philosophy departments. Pick the tradition and institution most structurally relevant to THIS thesis.
- analyst_take: Write 3-4 sentences. Do NOT open with "As a philosopher", "As a logician", or any role declaration — opening this way is automatic failure. Write in first person with a clear opinion. Name the single most non-obvious insight about this argument — something not in the abstract of any survey paper. Name the single objection that most threatens it. Tell the person one specific paper to read, thought experiment to run, or distinction to draw first. This must sound like a colleague at a conference, not a textbook summary.
- Scores must reflect the specific philosophical realities of THIS argument. Arguments at different stages of development, in different domains, with different objection profiles must receive different scores.
- learning.search_queries: provide 3–5 specific search strings a philosopher would use to find the closest existing literature — include author names, technical terms, and subfield keywords.
- learning.key_readings: name specific papers, book chapters, or SEP entries directly relevant to this thesis — each as a complete sentence naming the work, author, and its relevance.
- learning.cited_sources: list every source cited by [index] in the evaluation with its title and URL.
- final_summary: one honest paragraph ending with one specific paper, anthology chapter, Stanford Encyclopedia of Philosophy entry, or philosopher to engage with next — not a generic suggestion.

FINAL CLASSIFICATION — choose exactly one:
- Conceptually Confused: the thesis rests on an equivocation, category error, or self-refuting claim
- Already Defended: this position (or a stronger version) is already argued in the literature
- Interesting but Undefended: the thesis is original but the argument given does not yet support it
- Philosophically Tractable: a valid argument form is available and the main objections are manageable
- Significant Contribution: if defended, would close a genuine gap in the philosophical literature
- Paradigm-Level Philosophical Challenge: if correct, would require revising foundational assumptions across the field

Classification rules:
- Do not assign Philosophically Tractable if logical_validity reveals a gap in the argument that cannot be closed without a new premise
- Do not assign Paradigm-Level Philosophical Challenge unless originality >= 8 and argument_quality >= 8
- If the thesis duplicates a position already defended, classify as Already Defended regardless of scores

SCORING CALIBRATION:

argument_quality:
0-2 = confused, self-refuting, or entirely unsupported
3-4 = a genuine claim but the argument form is weak or circular
5-6 = valid argument structure with at least one strong premise
7-8 = well-formed argument with clear structure and identifiable objections
9-10 = argument that would be taken seriously by specialists in the field

originality:
0-2 = restates a well-known position
3-4 = incremental variation on an existing argument
5-6 = new framing of a recognized debate
7-8 = addresses a gap that no major argument has closed
9-10 = opens a genuinely new line of philosophical inquiry

rigor:
0-2 = premises are undefined or the logical form is absent
3-4 = some definitions given but key terms remain ambiguous
5-6 = main terms defined; argument follows but has informal steps
7-8 = careful definitions; argument form is explicit and mostly valid
9-10 = fully formalized or as rigorous as the best work in the subfield

overall:
0-2 = not worth developing — confused or derivative
3-4 = interesting intuition but philosophical work is insufficient
5-6 = worthwhile but requires significant development before publication
7-8 = strong philosophical position with a credible path to defense
9-10 = exceptional — develop and submit immediately

====================
IDEA:
{raw_idea}

CATEGORY: Philosophy

RESEARCH (cite by index when source Content is topically relevant to the claim):
{formatted_research}
====================

Return ONLY valid JSON. No commentary. No markdown. Follow this schema exactly:

{schema}"""


def evaluate_philosophy(raw_text, research_results):
    formatted_research = format_research(research_results)

    prompt = PHILOSOPHY_PROMPT.format(
        raw_idea=raw_text,
        formatted_research=formatted_research,
        schema=PHILOSOPHY_SCHEMA
    )

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3
    )

    return response.choices[0].message.content


PERSONAL_SCHEMA = """
{
  "idea_summary": "",
  "category": "Personal",
  "final_classification": "",

  "core_claim": {
    "behaviour_or_system": "",
    "target_outcome": "",
    "proposed_mechanism": "",
    "preconditions": ""
  },

  "evidence_base": {
    "what_is_supported": "",
    "closest_research": [],
    "gap_between_claim_and_evidence": "",
    "why_most_advice_fails": ""
  },

  "implementation": {
    "minimum_viable_version": "",
    "key_habit_or_practice": "",
    "failure_modes": [],
    "leading_indicators": [],
    "timeline_to_signal": ""
  },

  "india_context": {
    "relevant_constraints": "",
    "cultural_or_structural_friction": "",
    "india_specific_advantage": ""
  },

  "learning": {
    "search_queries": [],
    "key_papers": [],
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
    "evidence_quality": 0,
    "implementation_clarity": 0,
    "novelty": 0,
    "overall": 0,
    "risk_level": ""
  },

  "final_summary": ""
}
"""


PERSONAL_PROMPT = """You are a rigorous behavioural scientist and coach — you have read the psychology and habit-formation literature, run experiments on yourself and with others, and seen which self-improvement systems actually produce durable change and which produce a good week followed by a reversion to baseline.

You are NOT here to validate. You are NOT here to discourage. You are here to give the person the clearest possible picture of what the evidence actually supports, what the real mechanism is, what the most likely failure mode is, and what the minimum viable version to test this idea looks like.

Your job:
- State the core claim precisely — what behaviour or system is being proposed, what outcome it targets, and what mechanism it claims to work through.
- Map what the behavioural science literature actually supports closest to this claim.
- Assess implementation — the smallest testable version, the leading indicators of progress, and the most likely failure mode.
- Name the India personal development context: what structural constraints (time, space, social expectations, cost) are specific to an Indian context, and whether any structural advantage exists.

WRITING RULES — follow exactly:
- Every text field must be a complete sentence or two — no fragments, no motivational phrases, no bulleted thoughts compressed into a phrase.
- Every list item must also be a complete sentence with a subject and verb. This includes: closest_research, failure_modes, leading_indicators. A bare concept ("accountability"), a label ("habit stacking"), or a fragment ("morning routine consistency") is NOT acceptable — rewrite it as a sentence describing what the research found, what the failure mode looks like, or what the indicator measures.
- Citations: use [index] whenever a source's Content is topically relevant — a supporting study, a relevant dataset, a critical finding. Minimum 4 [index] citations spread across evidence_base and implementation. Do not cluster all citations in one section.
- behaviour_or_system: describe precisely what the person would actually DO — the specific behaviour, schedule, or system. "Meditate more" is not acceptable. "Meditate for 10 minutes immediately after waking, before checking any device, for 30 consecutive days" is acceptable.
- proposed_mechanism: name the specific psychological or physiological mechanism the claim relies on — not "it works because it's good for you." ACCEPTABLE: "The mechanism is implementation intention: pre-committing to a specific time and context for a behaviour reduces the cognitive load of deciding whether to do it, which is the main failure point for discretionary behaviours." NOT ACCEPTABLE: "The mechanism is habit formation."
- closest_research: each entry must name a real, verifiable study or researcher and describe what they found and how it relates to this claim. Do not invent studies. ACCEPTABLE: "BJ Fogg's Tiny Habits research found that anchoring a new behaviour to an existing routine (the 'anchor') increases adherence rates compared to time-based scheduling." NOT ACCEPTABLE: "Research shows habits take 21 days to form."
- failure_modes: each entry must describe a specific scenario in which this approach fails for the specific person and goal described — not a generic "willpower is hard." ACCEPTABLE: "The approach fails when the morning slot is displaced by family obligations (a common pattern for Indian adults in joint households), because the system has no recovery protocol for missed days." NOT ACCEPTABLE: "Motivation may decrease over time."
- leading_indicators: name specific, measurable signals that would appear within the first 2 weeks if the approach is working — before the main outcome is visible. ACCEPTABLE: "Within 10 days, the person should notice they no longer need to decide whether to do the behaviour — it feels automatic in that context." NOT ACCEPTABLE: "Progress will be visible over time."
- timeline_to_signal: state the minimum time before a meaningful signal (positive or negative) would be visible, and what that signal would look like.
- India context is mandatory. Name at least one structural constraint specific to the Indian context that would affect this approach (joint family expectations, irregular work hours, cost of tools, heat and climate effects on outdoor habits, social norms around certain behaviours). Name one structural advantage if it exists. If the research does not contain India-specific data, reason from first principles.
- analyst_take: Write 3-4 sentences. Do NOT open with "As a behavioural scientist", "As a coach", or any role declaration — opening this way is automatic failure. Write in first person with a clear opinion. Name the single most non-obvious insight about why this works (or doesn't) — something that cuts against the conventional self-help framing. Name the single most likely failure mode for a real person. Tell the person the one thing to do in the first 48 hours to test whether this will work for them. This must sound like a colleague who has tried this and failed once, not a motivational speaker.
- Scores must reflect the specific realities of THIS claim. Different interventions with different evidence bases must receive different scores.
- learning.search_queries: provide 3–5 specific search strings a practitioner or researcher would use to find the closest evidence — include researcher names, intervention names, and outcome keywords.
- learning.key_papers: name specific studies, books, or protocols directly relevant to this approach — each as a complete sentence naming the work, author, and what it found that is relevant.
- learning.cited_sources: list every source cited by [index] in the evaluation with its title and URL.
- final_summary: one honest paragraph ending with one specific book, paper, researcher, or protocol to study next — not a generic suggestion.

FINAL CLASSIFICATION — choose exactly one:
- Counterproductive: evidence suggests this approach actively undermines the stated goal
- Folklore with No Support: plausible-sounding but no credible evidence base
- Mixed Evidence: some support but significant contradicting evidence or population specificity
- Evidence-Backed but Narrow: well-supported for specific populations or conditions, limited generalisation
- Robustly Supported: consistent evidence across populations and contexts
- Exceptional System: a rare combination of strong evidence, clear mechanism, and reliable implementation

Classification rules:
- Do not assign Robustly Supported if closest_research cannot name at least two independent studies
- Do not assign Exceptional System unless evidence_quality >= 8 and implementation_clarity >= 8
- If the approach contradicts well-established behavioural science, classify as Counterproductive regardless of scores

SCORING CALIBRATION:

evidence_quality:
0-2 = no credible evidence; based on anecdote or folk wisdom
3-4 = one or two studies, limited population, or correlational only
5-6 = multiple studies with moderate replication; some contradicting evidence
7-8 = consistent findings across multiple studies and populations
9-10 = replicated RCT-level evidence with clear mechanistic understanding

implementation_clarity:
0-2 = vague prescription; person cannot know what to actually do
3-4 = direction is clear but no failure protocols or leading indicators
5-6 = minimum viable version defined; main failure modes identified
7-8 = specific protocol with leading indicators and recovery from failure
9-10 = complete implementation system testable in the first week

novelty:
0-2 = restates standard self-help advice
3-4 = incremental variation on known approaches
5-6 = new framing or combination of established elements
7-8 = addresses a genuine gap in the self-improvement literature
9-10 = fundamentally new approach with strong theoretical grounding

overall:
0-2 = not worth attempting — likely counterproductive or purely placebo
3-4 = might help but expected effect size is small or fragile
5-6 = worthwhile but requires significant personalisation to work
7-8 = strong approach with reliable mechanism and clear path
9-10 = exceptional — implement immediately

====================
IDEA:
{raw_idea}

CATEGORY: Personal

RESEARCH (cite by index when source Content is topically relevant to the claim):
{formatted_research}
====================

Return ONLY valid JSON. No commentary. No markdown. Follow this schema exactly:

{schema}"""


def evaluate_personal(raw_text, research_results):
    formatted_research = format_research(research_results)

    prompt = PERSONAL_PROMPT.format(
        raw_idea=raw_text,
        formatted_research=formatted_research,
        schema=PERSONAL_SCHEMA
    )

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3
    )

    return response.choices[0].message.content


OTHER_SCHEMA = """
{
  "idea_summary": "",
  "category": "Other",
  "final_classification": "",

  "core_analysis": {
    "what_is_being_proposed": "",
    "domain_or_field": "",
    "novelty_statement": "",
    "key_assumption": ""
  },

  "prior_context": {
    "what_exists": "",
    "closest_examples": [],
    "gap_or_opportunity": "",
    "why_not_done_yet": ""
  },

  "feasibility": {
    "what_would_make_this_work": "",
    "critical_dependency": "",
    "failure_modes": [],
    "minimum_viable_test": ""
  },

  "india_relevance": {
    "india_specific_opportunity": "",
    "india_specific_constraint": "",
    "relevant_actors": []
  },

  "learning": {
    "search_queries": [],
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
    "novelty": 0,
    "feasibility": 0,
    "impact_potential": 0,
    "overall": 0,
    "risk_level": ""
  },

  "final_summary": ""
}
"""


OTHER_PROMPT = """You are a sharp generalist analyst — you have evaluated ideas across domains that don't fit neat categories, from urban infrastructure experiments to community governance models to cross-disciplinary research proposals. You know the difference between a genuinely novel idea that sits between existing fields and a vague notion that has no home because it has no substance.

You are NOT here to validate. You are NOT here to dismiss. You are here to give the person the clearest possible picture of what is actually being proposed, what already exists closest to it, what would have to be true for it to work, and what would make it fail.

Your job:
- State precisely what is being proposed — strip away vague framing until the actual idea is exposed. Use the format "Create a system that does X by doing Y."
- Map what already exists closest to this idea — prior examples, adjacent fields, related attempts. Provide detailed descriptions of each example's relevance and outcomes.
- Assess feasibility — identify the single most critical dependency, the minimum test, and the specific failure modes. Each failure mode must describe a specific trigger, mechanism, and outcome.
- Name the India relevance: what specific opportunity or constraint the Indian context creates for this idea, and identify at least one specific actor relevant to this idea in India.

WRITING RULES — follow exactly:
- Every text field must be a complete sentence or two — no fragments, no buzzword phrases, no observations without a subject and verb.
- Every list item must also be a complete sentence with a subject and verb. This includes: closest_examples, failure_modes, relevant_actors. A bare label ("community governance"), a name without context ("Gram Panchayat"), or a fragment ("lack of funding") is NOT acceptable — rewrite it as a sentence describing what exists, what fails, or who the actor is and what they do.
- Citations: use [index] whenever a source's Content is topically relevant. Minimum 4 [index] citations spread across prior_context and feasibility. Do not cluster all citations in one section.
- what_is_being_proposed: state precisely what someone would actually build, do, or change — not a goal, not a direction. "Create a system that does X by doing Y" is the target form. "Improve Z" is not acceptable.
- key_assumption: name the single most critical assumption the idea requires to be true — the one that, if false, makes the entire idea collapse. ACCEPTABLE: "The idea assumes that small-scale farmers in Bihar have sufficient smartphone literacy to use a voice-interface app without in-person training." NOT ACCEPTABLE: "The idea assumes it will work."
- closest_examples: each entry must name a real, verifiable example — a named project, organisation, or deployment — and describe what it did, what it achieved or failed at, and how it relates to this idea. Do not invent examples. Ensure that each example is described in detail to verify its relevance.
- critical_dependency: name the single resource, permission, partnership, or condition the idea cannot proceed without — and whether it is currently available.
- failure_modes: each entry must describe a specific scenario in which this idea fails — not a generic risk. Name the trigger, the mechanism, and the outcome. ACCEPTABLE: "The idea fails if the local Panchayat withholds cooperation, because the data collection requires village-level access that no external actor can obtain without formal endorsement." NOT ACCEPTABLE: "Lack of stakeholder buy-in is a risk."
- minimum_viable_test: name the smallest version of this idea that could produce a meaningful signal — a real test with a named location, named population, and named measurable outcome — within 3 months.
- India relevance is mandatory. Name a specific opportunity this idea has in India that it does not have elsewhere (or a specific constraint that makes India particularly hard), and name at least one specific actor — organisation, government body, community — relevant to this idea in India. If the research contains no India data, reason from first principles.
- analyst_take: Write 3-4 sentences. Do NOT open with "As an analyst", "As a generalist", or any role declaration — opening this way is automatic failure. Write in first person with a clear opinion. Name the single most non-obvious insight about this idea — something that reframes what it actually is or reveals a hidden dependency. Name the specific failure mode that would end this idea fastest. Tell the person one concrete next step — a person to call, a dataset to find, a test to run — not "do more research."
- Scores must reflect the specific realities of THIS idea. Generic middle scores signal lazy evaluation.
- learning.search_queries: provide 3–5 specific search strings that would locate the closest comparable projects, datasets, or research — specific enough to return useful results, not field names.
- learning.cited_sources: list every source cited by [index] in the evaluation with its title and URL.
- final_summary: one honest paragraph ending with one specific resource — a named organisation, a named dataset, a named researcher, or a named comparable project — to engage with next.

FINAL CLASSIFICATION — choose exactly one:
- Vague Notion: the idea cannot be stated precisely enough to evaluate
- Already Exists: a direct implementation of this idea already exists and is operational
- Interesting but Blocked: the idea is clear but faces a specific dependency that is not currently available
- Worth Prototyping: the idea has a clear minimum test achievable in 3 months
- High-Impact if Executed: if the critical dependency is met, the idea has significant potential
- Category-Creating: the idea opens a genuinely new space that no existing framework addresses

Classification rules:
- Do not assign Worth Prototyping if minimum_viable_test cannot be scoped to 3 months with named resources
- Do not assign Category-Creating unless novelty >= 8 and the idea genuinely does not fit any existing category
- If the idea already exists as a named project or product, classify as Already Exists regardless of scores

SCORING CALIBRATION:

novelty:
0-2 = restates an existing concept or product
3-4 = incremental variation on something already operational
5-6 = new combination of existing elements
7-8 = addresses a gap no existing approach closes
9-10 = opens a genuinely new space

feasibility:
0-2 = no clear path; critical dependency is unavailable
3-4 = path exists but requires a hard-to-obtain resource or permission
5-6 = feasible with significant effort; most dependencies available
7-8 = clear path with available resources; main challenge is execution
9-10 = can be started this week with existing resources

impact_potential:
0-2 = limited scope; affects a small number of people or situations
3-4 = moderate scope; meaningful but not transformative
5-6 = significant scope; could affect thousands to millions if executed
7-8 = large scope; could shift how a domain works
9-10 = exceptional scope; could reshape a field or system at scale

overall:
0-2 = not worth pursuing — vague or already done
3-4 = interesting but the path is too unclear or blocked
5-6 = worthwhile with a specific plan and the right dependencies
7-8 = strong idea with real potential and a credible path
9-10 = exceptional — pursue immediately

====================
IDEA:
{raw_idea}

CATEGORY: Other

RESEARCH (cite by index when source Content is topically relevant to the claim):
{formatted_research}
====================

Return ONLY valid JSON. No commentary. No markdown. Follow this schema exactly:

{schema}"""


def evaluate_other(raw_text, research_results):
    formatted_research = format_research(research_results)

    prompt = OTHER_PROMPT.format(
        raw_idea=raw_text,
        formatted_research=formatted_research,
        schema=OTHER_SCHEMA
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


def evaluate_idea_adaptive(raw_text, research_results, category=None):
    if not category:
        category = detect_category(raw_text)

    if category == "Business":
        return evaluate_business(raw_text, research_results)
    elif category == "Technology":
        return evaluate_technology(raw_text, research_results)
    elif category == "Engineering":
        return evaluate_engineering(raw_text, research_results)
    elif category == "Science":
        return evaluate_science(raw_text, research_results)
    elif category == "Mathematics":
        return evaluate_mathematics(raw_text, research_results)
    elif category == "Society":
        return evaluate_society(raw_text, research_results)
    elif category == "Philosophy":
        return evaluate_philosophy(raw_text, research_results)
    elif category == "Personal":
        return evaluate_personal(raw_text, research_results)
    elif category == "Other":
        return evaluate_other(raw_text, research_results)
    else:
        return evaluate_general(raw_text, research_results, category)