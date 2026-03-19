import os
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

ALLOWED_CATEGORIES = [
    "Business",
    "Engineering",
    "Science",
    "Social",
    "Philosophy",
    "Personal",
    "Other"
]

def detect_category(raw_text):
    prompt = f"""
You are a classification system.

Classify the following idea into ONE of the categories below.

Return ONLY the category word.

Allowed categories:
Business
Engineering
Science
Social
Philosophy
Personal
Other

Idea:
{raw_text}
"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.0
    )

    category = response.choices[0].message.content.strip()

    if category not in ALLOWED_CATEGORIES:
        return "Other"

    return category


DOMAIN_LENSES = {

"Business": """
BUSINESS QUANTITATIVE REQUIREMENTS:

You MUST provide structured quantitative analysis.

1. TAM Estimation:
   - State assumptions clearly.
   - Estimate order-of-magnitude range.

2. Pricing Model:
   - Provide assumed price range.
   - Justify based on positioning.

3. Cost Structure:
   - Break down major cost components.
   - Estimate cost per unit using assumptions.
   - Estimate gross margin range.

4. Unit Economics:
   - Estimate CAC and LTV using assumptions.
   - Define break-even condition.

5. Sensitivity Analysis:
   - Choose one key variable.
   - Show impact if -20% and +20%.

6. Quantitative Kill Conditions:
   - Provide at least one numeric threshold that makes the model non-viable.

All numbers must:
- Be assumption-based.
- Avoid fabricated precision.
- Use ranges where uncertain.
""",

"Engineering": """
ENGINEERING QUANTITATIVE REQUIREMENTS:

You MUST provide structured quantitative analysis.

1. Efficiency Estimates:
   - Provide estimated efficiency range.
   - State assumptions.

2. Comparison With Alternatives:
   - Provide approximate benchmark values.
   - Explain relative advantage/disadvantage.

3. Cost Per Unit Estimate:
   - Provide order-of-magnitude estimate.
   - State assumptions.

4. Physical Constraints:
   - Identify thermodynamic or material limits.

5. Viability Threshold:
   - Define numeric threshold where system becomes impractical.

6. Sensitivity Analysis:
   - Choose one key variable.
   - Show impact if -20% and +20%.

All numbers must:
- Be assumption-based.
- Avoid fabricated precision.
- Use ranges where uncertain.
""",

"Science": """
SCIENTIFIC EVALUATION LENS:

You MUST analyze using scientific reasoning discipline.

1. Hypothesis Structure:
   - Clearly define the central hypothesis.
   - Identify dependent and independent variables.

2. Mechanistic Plausibility:
   - Does the mechanism align with established scientific principles?
   - Identify potential conflicts with known laws or models.

3. Empirical Testability:
   - Define how the hypothesis could be experimentally tested.
   - Identify required measurements or observable outcomes.

4. Falsifiability:
   - Specify what evidence would clearly disprove the hypothesis.

5. Quantitative Framing (if relevant):
   - Propose measurable variables.
   - Estimate order-of-magnitude ranges if applicable.
   - Identify threshold conditions where hypothesis fails.

6. Scalability of Evidence:
   - Would evidence generalize across contexts or remain localized?
""",

"Social": """
SOCIAL / PHILOSOPHY EVALUATION LENS:

1. Intellectual Lineage:
   - Identify closely related theories or thinkers.
   - Clarify whether this idea extends, reframes, or contradicts them.

2. Normative vs Descriptive:
   - Is this explaining how societies function?
   - Or recommending how they should function?
   - Explicitly separate the two.

3. Logical Coherence Test:
   - Identify internal tensions or definitional ambiguity.
   - Does the claim hold universally or only conditionally?

4. Counterexamples:
   - Provide at least one strong historical or conceptual counterexample.
   - Explain whether it weakens or refines the idea.

5. Scope Boundaries:
   - Under what conditions does this idea likely apply?
   - Where does it likely fail?

6. Falsifiability:
   - What evidence would clearly disprove this theory?
   - What observable pattern would contradict it?

7. Structural Stress Test:
   - Analyze short-term vs long-term stability separately.
   - Evaluate whether this mechanism creates hidden instability.
   - Identify a scenario where the mechanism reverses and destabilizes society.

8. Conditional Quantitative Framing:
   If measurable modeling is possible:
   - Propose measurable indicators.
   - Estimate the scale at which the effect becomes significant.
   - Identify a threshold where the hypothesis would likely fail.
   - Use assumption-based reasoning if numbers are uncertain.
""",

"Philosophy": """
SOCIAL / PHILOSOPHY EVALUATION LENS:

1. Intellectual Lineage:
   - Identify closely related theories or thinkers.
   - Clarify whether this idea extends, reframes, or contradicts them.

2. Normative vs Descriptive:
   - Is this explaining how societies function?
   - Or recommending how they should function?
   - Explicitly separate the two.

3. Logical Coherence Test:
   - Identify internal tensions or definitional ambiguity.
   - Does the claim hold universally or only conditionally?

4. Counterexamples:
   - Provide at least one strong historical or conceptual counterexample.
   - Explain whether it weakens or refines the idea.

5. Scope Boundaries:
   - Under what conditions does this idea likely apply?
   - Where does it likely fail?

6. Falsifiability:
   - What evidence would clearly disprove this theory?
   - What observable pattern would contradict it?

7. Structural Stress Test:
   - Analyze short-term vs long-term stability separately.
   - Evaluate whether this mechanism creates hidden instability.
   - Identify a scenario where the mechanism reverses and destabilizes society.

8. Conditional Quantitative Framing:
   If measurable modeling is possible:
   - Propose measurable indicators.
   - Estimate the scale at which the effect becomes significant.
   - Identify a threshold where the hypothesis would likely fail.
   - Use assumption-based reasoning if numbers are uncertain.
""",
"Personal": """
PERSONAL / BEHAVIORAL EVALUATION LENS:

1. Behavioral Mechanism:
   - What psychological principle is this idea relying on?
   - Is it grounded in established behavioral science?

2. Motivation Dynamics:
   - Analyze motivation decay over time.
   - Identify habit formation requirements.
   - Identify friction points.

3. Measurable Outcomes:
   - Define measurable indicators of success.
   - Estimate timeframe for observable change.

4. Adoption Risk:
   - Identify psychological barriers.
   - Identify failure patterns (drop-off, boredom, overload).

5. Conditional Quantitative Framing:
   - If relevant, estimate retention thresholds.
   - Identify minimum engagement level required for effect.

6. Structural Limitation:
   - Is this idea dependent on high intrinsic motivation?
   - Does it scale beyond highly disciplined individuals?
""",

"Other": """
GENERAL ANALYTICAL LENS:

1. Conceptual Clarity:
   - Is the idea clearly defined?
   - Are terms ambiguous?

2. Assumption Audit:
   - Identify hidden assumptions.
   - Evaluate structural soundness.

3. Logical Consistency:
   - Identify internal contradictions.
   - Identify scope limits.

4. Conditional Quantitative Framing (if relevant):
   - Propose measurable indicators.
   - Estimate scale thresholds.

5. Failure Boundary:
   - Identify scenario where idea breaks structurally.
"""
}

SCORE_ANCHORS = """
SCORING CALIBRATION:

Novelty:
0 = mainstream common idea
3 = common recombination
5 = moderate variation
7 = rare framing
9 = highly original
10 = paradigm-level shift

Overall Score:
0-2 = fundamentally weak
3-4 = conceptually unstable
5-6 = interesting but constrained
7-8 = structurally strong with risk
9-10 = breakthrough potential
"""



JSON_SCHEMA = """
{
  "idea_summary": "",
  "category": "",
  "core_analysis": {
    "problem_definition": "",
    "proposed_mechanism": "",
    "key_assumptions": [],
    "structural_weaknesses": [],
    "failure_scenarios": []
  },
  "domain_specific_analysis": {},
  "improvement_directions": {
    "strengthening_actions": [],
    "research_needed": [],
    "validation_tests": []
  },
  "scores": {
    "novelty": 0,
    "feasibility_reasoning": {
      "derived_from_quantitative_analysis": "",
      "threshold_logic": "",
      "score": 0
    },
    "overall": 0,
    "risk_level": ""
  },
  "final_classification": "",
  "verdict_reasoning": ""
}
"""




def evaluate_idea_adaptive(raw_text, research_results):
    category = detect_category(raw_text)
    domain_lens = DOMAIN_LENSES.get(category, DOMAIN_LENSES["Other"])

    formatted_research = ""
    for item in research_results[:10]:
        formatted_research += f"""
Title: {item['title']}
Snippet: {item['snippet']}
"""

    prompt = f"""
You are an Adaptive Idea Intelligence Engine.
COGNITIVE OPERATING MODE:

You are not a general assistant.
You are a rigorous systems-level evaluator.

Rules:
- Do not default to balanced tone for safety.
- If an idea is weak, say it clearly.
- If an idea is strong, justify it structurally.
- Challenge assumptions explicitly.
- Avoid generic phrasing.
- Do not invent specific statistics unless supported by provided research.
- If quantitative estimation is required, use order-of-magnitude reasoning and state assumptions.
- Prefer structural analysis over surface commentary.
- Identify at least one uncomfortable implication of the idea.
- Think in terms of system dynamics (short-term vs long-term effects).

ADVERSARIAL DISCIPLINE:
- Do not default to middle classifications.
- If quantitative logic exposes fragility, downgrade decisively.
- Identify the single strongest argument AGAINST the idea.
- Identify one scenario where the idea backfires severely.
- If the idea is structurally weak, classify as Weak Concept.
- Avoid safe middle ground unless genuinely justified.
- Be willing to assign scores below 4 if warranted.

Depth over politeness.
Precision over verbosity.

When estimating numbers:
- Use approximate reasoning.
- Clearly state assumptions.
- Avoid specific data claims unless present in research context.

====================
IDEA:
{raw_text}

CATEGORY:
{category}

RESEARCH:
{formatted_research}
====================

CORE ANALYSIS:
- Restate idea clearly.
- Define core problem.
- Explain proposed mechanism.
- Extract key assumptions.
- Identify structural weaknesses.
- Identify realistic failure scenarios.

====================

{domain_lens}

====================

{SCORE_ANCHORS}

====================

FINAL CLASSIFICATION:
Choose EXACTLY one:
- Weak Concept
- Interesting but Unproven
- Structurally Promising
- High-Potential Breakthrough
- Conceptually Confused
Classification must align with quantitative and structural analysis.
Do not assign "Structurally Promising" if feasibility score < 5.
Do not assign "High-Potential Breakthrough" unless novelty >= 8 and feasibility >= 6.
FEASIBILITY SCORING RULE:

The feasibility score MUST be derived from the quantitative analysis above.
Explain:
- Which quantitative factors support feasibility.
- Which thresholds create risk.
Then assign a score (0-10) using SCORE_ANCHORS.

Return ONLY valid JSON.
No commentary.
Follow this structure strictly:

{JSON_SCHEMA}
"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.35
    )

    return response.choices[0].message.content