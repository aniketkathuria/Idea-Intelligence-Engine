"""
Multi-category prompt optimization loop.

Run from project root:
    python backend/prompt_optimizer.py --category Business
    python backend/prompt_optimizer.py --category Technology

Each iteration:
  1. Judges all ideas of the given category in DB (Judge 1: structural quality, Judge 2: learning value)
  2. Saves prompt + all outputs + scores to <category>_prompt_history.json
  3. If both judge averages >= THRESHOLD, exits (prompt is good)
  4. Otherwise, fixes the prompt and reruns reprocess
  5. Repeats up to MAX_ITERATIONS times

After running, review the history file and pick the prompt from whichever
iteration produced the best scores.
"""

import os
import sys
import json
import re
import subprocess
import time
from datetime import datetime

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from dotenv import load_dotenv
load_dotenv()

from openai import OpenAI
from core.storage import load_all_ideas

# ── Logging helpers ───────────────────────────────────────────────────────────

def ts():
    return datetime.now().strftime("%H:%M:%S")

def log(msg, indent=0):
    prefix = "  " * indent
    print(f"[{ts()}] {prefix}{msg}", flush=True)

def log_sep(char="-", width=56):
    print(f"[{ts()}] {char * width}", flush=True)

def elapsed(start):
    s = int(time.time() - start)
    return f"{s//60}m {s%60}s" if s >= 60 else f"{s}s"

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

PROJECT_ROOT   = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
EVALUATOR_PATH = os.path.join(PROJECT_ROOT, "core", "evaluator.py")
REPROCESS_PATH = os.path.join(PROJECT_ROOT, "backend", "reprocess.py")

MAX_ITERATIONS      = 12
THRESHOLD           = 8.5   # both judge averages must reach this (85% of 10)
STEP_THRESHOLD      = 0.75  # default: each step must average >= 75% of its max across all ideas
STEP_THRESHOLD_LOW  = 0.50  # relaxed floor for steps where research availability limits the score


# ── Prompt extraction / replacement ───────────────────────────────────────────

def extract_business_prompt():
    with open(EVALUATOR_PATH, "r", encoding="utf-8") as f:
        content = f.read()
    match = re.search(r'BUSINESS_PROMPT = """(.+?)"""', content, re.DOTALL)
    if not match:
        raise ValueError("Could not find BUSINESS_PROMPT in evaluator.py")
    return match.group(1)


def replace_business_prompt(new_prompt):
    with open(EVALUATOR_PATH, "r", encoding="utf-8") as f:
        content = f.read()
    new_content = re.sub(
        r'(BUSINESS_PROMPT = """)(.+?)(""")',
        lambda m: m.group(1) + new_prompt + m.group(3),
        content,
        flags=re.DOTALL
    )
    with open(EVALUATOR_PATH, "w", encoding="utf-8") as f:
        f.write(new_content)



# ── Judge prompts ─────────────────────────────────────────────────────────────

JUDGE1_PROMPT = """
You are a strict structural auditor for a business idea evaluation system.

Your job: check whether this evaluation meets specific quality standards. You are NOT judging the idea — you are grading the evaluation's execution.

MANDATORY THOUGHT PROCESS — work through each criterion before scoring:

STEP 1 — Sentence Quality in List Fields (2 pts)
Check every item in: key_shifts, unique_dynamics, cost_structure, weakest_links items, search_queries.
Ask: Is each item a complete sentence with a subject and verb? A label ("high competition"), a fragment ("growing market"), or a single noun ("regulation") is NOT a sentence.
  2 = Every list item across the entire evaluation is a grammatically complete sentence
  1 = Most are sentences; up to 2 items are fragments or labels
  0 = Three or more list items are fragments, labels, or keywords

STEP 2 — Unit Economics Specificity (3 pts)
Check: tam_estimate, pricing_assumption, gross_margin_range, cac_ltv_estimate, kill_condition.
Ask: Does each field contain an actual number, range, or first-principles estimate with stated logic? "Significant" and "substantial" are not numbers. "Unverified assumption" is a failure.
  3 = All five fields have numbers or explicit first-principles reasoning ("assuming X% of Y population at Z price = ...")
  2 = Four fields have estimates; one is vague or missing
  1 = Two or three fields have estimates; rest are vague or empty
  0 = Majority are vague, empty, or say "unverified assumption"

STEP 3 — Competitive Analysis Depth (2 pts)
Check each player entry: does it name the specific business model (not "offers services"), a specific technical or market edge (not "large user base"), and a specific weakness (not "lacks features")?
  2 = Every player entry has a specific model, specific edge, and specific weakness — none are generic
  1 = At least half the players have specific detail; rest are shallow
  0 = Players named but descriptions are generic across the board

STEP 4 — Weakest Links Specificity (2 pts)
Check each weakest_links entry: is the weakness tied to a structural assumption unique to THIS idea — or is it a generic business risk?
Generic failures: "high competition", "market risk", "user adoption is hard", "scaling is difficult"
  2 = Every weakness names a specific assumption of THIS idea and explains why that assumption is fragile
  1 = At least one weakness is idea-specific; rest are generic
  0 = All weaknesses are generic — could apply to any startup

STEP 5 — Citations (1 pt)
Count [index] citations across the full evaluation text.
  1 = At least 5 [index] citations appear, spread across different sections
  0 = Fewer than 5 citations, or all clustered in one section

SCORING: Add up points from each step. Do not round up. Do not give partial credit within a criterion.

Return ONLY valid JSON — no commentary, no markdown:
{{
  "step1_sentence_quality": <0-2>,
  "step2_unit_economics": <0-3>,
  "step3_competitive_depth": <0-2>,
  "step4_weakest_links": <0-2>,
  "step5_citations": <0-1>,
  "score": <sum of all steps, 0-10>,
  "verdict": "<2-3 sentences naming the specific fields that failed and why>",
  "specific_failures": ["<exact field + exact reason it failed>"],
  "specific_wins": ["<exact field that met the standard and why>"]
}}

IDEA: {raw_idea}

EVALUATION:
{evaluation}
"""


JUDGE2_PROMPT = """
You are a learning value auditor for a business idea evaluation system.

Your job: assess whether this evaluation would genuinely teach someone something they didn't already know. You are NOT judging the idea — you are grading whether the evaluation has real intellectual content.

MANDATORY THOUGHT PROCESS — work through each criterion before scoring:

STEP 1 — Analyst Take Quality (3 pts)
Read the analyst_take field carefully. Check ALL four of:
  (a) Does it NOT open with "As an analyst", "As a market expert", or any role declaration?
  (b) Does it name a specific non-obvious insight — something NOT already stated in the market_context or competitive_landscape sections?
  (c) Does it name the single specific structural threat to THIS idea (not "competition" generically)?
  (d) Does it tell the person ONE specific thing to do or find out first — not "validate demand" or "conduct research"?
  3 = All four criteria met
  2 = Three criteria met
  1 = Two criteria met
  0 = Zero or one criteria met, or analyst_take is absent or a summary restatement

STEP 2 — Non-obvious Market or Competitive Insight (2 pts)
Ask: Is there at least one fact, number, or observation in the evaluation that a person would NOT find on the first page of a Google search for this idea?
Examples of obvious: "the market is large", "there is competition", "India has a growing middle class"
Examples of non-obvious: a specific competitor's technical weakness, a market dynamic that cuts against the obvious narrative, a structural reason why this segment is underserved
  2 = At least one clearly non-obvious insight with specifics
  1 = Insights are accurate but entirely predictable — nothing surprising
  0 = Entirely obvious — restates common knowledge

STEP 3 — Honest Positioning (2 pts)
Read the honest_uniqueness_verdict and whitespace fields. Ask: does the evaluation give a clear, unhedged verdict on whether this idea has a real differentiator — or does it diplomatically avoid the question?
  2 = States clearly whether the idea is differentiated, redundant, or niche — with a reason. Does not hedge.
  1 = Gives a verdict but qualifies it into meaninglessness ("could be unique if executed well")
  0 = Avoids taking a position — describes the idea without judging it

STEP 4 — India Context Specificity (2 pts)
Ask: Does the evaluation give specific analysis of why this idea succeeds or fails in India — beyond stating that India has a large or growing market?
Acceptable: specific regulatory constraint, infrastructure gap, pricing ceiling, language barrier, or dominant local player
Not acceptable: "India is a large market", "India has growing internet penetration", "India presents significant opportunity"
  2 = Specific India analysis tied to a structural feature of this idea
  1 = India mentioned with some detail but nothing structural
  0 = India absent or mentioned only as a large market opportunity

STEP 5 — Final Summary Actionability (1 pt)
Read the final_summary. Does it end with ONE specific thing — a named article, named person, named company, or named search term — that the person should look into next?
  1 = Ends with one specific, named next step
  0 = Ends vaguely, or just repeats search queries already in the learning section

SCORING: Add up points from each step. Do not round up.

Return ONLY valid JSON — no commentary, no markdown:
{{
  "step1_analyst_take": <0-3>,
  "step2_nonobvious_insight": <0-2>,
  "step3_honest_positioning": <0-2>,
  "step4_india_context": <0-2>,
  "step5_final_summary": <0-1>,
  "score": <sum of all steps, 0-10>,
  "verdict": "<2-3 sentences: what had real intellectual content and what was empty>",
  "what_was_missing": ["<specific gap with the exact field or section it appears in>"],
  "what_worked": ["<specific thing that genuinely taught something>"]
}}

IDEA: {raw_idea}

EVALUATION:
{evaluation}
"""


FIXER_PROMPT = """
You are an expert prompt engineer specializing in LLM business analysis prompts.

You are given a prompt that instructs an LLM to evaluate business ideas,
plus judge feedback showing exactly what the prompt failed to produce across multiple ideas.

Your job: rewrite the BUSINESS_PROMPT so the next evaluation run fixes all identified failures.

GROUND RULES — follow exactly:
1. Do NOT change the JSON schema. Output structure must remain identical.
2. Do NOT remove existing instructions — only strengthen or add more specific ones.
3. Unit economics: force the LLM to always estimate, even without direct citations.
   Add: "If no research directly supports a number, reason from first principles and
   state your assumption clearly — writing 'unverified assumption' is not acceptable."
4. Citations: require a minimum of 5 [index] citations spread across the evaluation.
5. Competitive analysis: require identifying the single most dangerous competitor and
   explaining in 1 sentence exactly why they are dangerous to this specific idea.
6. Weakest links: each must be tied to a specific structural assumption of THIS idea —
   generic risks like 'high competition' or 'market risk' are not acceptable.
7. Final summary: must end with one specific article, search, or person to look into next.
8. Maintain the same structure: role framing → rules → classification → idea/research injection → schema.
9. The fixer prompt must produce something that will be placed verbatim inside triple quotes
   in Python — no escape issues, no markdown fences.

CURRENT PROMPT:
{current_prompt}

JUDGE 1 FEEDBACK (Output Quality) — Average: {j1_avg}/10:
{j1_feedback}

JUDGE 2 FEEDBACK (Learning Value) — Average: {j2_avg}/10:
{j2_feedback}

Return ONLY the new prompt text. No JSON wrapper. No markdown. No commentary.
"""


# ── Reprocess ─────────────────────────────────────────────────────────────────

def run_reprocess():
    log("Starting reprocess — re-evaluating all ideas with new prompt + re-clustering", indent=1)
    log("(output from reprocess.py will stream below)", indent=1)
    log_sep(".")
    t = time.time()
    result = subprocess.run(
        [sys.executable, REPROCESS_PATH],
        capture_output=False,
        cwd=PROJECT_ROOT
    )
    log_sep("·")
    if result.returncode != 0:
        log(f"Reprocess FAILED after {elapsed(t)}")
        return False
    log(f"Reprocess complete  ({elapsed(t)})", indent=1)
    return True


# ── Technology judges ─────────────────────────────────────────────────────────

TECH_JUDGE1_PROMPT = """
You are a strict structural auditor for a technology idea evaluation system.

Your job: check whether this evaluation meets specific quality standards. You are NOT judging the tech idea — you are grading the evaluation's execution.

MANDATORY THOUGHT PROCESS — work through each criterion before scoring:

STEP 1 — Sentence Quality in Content List Fields (2 pts)
Check items in: current_workarounds, tech_stack_requirements, platform_dependencies.
DO NOT check search_queries or publications_to_follow — those are inherently phrase-format fields and are excluded from this criterion.
Ask: Is each item in the three content fields a complete sentence with a subject and verb? A label ("JavaScript"), a fragment ("manual data entry"), or a single noun ("APIs") is NOT a sentence.
  2 = Every item in current_workarounds, tech_stack_requirements, and platform_dependencies is a grammatically complete sentence
  1 = Most are sentences; up to 2 items across those three fields are fragments or labels
  0 = Three or more items in those three fields are fragments, labels, or bare keywords

STEP 2 — Technical Assessment Specificity (3 pts)
Check: feasibility, core_technical_challenge, build_complexity, tech_stack_requirements, platform_dependencies.
Ask: Does each field contain a specific technical claim — not vague phrases like "depends on implementation", "requires significant engineering", or "technically feasible"?
  3 = All fields make specific technical claims with concrete reasoning — no vague filler anywhere
  2 = Four fields are specific; one is vague or generic
  1 = Two or three fields are specific; rest are vague or empty
  0 = Majority are vague, generic, or could apply to any software product

STEP 3 — Moat Honesty (2 pts)
Read the moat field carefully. Valid moats: network effects, proprietary data, regulatory moat, switching costs, brand.
DISQUALIFIERS — any of these = automatic 0: "proprietary algorithms", "better UX", "first mover advantage", "innovative approach", "superior technology" (without specifics).
  2 = Names a real moat type AND explains why it applies specifically to THIS idea — OR explicitly states "no real moat exists" with a reason
  1 = Claims a moat but it is a disqualified phrase or explained vaguely ("strong data advantage" without specifics)
  0 = Moat field uses a disqualified phrase, is empty, or makes a claim that does not hold for this specific idea

STEP 4 — Weakest Assumptions Specificity (2 pts)
Check each weakest_assumptions entry: is the assumption tied to a structural constraint unique to THIS idea — or is it a generic tech risk?
Generic failures: "user adoption is hard", "scaling is difficult", "competition is fierce", "market is uncertain"
  2 = Every assumption names a specific structural dependency of THIS idea and explains why that dependency is fragile
  1 = At least one assumption is idea-specific; rest are generic
  0 = All assumptions are generic — could apply to any software startup

STEP 5 — Citations (1 pt)
Count [index] citations across the full evaluation text.
  1 = At least 5 [index] citations appear, spread across at least two different sections
  0 = Fewer than 5 citations, or all clustered in one section, or absent entirely

SCORING: Add up points from each step. Do not round up. Do not give partial credit within a criterion.

Return ONLY valid JSON — no commentary, no markdown:
{{
  "step1_sentence_quality": <0-2>,
  "step2_technical_specificity": <0-3>,
  "step3_moat_honesty": <0-2>,
  "step4_weakest_assumptions": <0-2>,
  "step5_citations": <0-1>,
  "score": <sum of all steps, 0-10>,
  "verdict": "<2-3 sentences naming the specific fields that failed and why>",
  "specific_failures": ["<exact field + exact reason it failed>"],
  "specific_wins": ["<exact field that met the standard and why>"]
}}

IDEA: {raw_idea}

EVALUATION:
{evaluation}
"""


TECH_JUDGE2_PROMPT = """
You are a learning value auditor for a technology idea evaluation system.

Your job: assess whether this evaluation would genuinely teach a builder something they didn't already know. You are NOT judging the tech idea — you are grading whether the evaluation has real intellectual content.

MANDATORY THOUGHT PROCESS — work through each criterion before scoring:

STEP 1 — Analyst Take Quality (3 pts)
Read the analyst_take field carefully. Check ALL four of:
  (a) Does it NOT open with "As a technologist", "As a product engineer", "As a senior engineer", or any role declaration?
  (b) Does it name a specific non-obvious insight — something NOT already stated in the technical_assessment or competitive_landscape sections?
  (c) Does it name the single specific structural threat to THIS idea (not "competition" generically, not "technical complexity")?
  (d) Does it tell the person ONE specific thing to build or validate first — not "validate demand", "conduct research", or "build an MVP"?
  3 = All four criteria met
  2 = Three criteria met
  1 = Two criteria met
  0 = Zero or one criteria met, or analyst_take opens with a role declaration, or it is a summary restatement

STEP 2 — Non-obvious Technical Insight (2 pts)
Ask: Is there at least one fact, number, or technical observation in the evaluation that a person would NOT find on the first page of a Google search for this idea?
Examples of obvious: "scaling is hard", "you need a large user base", "integration with existing tools is key"
Examples of non-obvious: a specific technical constraint that makes this harder than it looks, a competitor's specific architectural weakness, a latency or cost constraint that changes the build strategy
  2 = At least one clearly non-obvious technical insight with specifics
  1 = Insights are accurate but entirely predictable — nothing a builder wouldn't already assume
  0 = Entirely obvious — restates common knowledge about the technology domain

STEP 3 — India Context Specificity (2 pts)
Ask: Does the evaluation give specific analysis of why this idea succeeds or fails in India — beyond stating that India has a large or growing market?
Acceptable: specific infrastructure gap (latency, device spec), pricing ceiling that breaks unit economics, language/localization requirement, dominant local player already doing this, regulatory constraint
Not acceptable: "India is a large market", "India has growing internet penetration", "India presents a significant opportunity", "Indian developers are cost-conscious"
  2 = Specific India analysis tied to a structural feature of this exact idea
  1 = India mentioned with some detail but nothing structurally tied to this idea
  0 = India absent or mentioned only as a large/growing market

STEP 4 — Competitive Intelligence Accuracy (2 pts)
Ask: Are the named competitors real, and are their descriptions accurate? Is the "most dangerous competitor" claim credible?
Check: Do the player entries describe what the company actually does? Are India players actually India-based? Is the most dangerous competitor genuinely the one that makes this idea redundant?
  2 = Named competitors are real, descriptions are accurate, most dangerous competitor identified correctly with a specific reason
  1 = Competitors are real but descriptions are partly inaccurate or generic; most dangerous competitor not clearly identified
  0 = Named companies are mislabeled (wrong country, wrong product), descriptions are fabricated, or most dangerous competitor is missing

STEP 5 — Final Summary Actionability (1 pt)
Read the final_summary. Does it end with ONE specific thing — a named repo, named paper, named company, or named person — that the builder should study next?
  1 = Ends with one specific, named next step
  0 = Ends vaguely, just repeats search queries already listed, or suggests generic actions

SCORING: Add up points from each step. Do not round up.

Return ONLY valid JSON — no commentary, no markdown:
{{
  "step1_analyst_take": <0-3>,
  "step2_nonobvious_insight": <0-2>,
  "step3_india_context": <0-2>,
  "step4_competitive_accuracy": <0-2>,
  "step5_final_summary": <0-1>,
  "score": <sum of all steps, 0-10>,
  "verdict": "<2-3 sentences: what had real technical content and what was empty or wrong>",
  "what_was_missing": ["<specific gap with the exact field or section it appears in>"],
  "what_worked": ["<specific thing that genuinely taught something a builder didn't already know>"]
}}

IDEA: {raw_idea}

EVALUATION:
{evaluation}
"""


TECH_FIXER_PROMPT = """
You are an expert prompt engineer specializing in LLM technology idea evaluation prompts.

You are given a prompt that instructs an LLM to evaluate technology ideas,
plus judge feedback showing exactly what the prompt failed to produce across multiple ideas.

Your job: rewrite the TECHNOLOGY_PROMPT so the next evaluation run fixes all identified failures.

GROUND RULES — follow exactly:
1. Do NOT change the JSON schema. Output structure must remain identical.
2. Do NOT remove existing instructions — only strengthen or add more specific ones.
3. List fields: every item in current_workarounds, tech_stack_requirements, platform_dependencies, search_queries must be a complete sentence with subject and verb. Labels ("JavaScript"), fragments ("manual data entry"), and bare nouns are not acceptable.
4. Technical assessment: vague answers like "depends on implementation", "requires significant engineering", or "technically feasible" are not acceptable. Every field must make a specific claim.
5. Moat: "better UX", "first mover advantage", "proprietary algorithms", and "innovative approach" are NOT moats. Valid moats: network effects, proprietary data, regulatory moat, switching costs, brand. If none apply, the moat field must explicitly state that and say why.
6. Analyst take: must NOT open with "As a technologist", "As a product engineer", or any role declaration. Any opening with a role label = immediate failure. It must sound like a person with a distinct opinion, not a report with a conclusion.
7. Scores: different ideas at fundamentally different stages and in different markets MUST receive different scores. Uniform scores across all ideas (e.g., 6/6/6 on every idea) indicate the prompt is not forcing discrimination — add an explicit instruction that score distributions across ideas must vary.
8. Citations: require minimum 5 [index] citations spread across problem space, competitive landscape, and technical assessment.
9. Competitive analysis: require identifying the single most dangerous competitor and explaining in one sentence exactly why they make this idea redundant if they ship one feature. India players must actually be India-based — do not label a US company as an India player.
10. India context: require direct structural analysis (pricing ceiling, latency constraint, language barrier, dominant local player) — not generic India market commentary.
11. Final summary: must end with one specific repo, paper, company, or person to study next — not a general suggestion.
12. Maintain the same structure: role framing → rules → classification → idea/research injection → schema.
13. Output must be placed verbatim inside triple quotes in Python — no escape issues, no markdown fences.

CURRENT PROMPT:
{current_prompt}

JUDGE 1 FEEDBACK (Structural Quality) — Average: {j1_avg}/10:
{j1_feedback}

JUDGE 2 FEEDBACK (Learning Value) — Average: {j2_avg}/10:
{j2_feedback}

Return ONLY the new prompt text. No JSON wrapper. No markdown. No commentary.
"""


# ── Engineering judges ────────────────────────────────────────────────────────

ENG_JUDGE1_PROMPT = """
You are a strict structural auditor for an engineering idea evaluation system.

Your job: check whether this evaluation meets specific quality standards. You are NOT judging the engineering idea — you are grading the evaluation's execution.

MANDATORY THOUGHT PROCESS — work through each criterion before scoring:

STEP 1 — Sentence Quality in Content List Fields (2 pts)
Check items in: current_solutions, materials_and_components, regulatory_requirements.
DO NOT check search_queries or publications_to_follow — those are inherently phrase-format fields and are excluded from this criterion.
Ask: Is each item in the three content fields a complete sentence with a subject and verb? A label ("steel"), a fragment ("ISO certification"), or a single noun ("sensors") is NOT a sentence.
  2 = Every item in current_solutions, materials_and_components, and regulatory_requirements is a grammatically complete sentence
  1 = Most are sentences; up to 2 items across those three fields are fragments or labels
  0 = Three or more items in those three fields are fragments, labels, or bare keywords

STEP 2 — Engineering Assessment Specificity (3 pts)
Check: physical_feasibility, core_engineering_challenge, development_complexity, materials_and_components, regulatory_requirements.
Ask: Does each field contain a specific engineering claim — not vague phrases like "depends on materials chosen", "requires significant R&D", or "physically feasible"?
  3 = All fields make specific engineering claims with concrete reasoning — no vague filler anywhere
  2 = Four fields are specific; one is vague or generic
  1 = Two or three fields are specific; rest are vague or empty
  0 = Majority are vague, generic, or could apply to any hardware product

STEP 3 — Moat Honesty (2 pts)
Read the moat field carefully. Valid moats: proprietary manufacturing process, regulatory approval already obtained, hardware-software integration depth, switching costs from installed base, brand in a safety-critical segment.
DISQUALIFIERS — any of these = automatic 0: "innovative engineering", "better design", "first mover advantage", "superior technology", "advanced materials" (without specifics).
  2 = Names a real moat type AND explains why it applies specifically to THIS idea — OR explicitly states "no real moat exists" with a reason
  1 = Claims a moat but it is a disqualified phrase or explained vaguely
  0 = Moat field uses a disqualified phrase, is empty, or makes a claim that does not hold for this specific idea

STEP 4 — Weakest Assumptions Specificity (2 pts)
Check each weakest_assumptions entry: is the assumption tied to a specific physical or supply-chain constraint unique to THIS idea — or is it a generic engineering risk?
Generic failures: "manufacturing is hard", "supply chain is uncertain", "scaling is difficult", "regulatory approval takes time"
  2 = Every assumption names a specific physical or supply-chain dependency of THIS idea and explains why that dependency is fragile
  1 = At least one assumption is idea-specific; rest are generic
  0 = All assumptions are generic — could apply to any hardware startup

STEP 5 — Citations (1 pt)
Count [index] citations across the full evaluation text.
  1 = At least 5 [index] citations appear, spread across at least two different sections
  0 = Fewer than 5 citations, or all clustered in one section, or absent entirely

SCORING: Add up points from each step. Do not round up. Do not give partial credit within a criterion.

Return ONLY valid JSON — no commentary, no markdown:
{{
  "step1_sentence_quality": <0-2>,
  "step2_engineering_specificity": <0-3>,
  "step3_moat_honesty": <0-2>,
  "step4_weakest_assumptions": <0-2>,
  "step5_citations": <0-1>,
  "score": <sum of all steps, 0-10>,
  "verdict": "<2-3 sentences naming the specific fields that failed and why>",
  "specific_failures": ["<exact field + exact reason it failed>"],
  "specific_wins": ["<exact field that met the standard and why>"]
}}

IDEA: {raw_idea}

EVALUATION:
{evaluation}
"""


ENG_JUDGE2_PROMPT = """
You are a learning value auditor for an engineering idea evaluation system.

Your job: assess whether this evaluation would genuinely teach a builder something they didn't already know about the physical and commercial challenges of this engineering idea. You are NOT judging the idea — you are grading whether the evaluation has real intellectual content.

MANDATORY THOUGHT PROCESS — work through each criterion before scoring:

STEP 1 — Analyst Take Quality (3 pts)
Read the analyst_take field carefully. Check ALL four of:
  (a) Does it NOT open with "As a systems engineer", "As a hardware developer", "As an engineer", or any role declaration?
  (b) Does it name a specific non-obvious insight — something NOT already stated in the engineering_assessment or competitive_landscape sections?
  (c) Does it name the single specific physical or regulatory constraint that structurally kills this idea (not "manufacturing is hard" generically)?
  (d) Does it tell the person ONE specific thing to prototype or certify first — not "validate demand", "conduct market research", or "build a prototype"?
  3 = All four criteria met
  2 = Three criteria met
  1 = Two criteria met
  0 = Zero or one criteria met, or analyst_take opens with a role declaration, or it is a summary restatement

STEP 2 — Non-obvious Engineering Insight (2 pts)
Ask: Is there at least one fact, number, or engineering observation in the evaluation that a person would NOT find on the first page of a Google search for this idea?
Examples of obvious: "manufacturing at scale is hard", "you need regulatory approval", "materials cost money"
Examples of non-obvious: a specific material property that changes the design constraint, a certification pathway that adds 18 months, a supply chain concentration risk that breaks the BOM, a physics limit that caps performance
  2 = At least one clearly non-obvious engineering insight with specifics
  1 = Insights are accurate but entirely predictable — nothing a builder wouldn't already assume
  0 = Entirely obvious — restates common knowledge about the engineering domain

STEP 3 — India Manufacturing / Infrastructure Context Specificity (2 pts)
Ask: Does the evaluation give specific analysis of why this idea succeeds or fails in India's manufacturing and infrastructure environment?
Acceptable: BIS certification timeline and cost, component import duty impact on BOM, grid power reliability constraint, manufacturing ecosystem gap, skilled labor availability
Not acceptable: "India is a large market", "India has growing infrastructure", "India presents a significant opportunity", "Indian manufacturers are cost-conscious"
  2 = Specific India analysis tied to a structural manufacturing or regulatory feature of this exact idea
  1 = India mentioned with some detail but nothing structurally tied to this idea's engineering constraints
  0 = India absent or mentioned only as a large/growing market

STEP 4 — Competitive Intelligence Accuracy (2 pts)
Ask: Are the named competitors real, and are their descriptions accurate? Are India players actually India-based?
Check: Do the player entries describe what the company actually makes? Are the engineering edge and weakness claims accurate? Is the most dangerous competitor genuinely the one that makes this idea redundant?
  2 = Named competitors are real, descriptions are accurate, most dangerous competitor identified correctly with a specific reason
  1 = Competitors are real but descriptions are partly inaccurate or generic; most dangerous competitor not clearly identified
  0 = Named companies are mislabeled (wrong country, wrong product), descriptions are fabricated, or most dangerous competitor is missing

STEP 5 — Final Summary Actionability (1 pt)
Read the final_summary. Does it end with ONE specific thing — a named repo, named paper, named standards body, or named company — that the builder should study next?
  1 = Ends with one specific, named next step
  0 = Ends vaguely, just repeats search queries already listed, or suggests generic actions

SCORING: Add up points from each step. Do not round up.

Return ONLY valid JSON — no commentary, no markdown:
{{
  "step1_analyst_take": <0-3>,
  "step2_nonobvious_insight": <0-2>,
  "step3_india_context": <0-2>,
  "step4_competitive_accuracy": <0-2>,
  "step5_final_summary": <0-1>,
  "score": <sum of all steps, 0-10>,
  "verdict": "<2-3 sentences: what had real engineering content and what was empty or wrong>",
  "what_was_missing": ["<specific gap with the exact field or section it appears in>"],
  "what_worked": ["<specific thing that genuinely taught something a builder didn't already know>"]
}}

IDEA: {raw_idea}

EVALUATION:
{evaluation}
"""


ENG_FIXER_PROMPT = """
You are an expert prompt engineer specializing in LLM engineering idea evaluation prompts.

You are given a prompt that instructs an LLM to evaluate physical engineering ideas,
plus judge feedback showing exactly what the prompt failed to produce across multiple ideas.

Your job: rewrite the ENGINEERING_PROMPT so the next evaluation run fixes all identified failures.

GROUND RULES — follow exactly:
1. Do NOT change the JSON schema. Output structure must remain identical.
2. Do NOT remove existing instructions — only strengthen or add more specific ones.
3. List fields: every item in current_solutions, materials_and_components, regulatory_requirements must be a complete sentence with subject and verb. Labels ("steel"), fragments ("ISO certification"), and bare nouns are not acceptable.
4. Engineering assessment: vague answers like "depends on materials chosen", "requires significant R&D", or "physically feasible" are not acceptable. Every field must make a specific claim about the physical or regulatory constraint.
5. Moat: "better design", "first mover advantage", "innovative engineering", and "superior technology" are NOT moats. Valid moats: proprietary manufacturing process, regulatory approval already obtained, hardware-software integration depth, switching costs from installed base, brand in safety-critical segment. If none apply, the moat field must explicitly state that and say why.
6. Analyst take: must NOT open with "As a systems engineer", "As a hardware developer", "As an engineer", or any role declaration. Any opening with a role label = immediate failure. It must sound like a person with a distinct opinion, not a report with a conclusion.
7. Scores: different ideas at fundamentally different stages, in different regulatory environments, and with different manufacturing constraints MUST receive different scores. Uniform scores across all ideas indicate lazy evaluation — add an explicit instruction that score distributions must vary.
8. Citations: require minimum 5 [index] citations spread across problem space, competitive landscape, and engineering assessment.
9. Competitive analysis: require identifying the single most dangerous competitor and explaining in one sentence exactly why they make this idea redundant. India players must actually be India-based — do not label a foreign company as an India player.
10. India context: require direct structural analysis (BIS certification cost and timeline, component import duties impact on BOM, grid power reliability constraint, manufacturing ecosystem gap, skilled labor availability) — not generic India market commentary.
11. Final summary: must end with one specific repo, paper, standards body, or company to study next — not a general suggestion.
12. Maintain the same structure: role framing → rules → classification → scoring calibration → idea/research injection → schema.
13. Output must be placed verbatim inside triple quotes in Python — no escape issues, no markdown fences.

CURRENT PROMPT:
{current_prompt}

JUDGE 1 FEEDBACK (Structural Quality) — Average: {j1_avg}/10:
{j1_feedback}

JUDGE 2 FEEDBACK (Learning Value) — Average: {j2_avg}/10:
{j2_feedback}

Return ONLY the new prompt text. No JSON wrapper. No markdown. No commentary.
"""


# ── Technology prompt extraction / replacement ────────────────────────────────

def extract_technology_prompt():
    with open(EVALUATOR_PATH, "r", encoding="utf-8") as f:
        content = f.read()
    match = re.search(r'TECHNOLOGY_PROMPT = """(.+?)"""', content, re.DOTALL)
    if not match:
        raise ValueError("Could not find TECHNOLOGY_PROMPT in evaluator.py")
    return match.group(1)


def replace_technology_prompt(new_prompt):
    with open(EVALUATOR_PATH, "r", encoding="utf-8") as f:
        content = f.read()
    new_content = re.sub(
        r'(TECHNOLOGY_PROMPT = """)(.+?)(""")',
        lambda m: m.group(1) + new_prompt + m.group(3),
        content,
        flags=re.DOTALL
    )
    with open(EVALUATOR_PATH, "w", encoding="utf-8") as f:
        f.write(new_content)


# ── Engineering prompt extraction / replacement ───────────────────────────────

def extract_engineering_prompt():
    with open(EVALUATOR_PATH, "r", encoding="utf-8") as f:
        content = f.read()
    match = re.search(r'ENGINEERING_PROMPT = """(.+?)"""', content, re.DOTALL)
    if not match:
        raise ValueError("Could not find ENGINEERING_PROMPT in evaluator.py")
    return match.group(1)


def replace_engineering_prompt(new_prompt):
    with open(EVALUATOR_PATH, "r", encoding="utf-8") as f:
        content = f.read()
    new_content = re.sub(
        r'(ENGINEERING_PROMPT = """)(.+?)(""")',
        lambda m: m.group(1) + new_prompt + m.group(3),
        content,
        flags=re.DOTALL
    )
    with open(EVALUATOR_PATH, "w", encoding="utf-8") as f:
        f.write(new_content)


# ── Science judges ────────────────────────────────────────────────────────────

SCI_JUDGE1_PROMPT = """
You are a strict structural auditor for a scientific hypothesis evaluation system.

Your job: check whether this evaluation meets specific quality standards. You are NOT judging the science — you are grading the evaluation's execution.

MANDATORY THOUGHT PROCESS — work through each criterion before scoring:

STEP 1 — Sentence Quality in Content List Fields (2 pts)
Check items in: key_papers_or_groups, required_equipment, relevant_institutions.
DO NOT check search_queries or key_papers in learning — those are inherently phrase-format fields.
Ask: Is each item in the three content fields a complete sentence with a subject and verb? A label ("PCR"), a fragment ("IIT lab"), or a single noun ("cryo-EM") is NOT a sentence.
  2 = Every item in key_papers_or_groups, required_equipment, and relevant_institutions is a grammatically complete sentence
  1 = Most are sentences; up to 2 items across those three fields are fragments or labels
  0 = Three or more items in those three fields are fragments, labels, or bare keywords

STEP 2 — Hypothesis Precision and Falsifiability (3 pts)
Check: core_claim and falsifiability fields.
Ask: Is core_claim a specific testable statement — not a direction or a vague possibility? "X may influence Y" is NOT a hypothesis. Does falsifiability name one concrete experimental result that would disprove the claim?
  3 = core_claim is a specific mechanistic hypothesis AND falsifiability names a concrete disproving result
  2 = core_claim is specific but falsifiability is vague, or core_claim is directional but falsifiability is concrete
  1 = core_claim is directional ("X may affect Y") and falsifiability is vague or generic
  0 = core_claim is not falsifiable, or falsifiability field says "if results are negative" or "if hypothesis is wrong"

STEP 3 — Critical Experiment Specificity (2 pts)
Read the critical_experiment field. Ask: Is it a named specific experiment with enough detail that a graduate student could design it? Or is it a vague method category?
Failures: "run experiments", "conduct trials", "laboratory testing", "further research", naming only a technique category (e.g., "RNA sequencing") without the specific assay design or model system.
  2 = Names a specific experiment with model system or sample type, measurement method, and what outcome confirms or refutes the claim
  1 = Names a specific technique but missing the model system or the decision criterion
  0 = Vague description of research activity, or names only a technique category

STEP 4 — Failure Modes Specificity (2 pts)
Check each failure_modes entry. Is the scenario a specific experimental or logical result that would invalidate this hypothesis — or is it generic?
Generic failures: "hypothesis might be wrong", "results may not replicate", "confounding variables", "sample size issues"
  2 = Every failure mode names a specific mechanism or experimental result that would collapse this particular hypothesis, with a probability estimate
  1 = At least one failure mode is hypothesis-specific; rest are generic
  0 = All failure modes are generic — could apply to any scientific study

STEP 5 — Citations (1 pt)
Count [index] citations across the full evaluation text.
  1 = At least 5 [index] citations appear, spread across at least two different sections
  0 = Fewer than 5 citations, or all clustered in one section, or absent entirely

SCORING: Add up points from each step. Do not round up. Do not give partial credit within a criterion.

Return ONLY valid JSON — no commentary, no markdown:
{{
  "step1_sentence_quality": <0-2>,
  "step2_hypothesis_precision": <0-3>,
  "step3_critical_experiment": <0-2>,
  "step4_failure_modes": <0-2>,
  "step5_citations": <0-1>,
  "score": <sum of all steps, 0-10>,
  "verdict": "<2-3 sentences naming the specific fields that failed and why>",
  "specific_failures": ["<exact field + exact reason it failed>"],
  "specific_wins": ["<exact field that met the standard and why>"]
}}

IDEA: {raw_idea}

EVALUATION:
{evaluation}
"""


SCI_JUDGE2_PROMPT = """
You are a learning value auditor for a scientific hypothesis evaluation system.

Your job: assess whether this evaluation would genuinely teach a researcher something they didn't already know about the intellectual frontier and experimental challenges of this hypothesis. You are NOT judging the science — you are grading whether the evaluation has real intellectual content.

MANDATORY THOUGHT PROCESS — work through each criterion before scoring:

STEP 1 — Analyst Take Quality (3 pts)
Read the analyst_take field carefully. Check ALL four of:
  (a) Does it NOT open with "As a scientist", "As a researcher", "As a biologist", or any role declaration?
  (b) Does it name a specific non-obvious insight — something NOT already stated in the prior_art or methodology sections?
  (c) Does it name the single specific experimental or logical flaw that structurally undermines this hypothesis (not "it needs more research" or "it's hard to test")?
  (d) Does it tell the person ONE specific experiment to run or ONE specific paper to read — not "conduct further research", "review the literature", or "design a study"?
  3 = All four criteria met
  2 = Three criteria met
  1 = Two criteria met
  0 = Zero or one criteria met, or analyst_take opens with a role declaration, or it is a summary restatement

STEP 2 — Non-obvious Scientific Insight (2 pts)
Ask: Is there at least one fact, result, or scientific observation in the evaluation that a person would NOT find on the first page of a Google Scholar search for this topic?
Examples of obvious: "more research is needed", "the mechanism is not fully understood", "prior studies show mixed results"
Examples of non-obvious: a specific competing hypothesis that predicts the opposite outcome, a technical limitation of the primary assay that introduces systematic bias, a known confound in this model system that the field has not resolved, a result from a tangentially related field that reframes the question
  2 = At least one clearly non-obvious scientific insight with specifics
  1 = Insights are accurate but entirely predictable — nothing a researcher wouldn't already know from a standard review article
  0 = Entirely obvious — restates common knowledge about the domain

STEP 3 — India Research Context Specificity (2 pts)
Ask: Does the evaluation give specific, actionable analysis of the India research landscape for this hypothesis?
Acceptable: naming a specific Indian institution with the equipment to run this, naming the correct government funding body (DST/DBT/CSIR/ICMR/SERB) with a realistic grant size, naming a specific infrastructure gap that constrains this work in India, or naming India's specific biodiversity or population advantage for this research question
Not acceptable: "Indian institutions are doing good research", "CSIR supports science", "India has growing research capacity", "Indian researchers are interested in this area"
  2 = Specific India analysis tied to a structural feature of this exact hypothesis — institution, funding body with grant range, infrastructure gap, or biodiversity/population advantage
  1 = India mentioned with some specificity but not tied to the structural constraints of this particular research question
  0 = India absent, or mentioned only as having research capacity or interest

STEP 4 — Prior Art Accuracy (2 pts)
Ask: Are the named papers or research groups real, and are their findings accurately described?
Check: Do the key_papers_or_groups entries describe what those researchers actually found? Are the citations used to support claims that actually appear in those sources?
  2 = Named papers and groups are real, descriptions of their findings are accurate, citations support the specific claims made
  1 = Papers and groups are real but descriptions are partly inaccurate or over-simplified; citations loosely related to claims
  0 = Named papers or groups appear fabricated, findings are misrepresented, or citations contradict the claims they support

STEP 5 — Final Summary Actionability (1 pt)
Read the final_summary. Does it end with ONE specific thing — a named paper, named lab group, named preprint server category, or named database — that the researcher should consult next?
  1 = Ends with one specific, named next step
  0 = Ends vaguely, just repeats search queries already listed, or suggests generic "review the literature"

SCORING: Add up points from each step. Do not round up.

Return ONLY valid JSON — no commentary, no markdown:
{{
  "step1_analyst_take": <0-3>,
  "step2_nonobvious_insight": <0-2>,
  "step3_india_context": <0-2>,
  "step4_prior_art_accuracy": <0-2>,
  "step5_final_summary": <0-1>,
  "score": <sum of all steps, 0-10>,
  "verdict": "<2-3 sentences: what had real scientific content and what was empty or wrong>",
  "what_was_missing": ["<specific gap with the exact field or section it appears in>"],
  "what_worked": ["<specific thing that genuinely taught something a researcher didn't already know>"]
}}

IDEA: {raw_idea}

EVALUATION:
{evaluation}
"""


SCI_FIXER_PROMPT = """
You are an expert prompt engineer specializing in LLM scientific hypothesis evaluation prompts.

You are given a prompt that instructs an LLM to evaluate scientific hypotheses,
plus judge feedback showing exactly what the prompt failed to produce across multiple ideas.

Your job: rewrite the SCIENCE_PROMPT so the next evaluation run fixes all identified failures.

GROUND RULES — follow exactly:
1. Do NOT change the JSON schema. Output structure must remain identical.
2. Do NOT remove existing instructions — only strengthen or add more specific ones.
3. List fields: every item in key_papers_or_groups, required_equipment, relevant_institutions must be a complete sentence with subject and verb. Labels ("PCR"), fragments ("CSIR lab"), and bare nouns are not acceptable.
4. Hypothesis precision: core_claim must be a specific mechanistic statement, not a direction. "X may affect Y" is not acceptable — it must be "Inhibiting X in condition Z will reduce Y by mechanism M." The falsifiability field must name one concrete experimental result that would disprove the claim — "if results are negative" is not acceptable.
5. Critical experiment: must name a specific experiment with model system or sample type, measurement method, and the outcome criterion that confirms or refutes the claim — not just a technique category.
6. Failure modes: each must name a specific mechanism or experimental result that would collapse THIS particular hypothesis — generic risks like "hypothesis might be wrong", "results may not replicate", or "confounding variables" are not acceptable.
7. Analyst take: must NOT open with "As a scientist", "As a researcher", "As a biologist", or any role declaration. Any opening with a role label = immediate failure. It must name a specific non-obvious insight, a specific structural flaw, and ONE named experiment or paper — not generic advice to "conduct further research."
8. Scores: different hypotheses at different stages of validation, in different domains, with different methodological barriers MUST receive different scores. Uniform scores signal lazy evaluation.
9. Citations: require minimum 5 [index] citations spread across prior_art, methodology, and failure_modes.
10. India research context: require specific institution names, specific funding body with grant size range, specific infrastructure gap or biodiversity advantage tied to THIS hypothesis — not generic statements about Indian research capacity.
11. Final summary: must end with one specific paper, lab group, preprint server category, or database — not a general suggestion.
12. Maintain the same structure: role framing → rules → classification → scoring calibration → idea/research injection → schema.
13. Output must be placed verbatim inside triple quotes in Python — no escape issues, no markdown fences.

CURRENT PROMPT:
{current_prompt}

JUDGE 1 FEEDBACK (Structural Quality) — Average: {j1_avg}/10:
{j1_feedback}

JUDGE 2 FEEDBACK (Learning Value) — Average: {j2_avg}/10:
{j2_feedback}

Return ONLY the new prompt text. No JSON wrapper. No markdown. No commentary.
"""


# ── Mathematics judges ────────────────────────────────────────────────────────

MATH_JUDGE1_PROMPT = """
You are a strict structural auditor for a mathematical conjecture evaluation system.

Your job: check whether this evaluation meets specific quality standards. You are NOT judging the mathematics — you are grading the evaluation's execution.

MANDATORY THOUGHT PROCESS — work through each criterion before scoring:

STEP 1 — Sentence Quality in Content List Fields (2 pts)
Check items in: closest_results, key_tools_and_techniques, relevant_institutions.
DO NOT check search_queries or key_references — those are phrase-format fields.
Ask: Is each item a complete sentence with a subject and verb? A bare citation ("Hardy-Ramanujan 1917"), a label ("sieve theory"), or a fragment ("algebraic geometry methods") is NOT a sentence.
  2 = Every item in closest_results, key_tools_and_techniques, and relevant_institutions is a grammatically complete sentence
  1 = Most are sentences; up to 2 items across those three fields are fragments or labels
  0 = Three or more items in those three fields are fragments, labels, or bare citations

STEP 2 — Conjecture Precision and Verifiability (3 pts)
Check: formal_statement and verification_method fields.
Ask: Is formal_statement a precise mathematical claim with explicit quantifiers, defined variables, and stated domain? Does verification_method name a specific algorithm or computational approach, the range it would check, and what a positive result would confirm?
  3 = formal_statement is fully precise AND verification_method names a specific algorithm, range, and interpretation
  2 = formal_statement is precise but verification_method is vague, OR formal_statement is slightly informal but verification_method is specific
  1 = formal_statement uses informal language ("for large n", "almost all", "seems to") AND verification_method is vague
  0 = formal_statement is not a mathematical claim, or verification_method is absent or says "check computationally"

STEP 3 — Critical Obstacle Specificity (2 pts)
Read the critical_obstacle field. Ask: Does it name the specific mathematical step where the proposed proof strategy fails — or does it give a generic difficulty?
Failures: "the proof is hard", "current tools are insufficient", "this is an open problem", "further research is needed"
  2 = Names the specific step or barrier — the precise point where the argument breaks or no current technique applies — with enough detail that a mathematician would recognize the difficulty
  1 = Identifies a general area of difficulty but does not pinpoint the specific obstacle
  0 = Generic statement of difficulty with no mathematical specificity

STEP 4 — Counterexample Risks Specificity (2 pts)
Check each counterexample_risks entry. Does it describe a specific mathematical construction or family that could refute the conjecture — or is it generic?
Generic failures: "the conjecture might be false", "there may be exceptions", "edge cases exist", "the claim could fail for large numbers"
  2 = Every counterexample risk names a specific mathematical structure, construction, or family that is dangerous to this conjecture, and explains why
  1 = At least one counterexample risk is mathematically specific; rest are generic
  0 = All counterexample risks are generic — could apply to any conjecture

STEP 5 — Citations (1 pt)
Count [index] citations across the full evaluation text.
  1 = At least 5 [index] citations appear, spread across at least two different sections
  0 = Fewer than 5 citations, or all clustered in one section, or absent entirely

SCORING: Add up points from each step. Do not round up. Do not give partial credit within a criterion.

Return ONLY valid JSON — no commentary, no markdown:
{{
  "step1_sentence_quality": <0-2>,
  "step2_conjecture_precision": <0-3>,
  "step3_critical_obstacle": <0-2>,
  "step4_counterexample_risks": <0-2>,
  "step5_citations": <0-1>,
  "score": <sum of all steps, 0-10>,
  "verdict": "<2-3 sentences naming the specific fields that failed and why>",
  "specific_failures": ["<exact field + exact reason it failed>"],
  "specific_wins": ["<exact field that met the standard and why>"]
}}

IDEA: {raw_idea}

EVALUATION:
{evaluation}
"""


MATH_JUDGE2_PROMPT = """
You are a learning value auditor for a mathematical conjecture evaluation system.

Your job: assess whether this evaluation would genuinely teach a mathematician something non-obvious about the conjecture's place in the literature, its proof barriers, and its connections to other problems. You are NOT judging the mathematics — you are grading whether the evaluation has real intellectual content.

MANDATORY THOUGHT PROCESS — work through each criterion before scoring:

STEP 1 — Analyst Take Quality (3 pts)
Read the analyst_take field carefully. Check ALL four of:
  (a) Does it NOT open with "As a mathematician", "As a number theorist", "As a researcher", or any role declaration?
  (b) Does it name a specific non-obvious mathematical insight — something NOT already stated in the prior_art or proof_strategy sections?
  (c) Does it name the single specific obstacle that makes this conjecture genuinely hard with current tools (not "it's an open problem" or "it's difficult")?
  (d) Does it tell the person ONE specific thing to compute, read, or prove first — not "study the literature", "explore further", or "attempt a proof"?
  3 = All four criteria met
  2 = Three criteria met
  1 = Two criteria met
  0 = Zero or one criteria met, or opens with a role declaration, or is a summary restatement

STEP 2 — Non-obvious Mathematical Insight (2 pts)
Ask: Is there at least one observation in the evaluation that a person would NOT find in the introduction of a standard survey paper on this topic?
Examples of obvious: "this is related to the Riemann Hypothesis", "sieve methods have been applied to similar problems", "computational verification has been done for small cases"
Examples of non-obvious: a specific connection to a distant area of mathematics that reframes the problem, a known result in a different domain that immediately rules out a natural proof strategy, a precise quantitative barrier (e.g., a GRH-conditional lower bound that the conjecture must beat), a known counterexample to a closely related but stronger claim
  2 = At least one clearly non-obvious mathematical insight with specifics
  1 = Insights are accurate but predictable from any survey article on the topic
  0 = Entirely obvious — restates common knowledge about the mathematical domain

STEP 3 — India Mathematics Context Specificity (2 pts)
Ask: Does the evaluation give specific, actionable information about the India research landscape for this area of mathematics?
Acceptable: naming a specific Indian institution with active researchers in this exact domain, naming NBHM or SERB with a realistic grant range, identifying a specific Indian mathematician or group working on related problems, naming India's historical contribution to this mathematical area (e.g., Ramanujan's work on partitions for number theory conjectures)
Not acceptable: "Indian institutions are doing good mathematics", "TIFR is a strong research center", "India has talented mathematicians", "Indian researchers are active in this field"
  2 = Specific India context tied to a structural feature of this exact mathematical domain — named institution, named researcher or group, NBHM/SERB funding path, or India's documented contribution
  1 = India mentioned with some specificity but not tied to the particular domain of this conjecture
  0 = India absent or mentioned only generically

STEP 4 — Prior Art Accuracy (2 pts)
Ask: Are the named theorems, papers, and results real and correctly described?
Check: Do the closest_results entries describe what was actually proved? Are the named mathematicians correctly attributed? Do citations support the specific claims made?
  2 = Named theorems and results are real, attributions are correct, descriptions accurately represent what was proved
  1 = Named results are real but descriptions are simplified or slightly inaccurate; minor attribution errors
  0 = Named theorems appear fabricated, results are misattributed, or descriptions contradict what was actually proved

STEP 5 — Final Summary Actionability (1 pt)
Read the final_summary. Does it end with ONE specific thing — a named paper, textbook chapter, OEIS sequence, or open problem list — that the person should consult next?
  1 = Ends with one specific, named next step
  0 = Ends vaguely, repeats search queries, or suggests "explore the literature"

SCORING: Add up points from each step. Do not round up.

Return ONLY valid JSON — no commentary, no markdown:
{{
  "step1_analyst_take": <0-3>,
  "step2_nonobvious_insight": <0-2>,
  "step3_india_context": <0-2>,
  "step4_prior_art_accuracy": <0-2>,
  "step5_final_summary": <0-1>,
  "score": <sum of all steps, 0-10>,
  "verdict": "<2-3 sentences: what had real mathematical content and what was empty or wrong>",
  "what_was_missing": ["<specific gap with the exact field or section it appears in>"],
  "what_worked": ["<specific thing that genuinely taught something non-obvious>"]
}}

IDEA: {raw_idea}

EVALUATION:
{evaluation}
"""


MATH_FIXER_PROMPT = """
You are an expert prompt engineer specializing in LLM mathematical conjecture evaluation prompts.

You are given a prompt that instructs an LLM to evaluate mathematical conjectures and patterns,
plus judge feedback showing exactly what the prompt failed to produce across multiple ideas.

Your job: rewrite the MATHEMATICS_PROMPT so the next evaluation run fixes all identified failures.

GROUND RULES — follow exactly:
1. Do NOT change the JSON schema. Output structure must remain identical.
2. Do NOT remove existing instructions — only strengthen or add more specific ones.
3. List fields: every item in closest_results, key_tools_and_techniques, relevant_institutions must be a complete sentence with subject and verb. Bare citations, labels, and technique names without explanation are not acceptable.
4. Conjecture precision: formal_statement must have explicit quantifiers, defined variables, and stated domain. verification_method must name a specific algorithm or computational approach, the range to check, and what a positive result confirms (and does not confirm).
5. Critical obstacle: must name the specific mathematical step where the proof strategy fails — "the proof is hard" or "current tools are insufficient" are not acceptable.
6. Counterexample risks: each must name a specific mathematical construction or family that is dangerous to this conjecture — "the conjecture might be false" is not acceptable.
7. Analyst take: must NOT open with "As a mathematician", "As a number theorist", or any role declaration. Must name a specific non-obvious insight, the single specific proof barrier, and ONE concrete next step (computation, paper, or sub-problem) — not generic advice.
8. Scores: different conjectures at different stages of development, in different domains, with different proof barriers MUST receive different scores. Uniform scores signal lazy evaluation.
9. Citations: require minimum 5 [index] citations spread across prior_art, proof_strategy, and counterexample_risks.
10. India math context: require naming a specific institution with researchers in this exact domain, the NBHM or SERB funding path with realistic grant size, and India's documented contribution to this area — not generic statements.
11. Final summary: must end with one specific paper, textbook chapter, OEIS sequence, or open problem list — not a general suggestion.
12. Maintain the same structure: role framing → rules → classification → scoring calibration → idea/research injection → schema.
13. Output must be placed verbatim inside triple quotes in Python — no escape issues, no markdown fences.

CURRENT PROMPT:
{current_prompt}

JUDGE 1 FEEDBACK (Structural Quality) — Average: {j1_avg}/10:
{j1_feedback}

JUDGE 2 FEEDBACK (Learning Value) — Average: {j2_avg}/10:
{j2_feedback}

Return ONLY the new prompt text. No JSON wrapper. No markdown. No commentary.
"""


# ── Mathematics prompt extraction / replacement ───────────────────────────────

def extract_mathematics_prompt():
    with open(EVALUATOR_PATH, "r", encoding="utf-8") as f:
        content = f.read()
    match = re.search(r'MATHEMATICS_PROMPT = """(.+?)"""', content, re.DOTALL)
    if not match:
        raise ValueError("Could not find MATHEMATICS_PROMPT in evaluator.py")
    return match.group(1)


def replace_mathematics_prompt(new_prompt):
    with open(EVALUATOR_PATH, "r", encoding="utf-8") as f:
        content = f.read()
    new_content = re.sub(
        r'(MATHEMATICS_PROMPT = """)(.+?)(""")',
        lambda m: m.group(1) + new_prompt + m.group(3),
        content,
        flags=re.DOTALL
    )
    with open(EVALUATOR_PATH, "w", encoding="utf-8") as f:
        f.write(new_content)


# ── Science prompt extraction / replacement ───────────────────────────────────

def extract_science_prompt():
    with open(EVALUATOR_PATH, "r", encoding="utf-8") as f:
        content = f.read()
    match = re.search(r'SCIENCE_PROMPT = """(.+?)"""', content, re.DOTALL)
    if not match:
        raise ValueError("Could not find SCIENCE_PROMPT in evaluator.py")
    return match.group(1)


def replace_science_prompt(new_prompt):
    with open(EVALUATOR_PATH, "r", encoding="utf-8") as f:
        content = f.read()
    new_content = re.sub(
        r'(SCIENCE_PROMPT = """)(.+?)(""")',
        lambda m: m.group(1) + new_prompt + m.group(3),
        content,
        flags=re.DOTALL
    )
    with open(EVALUATOR_PATH, "w", encoding="utf-8") as f:
        f.write(new_content)


# ── Step-level threshold checker ─────────────────────────────────────────────

def check_step_thresholds(idea_records, cfg):
    """
    For each step in each judge, compute the average score across all ideas.
    Return a list of failure strings for any step below its threshold * max.
    Steps listed in cfg["low_floor_steps"] use STEP_THRESHOLD_LOW (50%); all others use STEP_THRESHOLD (75%).
    Empty list means all steps passed.
    """
    failures      = []
    low_floor_set = set(cfg.get("low_floor_steps", []))

    for judge_key, steps in [("judge1", cfg.get("judge1_steps", {})),
                              ("judge2", cfg.get("judge2_steps", {}))]:
        for step_name, max_pts in steps.items():
            floor    = STEP_THRESHOLD_LOW if step_name in low_floor_set else STEP_THRESHOLD
            pct_label = "50%" if step_name in low_floor_set else "75%"
            scores   = [r[judge_key].get(step_name, 0) for r in idea_records]
            avg      = sum(scores) / len(scores)
            required = max_pts * floor
            if avg < required:
                failures.append(
                    f"{judge_key}/{step_name}: avg {avg:.2f}/{max_pts} "
                    f"(need >= {required:.2f} for {pct_label} gate)"
                )

    return failures


# ── Other judges / fixer ─────────────────────────────────────────────────────

OTHER_JUDGE1_PROMPT = """You are a strict structural auditor for a generalist idea evaluation system.

Your job: check whether this evaluation meets specific quality standards. You are NOT judging the idea — you are grading the evaluation's execution.

MANDATORY THOUGHT PROCESS — work through each criterion before scoring:

STEP 1 — Sentence Quality in List Fields (2 pts)
Check every item in: closest_examples, failure_modes, relevant_actors.
Ask: Is each item a complete sentence with a subject and verb? A bare label ("community governance"), a name without context, or a fragment ("lack of funding") is NOT a sentence.
  2 = Every list item across the entire evaluation is a grammatically complete sentence
  1 = Most are sentences; up to 2 items are fragments or labels
  0 = Three or more list items are fragments, labels, or incomplete phrases

STEP 2 — Precision and Dependency Clarity (3 pts)
Check: what_is_being_proposed, key_assumption, and critical_dependency.
Ask: Does what_is_being_proposed state exactly what someone would build or do (not a goal or direction)? Does key_assumption name the single assumption whose failure collapses the idea? Does critical_dependency name the specific resource, permission, or condition the idea cannot proceed without?
  3 = All three are specific and concrete — what/who/where/when is clear for each
  2 = Two are specific; one is vague or generic
  1 = Only one is specific; the other two are vague or absent
  0 = what_is_being_proposed is a goal or direction, and no dependency or assumption is named

STEP 3 — Failure Modes Specificity (2 pts)
Check each failure_modes entry. Does it describe a specific scenario with a named trigger, mechanism, and outcome — or is it a generic risk?
Generic failures: "lack of funding", "stakeholder resistance", "execution challenges", "market conditions may change"
  2 = Every failure mode names a specific trigger, mechanism, and outcome tied to this particular idea
  1 = At least one failure mode is specific; rest are generic risk labels
  0 = All failure modes are generic — could apply to any project

STEP 4 — Minimum Viable Test Concreteness (2 pts)
Read minimum_viable_test. Ask: Does it name a specific location or population, a specific action, and a measurable outcome — achievable within 3 months?
Failures: "run a pilot", "test with a small group", "conduct a proof of concept", naming only a method without specifics
  2 = Specific location or population + specific action + named measurable outcome + achievable within 3 months
  1 = Two of the four elements are present; one or two are vague
  0 = minimum_viable_test is absent or describes only "run a pilot" without specifics

STEP 5 — Citations (1 pt)
Count [index] citations across the full evaluation text.
  1 = At least 4 [index] citations appear, spread across prior_context and feasibility
  0 = Fewer than 4 citations, or all clustered in one section, or absent entirely

SCORING: Add up points from each step. Do not round up. Do not give partial credit within a criterion.

Return ONLY valid JSON — no commentary, no markdown:
{{
  "step1_sentence_quality": <0-2>,
  "step2_precision_and_dependency": <0-3>,
  "step3_failure_modes": <0-2>,
  "step4_minimum_viable_test": <0-2>,
  "step5_citations": <0-1>,
  "score": <sum of all steps, 0-10>,
  "verdict": "<2-3 sentences naming the specific fields that failed and why>",
  "specific_failures": ["<exact field + exact reason it failed>"],
  "specific_wins": ["<exact field that met the standard and why>"]
}}

IDEA: {raw_idea}

EVALUATION:
{evaluation}
"""


OTHER_JUDGE2_PROMPT = """You are a learning value auditor for a generalist idea evaluation system.

Your job: assess whether this evaluation would genuinely help someone understand what the idea actually is, what already exists closest to it, and what would make it succeed or fail. You are NOT judging the idea — you are grading whether the evaluation has real analytical content.

MANDATORY THOUGHT PROCESS — work through each criterion before scoring:

STEP 1 — Analyst Take Quality (3 pts)
Read the analyst_take field carefully. Check ALL four of:
  (a) Does it NOT open with "As an analyst", "As a generalist", "As a researcher", or any role declaration?
  (b) Does it name a non-obvious insight that reframes what the idea actually is or reveals a hidden dependency — NOT already stated in core_analysis or feasibility?
  (c) Does it name the specific failure mode that would end this idea fastest — not "execution is hard" but the specific trigger and breakdown?
  (d) Does it tell the person ONE concrete next step — a person to contact, a dataset to find, or a specific test to run — not "do more research" or "validate the concept"?
  3 = All four criteria met
  2 = Three criteria met
  1 = Two criteria met
  0 = Zero or one criteria met, or opens with a role declaration, or is a summary restatement

STEP 2 — Non-Obvious Insight (2 pts)
Ask: Does the evaluation surface an insight that reframes what the idea actually is — reveals it belongs to a different domain, identifies a hidden structural dependency, or shows why previous attempts at something similar failed?
  2 = The insight is genuinely surprising and changes how you understand the idea
  1 = The insight is interesting but derivable from reading the idea framing alone
  0 = No genuine insight — the evaluation only validates or summarises the idea

STEP 3 — India Relevance Specificity (2 pts)
Read india_relevance. Ask: Does it name a specific opportunity or constraint that India creates for THIS idea — not generic "India is a large market" — and at least one named actor?
  2 = Specific India opportunity or constraint tied to this idea + at least one named relevant actor (organisation, body, community)
  1 = India mentioned with some specificity but not tied to the structural features of this particular idea
  0 = Absent, or only "India has a large population" or "there is potential in India"

STEP 4 — Prior Context Accuracy (2 pts)
Check closest_examples. Ask: Are the named examples real and verifiable? Do entries describe what they did, what they achieved or failed at, and how they relate to this idea?
  2 = Named examples are real, outcomes are accurately described, relevance to this idea is explained
  1 = Examples are named but described too briefly to verify, or relevance is asserted without explanation
  0 = Examples appear invented, outcomes are misrepresented, or entries are generic ("similar projects exist")

STEP 5 — Final Summary Actionability (1 pt)
Read final_summary. Does it end with ONE specific resource — a named organisation, named dataset, named researcher, or named comparable project?
  1 = Ends with one specific, named next step
  0 = Ends vaguely or with generic advice to "explore further"

SCORING: Add up points from each step. Do not round up.

Return ONLY valid JSON — no commentary, no markdown:
{{
  "step1_analyst_take": <0-3>,
  "step2_nonobvious_insight": <0-2>,
  "step3_india_relevance": <0-2>,
  "step4_prior_context_accuracy": <0-2>,
  "step5_final_summary": <0-1>,
  "score": <sum of all steps, 0-10>,
  "verdict": "<2-3 sentences: what had real analytical content and what was generic or vague>",
  "what_was_missing": ["<specific gap with the exact field or section it appears in>"],
  "what_worked": ["<specific thing that genuinely taught something non-obvious>"]
}}

IDEA: {raw_idea}

EVALUATION:
{evaluation}
"""


OTHER_FIXER_PROMPT = """You are an expert prompt engineer specializing in LLM generalist idea evaluation prompts.

You are given a prompt that instructs an LLM to evaluate ideas that don't fit standard categories,
plus judge feedback showing exactly what the prompt failed to produce across multiple ideas.

Your job: rewrite the OTHER_PROMPT so the next evaluation run fixes all identified failures.

GROUND RULES — follow exactly:
1. Do NOT change the JSON schema. Output structure must remain identical.
2. Do NOT remove existing instructions — only strengthen or add more specific ones.
3. List fields: every item in closest_examples, failure_modes, relevant_actors must be a complete sentence with subject and verb. Labels and fragments are not acceptable.
4. Precision: what_is_being_proposed must describe what someone actually builds or does — not a goal. key_assumption must name the single assumption whose failure collapses the idea. critical_dependency must name the specific resource or permission needed.
5. Failure modes: each must describe a specific trigger, mechanism, and outcome — not generic risks.
6. Minimum viable test: must name specific location or population, specific action, measurable outcome, and be achievable in 3 months.
7. Analyst take: must NOT open with "As an analyst" or any role declaration. Must surface a non-obvious insight, name the fastest failure mode, and give ONE concrete next step.
8. Scores: different ideas at different feasibility and novelty levels MUST receive different scores. Uniform scores signal lazy evaluation.
9. Citations: require minimum 4 [index] citations spread across prior_context and feasibility.
10. India relevance: require a specific opportunity or constraint tied to this particular idea, plus at least one named actor.
11. Final summary: must end with one specific named resource — not a general suggestion.
12. Maintain the same structure: role framing → rules → classification → scoring calibration → idea/research injection → schema.
13. Output must be placed verbatim inside triple quotes in Python — no escape issues, no markdown fences.

CURRENT PROMPT:
{current_prompt}

JUDGE 1 FEEDBACK (Structural Quality) — Average: {j1_avg}/10:
{j1_feedback}

JUDGE 2 FEEDBACK (Learning Value) — Average: {j2_avg}/10:
{j2_feedback}

Return ONLY the new prompt text. No JSON wrapper. No markdown. No commentary.
"""


# ── Other prompt extraction / replacement ─────────────────────────────────────

def extract_other_prompt():
    with open(EVALUATOR_PATH, "r", encoding="utf-8") as f:
        content = f.read()
    match = re.search(r'OTHER_PROMPT = """(.+?)"""', content, re.DOTALL)
    if not match:
        raise ValueError("Could not find OTHER_PROMPT in evaluator.py")
    return match.group(1)


def replace_other_prompt(new_prompt):
    with open(EVALUATOR_PATH, "r", encoding="utf-8") as f:
        content = f.read()
    new_content = re.sub(
        r'(OTHER_PROMPT = """)(.+?)(""")',
        lambda m: m.group(1) + new_prompt + m.group(3),
        content,
        flags=re.DOTALL
    )
    with open(EVALUATOR_PATH, "w", encoding="utf-8") as f:
        f.write(new_content)


# ── Personal judges / fixer ──────────────────────────────────────────────────

PERS_JUDGE1_PROMPT = """You are a strict structural auditor for a personal development idea evaluation system.

Your job: check whether this evaluation meets specific quality standards. You are NOT judging the idea — you are grading the evaluation's execution.

MANDATORY THOUGHT PROCESS — work through each criterion before scoring:

STEP 1 — Sentence Quality in List Fields (2 pts)
Check every item in: closest_research, failure_modes, leading_indicators.
Ask: Is each item a complete sentence with a subject and verb? A bare concept ("accountability"), a label ("habit stacking"), or a fragment ("morning routine consistency") is NOT a sentence.
  2 = Every list item across the entire evaluation is a grammatically complete sentence
  1 = Most are sentences; up to 2 items are fragments or labels
  0 = Three or more list items are fragments, labels, or incomplete phrases

STEP 2 — Implementation Specificity (3 pts)
Check: behaviour_or_system, minimum_viable_version, leading_indicators, and timeline_to_signal.
Ask: Does behaviour_or_system describe exactly what the person does (specific action, specific time/context)? Does minimum_viable_version name the smallest testable version? Do leading_indicators name measurable signals within the first 2 weeks?
  3 = behaviour_or_system is specific + minimum_viable_version is defined + leading_indicators are measurable within 2 weeks
  2 = Two of the three are fully met; one is vague
  1 = Only one is fully met; the other two are vague or absent
  0 = behaviour_or_system is vague ("meditate more", "exercise regularly") and no implementation detail exists

STEP 3 — Failure Modes Specificity (2 pts)
Check each failure_modes entry. Does it describe a specific scenario in which this approach fails for this person and goal — or is it generic?
Generic failures: "motivation may decrease", "willpower is hard", "consistency is challenging", "life gets in the way"
  2 = Every failure mode describes a specific scenario tied to the behaviour and context of THIS idea — named trigger, named pattern, named breakdown point
  1 = At least one failure mode is specific; rest are generic
  0 = All failure modes are generic — could apply to any self-improvement effort

STEP 4 — Mechanism Clarity (2 pts)
Read proposed_mechanism. Ask: Does it name the specific psychological or physiological mechanism — not "it works because it builds discipline" or "it creates positive habits"?
Failures: "habit formation", "builds discipline", "creates positive mindset", "increases motivation"
  2 = Names a specific mechanism (implementation intention, variable reward schedule, autonomic nervous system response, working memory offloading, etc.) and explains how it applies to this specific behaviour
  1 = A mechanism is named but described vaguely or without connection to this specific behaviour
  0 = No mechanism named, or mechanism is circular ("it works because you do it consistently")

STEP 5 — Citations (1 pt)
Count [index] citations across the full evaluation text.
  1 = At least 4 [index] citations appear, spread across evidence_base and implementation
  0 = Fewer than 4 citations, or all clustered in one section, or absent entirely

SCORING: Add up points from each step. Do not round up. Do not give partial credit within a criterion.

Return ONLY valid JSON — no commentary, no markdown:
{{
  "step1_sentence_quality": <0-2>,
  "step2_implementation_specificity": <0-3>,
  "step3_failure_modes": <0-2>,
  "step4_mechanism_clarity": <0-2>,
  "step5_citations": <0-1>,
  "score": <sum of all steps, 0-10>,
  "verdict": "<2-3 sentences naming the specific fields that failed and why>",
  "specific_failures": ["<exact field + exact reason it failed>"],
  "specific_wins": ["<exact field that met the standard and why>"]
}}

IDEA: {raw_idea}

EVALUATION:
{evaluation}
"""


PERS_JUDGE2_PROMPT = """You are a learning value auditor for a personal development idea evaluation system.

Your job: assess whether this evaluation would genuinely help a person understand whether and how to implement this idea. You are NOT judging the idea — you are grading whether the evaluation has real practical content.

MANDATORY THOUGHT PROCESS — work through each criterion before scoring:

STEP 1 — Analyst Take Quality (3 pts)
Read the analyst_take field carefully. Check ALL four of:
  (a) Does it NOT open with "As a behavioural scientist", "As a coach", "As a researcher", or any role declaration?
  (b) Does it name a non-obvious insight about why this works or doesn't — something that cuts against the conventional self-help framing, NOT already stated in evidence_base or implementation?
  (c) Does it name the single most likely failure mode for a real person — not "motivation may decrease" but the specific breakdown scenario?
  (d) Does it tell the person ONE specific thing to do in the first 48 hours to test whether this will work for them — not "try it and see" or "start small"?
  3 = All four criteria met
  2 = Three criteria met
  1 = Two criteria met
  0 = Zero or one criteria met, or opens with a role declaration, or is a motivational restatement

STEP 2 — Non-Obvious Insight (2 pts)
Ask: Does the evaluation surface an insight that cuts against the standard self-help framing — reveals a hidden failure mechanism, explains why the conventional version of this advice fails, or identifies a population for whom this works differently?
  2 = The insight is genuinely surprising and changes how you think about the approach
  1 = The insight is interesting but derivable from reading the idea framing alone
  0 = No genuine insight — the evaluation validates the idea or reports the obvious

STEP 3 — India Context Specificity (2 pts)
Read india_context. Ask: Does it name at least one structural constraint specific to the Indian context for this behaviour — not "India has many distractions" but a named structural feature (joint family expectations, irregular power supply, cost, heat, social norms)?
  2 = Names a specific structural constraint AND either a specific advantage or a concrete adaptation for the Indian context
  1 = India mentioned but constraint is generic or not tied to this specific behaviour
  0 = Absent, or only "cultural differences exist in India"

STEP 4 — Evidence Base Accuracy (2 pts)
Check closest_research. Ask: Are the named studies or researchers real? Do entries describe what was found and how it relates to this claim?
  2 = Named studies and researchers are real, findings are accurately described, relevance to this claim is explained
  1 = Studies are named but described too briefly to verify, or relevance is asserted without explanation
  0 = Studies appear invented, findings are misrepresented, or entries are generic ("research shows...")

STEP 5 — Final Summary Actionability (1 pt)
Read final_summary. Does it end with ONE specific book, paper, researcher, or protocol to study next?
  1 = Ends with one specific, named next step
  0 = Ends vaguely or with generic advice to "read more" or "do further research"

SCORING: Add up points from each step. Do not round up.

Return ONLY valid JSON — no commentary, no markdown:
{{
  "step1_analyst_take": <0-3>,
  "step2_nonobvious_insight": <0-2>,
  "step3_india_context": <0-2>,
  "step4_evidence_accuracy": <0-2>,
  "step5_final_summary": <0-1>,
  "score": <sum of all steps, 0-10>,
  "verdict": "<2-3 sentences: what had real practical content and what was generic or motivational>",
  "what_was_missing": ["<specific gap with the exact field or section it appears in>"],
  "what_worked": ["<specific thing that genuinely taught something non-obvious>"]
}}

IDEA: {raw_idea}

EVALUATION:
{evaluation}
"""


PERS_FIXER_PROMPT = """You are an expert prompt engineer specializing in LLM personal development idea evaluation prompts.

You are given a prompt that instructs an LLM to evaluate personal development ideas,
plus judge feedback showing exactly what the prompt failed to produce across multiple ideas.

Your job: rewrite the PERSONAL_PROMPT so the next evaluation run fixes all identified failures.

GROUND RULES — follow exactly:
1. Do NOT change the JSON schema. Output structure must remain identical.
2. Do NOT remove existing instructions — only strengthen or add more specific ones.
3. List fields: every item in closest_research, failure_modes, leading_indicators must be a complete sentence with subject and verb. Labels and fragments are not acceptable.
4. Implementation specificity: behaviour_or_system must describe exact action, time, and context. minimum_viable_version must be testable in week one. leading_indicators must be measurable within 2 weeks — not "you will feel better."
5. Failure modes: each must name a specific scenario tied to this behaviour and context — generic motivational failures ("willpower is hard") are not acceptable.
6. Mechanism: proposed_mechanism must name a specific psychological or physiological process — not circular ("it works because you do it") or generic ("habit formation").
7. Analyst take: must NOT open with "As a behavioural scientist", "As a coach", or any role declaration. Must cut against the conventional self-help framing, name the specific failure mode, and give one action for the first 48 hours.
8. Scores: different interventions at different evidence levels MUST receive different scores. Uniform scores signal lazy evaluation.
9. Citations: require minimum 4 [index] citations spread across evidence_base and implementation.
10. India context: require at least one named structural constraint specific to India for this behaviour — not generic cultural differences.
11. Final summary: must end with one specific book, paper, researcher, or protocol — not a general suggestion.
12. Maintain the same structure: role framing → rules → classification → scoring calibration → idea/research injection → schema.
13. Output must be placed verbatim inside triple quotes in Python — no escape issues, no markdown fences.

CURRENT PROMPT:
{current_prompt}

JUDGE 1 FEEDBACK (Structural Quality) — Average: {j1_avg}/10:
{j1_feedback}

JUDGE 2 FEEDBACK (Learning Value) — Average: {j2_avg}/10:
{j2_feedback}

Return ONLY the new prompt text. No JSON wrapper. No markdown. No commentary.
"""


# ── Personal prompt extraction / replacement ──────────────────────────────────

def extract_personal_prompt():
    with open(EVALUATOR_PATH, "r", encoding="utf-8") as f:
        content = f.read()
    match = re.search(r'PERSONAL_PROMPT = """(.+?)"""', content, re.DOTALL)
    if not match:
        raise ValueError("Could not find PERSONAL_PROMPT in evaluator.py")
    return match.group(1)


def replace_personal_prompt(new_prompt):
    with open(EVALUATOR_PATH, "r", encoding="utf-8") as f:
        content = f.read()
    new_content = re.sub(
        r'(PERSONAL_PROMPT = """)(.+?)(""")',
        lambda m: m.group(1) + new_prompt + m.group(3),
        content,
        flags=re.DOTALL
    )
    with open(EVALUATOR_PATH, "w", encoding="utf-8") as f:
        f.write(new_content)


# ── Philosophy judges / fixer ────────────────────────────────────────────────

PHIL_JUDGE1_PROMPT = """You are a strict structural auditor for a philosophical argument evaluation system.

Your job: check whether this evaluation meets specific quality standards. You are NOT judging the philosophy — you are grading the evaluation's execution.

MANDATORY THOUGHT PROCESS — work through each criterion before scoring:

STEP 1 — Sentence Quality in List Fields (2 pts)
Check every item in: closest_arguments, key_premises, possible_responses, relevant_institutions.
Ask: Is each item a complete sentence with a subject and verb? A bare citation ("Nagel 1974"), a label ("functionalism"), or a fragment ("philosophical zombies") is NOT a sentence.
  2 = Every list item across the entire evaluation is a grammatically complete sentence
  1 = Most are sentences; up to 2 items are fragments or labels
  0 = Three or more list items are fragments, labels, or bare citations

STEP 2 — Argument Precision (3 pts)
Check: core_thesis, logical_structure, and key_premises fields.
Ask: Is core_thesis a precise philosophical claim (not a question, not a worry, not a direction)? Does logical_structure name the argument form and explain how premises lead to conclusion? Are key_premises stated as complete declarative claims the argument requires to be true?
  3 = core_thesis is a precise claim + logical_structure names the form and structure + all key_premises are complete declarative sentences
  2 = Two of the three are fully met; one is vague or incomplete
  1 = Only one is fully met; the other two are vague or absent
  0 = core_thesis is a question or vague direction, and argument structure is absent

STEP 3 — Strongest Objection Specificity (2 pts)
Read the strongest_objection field. Ask: Does it name the specific counterargument, counterexample, or reductio that most directly threatens the thesis — or does it give a generic objection?
Failures: "the thesis might be wrong", "critics may disagree", "this is controversial", "further argument is needed"
  2 = Names the specific philosophical move — the counterexample, the reductio, or the competing commitment — with enough detail that a philosopher in the subfield would recognize the objection
  1 = Identifies a general type of objection but does not name the specific move
  0 = Generic statement that the thesis faces objections, with no philosophical specificity

STEP 4 — Thought Experiment Quality (2 pts)
Read the thought_experiment field. Ask: Does it design a specific scenario with named setup, predicted result, and refuting result — or does it gesture at a thought experiment?
Failures: "consider a thought experiment", "imagine a scenario", "one could design a case"
  2 = Specific scenario with named setup + what the thesis predicts + what would refute it
  1 = A scenario is described but the refuting condition or the thesis's prediction is absent
  0 = No thought experiment, or only "consider a thought experiment" without a scenario

STEP 5 — Citations (1 pt)
Count [index] citations across the full evaluation text.
  1 = At least 5 [index] citations appear, spread across at least two different sections
  0 = Fewer than 5 citations, or all clustered in one section, or absent entirely

SCORING: Add up points from each step. Do not round up. Do not give partial credit within a criterion.

Return ONLY valid JSON — no commentary, no markdown:
{{
  "step1_sentence_quality": <0-2>,
  "step2_argument_precision": <0-3>,
  "step3_strongest_objection": <0-2>,
  "step4_thought_experiment": <0-2>,
  "step5_citations": <0-1>,
  "score": <sum of all steps, 0-10>,
  "verdict": "<2-3 sentences naming the specific fields that failed and why>",
  "specific_failures": ["<exact field + exact reason it failed>"],
  "specific_wins": ["<exact field that met the standard and why>"]
}}

IDEA: {raw_idea}

EVALUATION:
{evaluation}
"""


PHIL_JUDGE2_PROMPT = """You are a learning value auditor for a philosophical argument evaluation system.

Your job: assess whether this evaluation would genuinely teach a philosopher something non-obvious about the argument's place in the literature, its logical vulnerabilities, and its connections to live debates. You are NOT judging the philosophy — you are grading whether the evaluation has real intellectual content.

MANDATORY THOUGHT PROCESS — work through each criterion before scoring:

STEP 1 — Analyst Take Quality (3 pts)
Read the analyst_take field carefully. Check ALL four of:
  (a) Does it NOT open with "As a philosopher", "As a logician", "As a researcher", or any role declaration?
  (b) Does it name a specific non-obvious insight — something that reframes the thesis or connects it to an unexpected domain, NOT already stated in prior_art or argument_analysis?
  (c) Does it name the single objection that most threatens the argument — not "critics may disagree" but the specific move?
  (d) Does it tell the person ONE specific paper to read, distinction to draw, or thought experiment to run first — not "engage with the literature" or "develop the argument"?
  3 = All four criteria met
  2 = Three criteria met
  1 = Two criteria met
  0 = Zero or one criteria met, or opens with a role declaration, or is a summary restatement

STEP 2 — Non-Obvious Insight (2 pts)
Ask: Does the evaluation surface an insight that reframes the argument — connects it to an unexpected domain, reveals a hidden logical dependency, or identifies why the conventional response to this type of argument fails here?
  2 = The insight is genuinely surprising and changes how you think about the argument
  1 = The insight is interesting but derivable from reading the thesis framing alone
  0 = No genuine insight — the evaluation only summarizes the argument or reports the obvious

STEP 3 — India Philosophy Context Specificity (2 pts)
Read india_philosophy_context. Ask: Does it name a specific Indian institution, the correct funding body (ICPR with grant range), and a specific Indian philosophical tradition directly relevant to this thesis?
  2 = Specific institution + ICPR funding + named Indian tradition with direct relevance to this argument
  1 = India mentioned with some specificity but tradition or institution is generic
  0 = Absent, or only "Indian philosophy has relevant traditions" without naming them

STEP 4 — Prior Art Accuracy (2 pts)
Check closest_arguments. Ask: Are the named positions or papers real and verifiable? Do entries describe what was argued and how it relates to this thesis?
  2 = Named positions and papers are real, arguments are accurately described, relevance to this thesis is explained
  1 = Positions are named but described too briefly to verify, or relevance is asserted without explanation
  0 = Positions appear invented, arguments are misrepresented, or entries are generic field summaries

STEP 5 — Final Summary Actionability (1 pt)
Read final_summary. Does it end with ONE specific paper, SEP entry, anthology chapter, or philosopher to engage with next?
  1 = Ends with one specific, named next step
  0 = Ends vaguely or with generic advice to "engage with the literature"

SCORING: Add up points from each step. Do not round up.

Return ONLY valid JSON — no commentary, no markdown:
{{
  "step1_analyst_take": <0-3>,
  "step2_nonobvious_insight": <0-2>,
  "step3_india_context": <0-2>,
  "step4_prior_art_accuracy": <0-2>,
  "step5_final_summary": <0-1>,
  "score": <sum of all steps, 0-10>,
  "verdict": "<2-3 sentences: what had real philosophical content and what was empty or generic>",
  "what_was_missing": ["<specific gap with the exact field or section it appears in>"],
  "what_worked": ["<specific thing that genuinely taught something non-obvious>"]
}}

IDEA: {raw_idea}

EVALUATION:
{evaluation}
"""


PHIL_FIXER_PROMPT = """You are an expert prompt engineer specializing in LLM philosophical argument evaluation prompts.

You are given a prompt that instructs an LLM to evaluate philosophical arguments,
plus judge feedback showing exactly what the prompt failed to produce across multiple ideas.

Your job: rewrite the PHILOSOPHY_PROMPT so the next evaluation run fixes all identified failures.

GROUND RULES — follow exactly:
1. Do NOT change the JSON schema. Output structure must remain identical.
2. Do NOT remove existing instructions — only strengthen or add more specific ones.
3. List fields: every item in closest_arguments, key_premises, possible_responses, relevant_institutions must be a complete sentence with subject and verb. Labels and fragments are not acceptable.
4. Argument precision: core_thesis must be a precise philosophical claim — not a question, not a direction. logical_structure must name the argument form and trace premises to conclusion. key_premises must be complete declarative sentences stating what the argument requires to be true.
5. Strongest objection: must name the specific counterargument, counterexample, or reductio — not "critics may disagree" or "this is controversial."
6. Thought experiment: must design a specific scenario with named setup, the thesis's prediction, and the result that would refute it — not "consider a thought experiment."
7. Analyst take: must NOT open with "As a philosopher", "As a logician", or any role declaration. Must name a non-obvious insight, the single most dangerous objection, and ONE specific paper or distinction — not generic advice to "develop the argument."
8. Scores: different arguments at different stages, in different domains, with different objection profiles MUST receive different scores. Uniform scores signal lazy evaluation.
9. Citations: require minimum 5 [index] citations spread across prior_art, argument_analysis, and india_philosophy_context.
10. India philosophy context: require a specific institution, ICPR funding with grant range, and a named Indian philosophical tradition directly relevant to THIS thesis — not generic statements about Indian philosophy.
11. Final summary: must end with one specific paper, SEP entry, anthology chapter, or philosopher — not a general suggestion.
12. Maintain the same structure: role framing → rules → classification → scoring calibration → idea/research injection → schema.
13. Output must be placed verbatim inside triple quotes in Python — no escape issues, no markdown fences.

CURRENT PROMPT:
{current_prompt}

JUDGE 1 FEEDBACK (Structural Quality) — Average: {j1_avg}/10:
{j1_feedback}

JUDGE 2 FEEDBACK (Learning Value) — Average: {j2_avg}/10:
{j2_feedback}

Return ONLY the new prompt text. No JSON wrapper. No markdown. No commentary.
"""


# ── Philosophy prompt extraction / replacement ────────────────────────────────

def extract_philosophy_prompt():
    with open(EVALUATOR_PATH, "r", encoding="utf-8") as f:
        content = f.read()
    match = re.search(r'PHILOSOPHY_PROMPT = """(.+?)"""', content, re.DOTALL)
    if not match:
        raise ValueError("Could not find PHILOSOPHY_PROMPT in evaluator.py")
    return match.group(1)


def replace_philosophy_prompt(new_prompt):
    with open(EVALUATOR_PATH, "r", encoding="utf-8") as f:
        content = f.read()
    new_content = re.sub(
        r'(PHILOSOPHY_PROMPT = """)(.+?)(""")',
        lambda m: m.group(1) + new_prompt + m.group(3),
        content,
        flags=re.DOTALL
    )
    with open(EVALUATOR_PATH, "w", encoding="utf-8") as f:
        f.write(new_content)


# ── Society judges / fixer ───────────────────────────────────────────────────

SOC_JUDGE1_PROMPT = """You are a strict structural auditor for a social science hypothesis evaluation system.

Your job: check whether this evaluation meets specific quality standards. You are NOT judging the hypothesis — you are grading the evaluation's execution.

MANDATORY THOUGHT PROCESS — work through each criterion before scoring:

STEP 1 — Sentence Quality in List Fields (2 pts)
Check every item in: closest_studies, required_data, confounds, alternative_explanations, relevant_institutions.
Ask: Is each item a complete sentence with a subject and verb? A bare concept ("caste mobility"), a label ("panel data"), or a fragment ("WhatsApp usage patterns") is NOT a sentence.
  2 = Every list item across the entire evaluation is a grammatically complete sentence
  1 = Most are sentences; up to 2 items are fragments or labels
  0 = Three or more list items are fragments, labels, or incomplete phrases

STEP 2 — Hypothesis Precision (3 pts)
Check: core_claim and falsifiability fields.
Ask: Does core_claim name WHO does WHAT under WHAT CONDITIONS with WHAT EFFECT? Does falsifiability name the specific empirical observation that would prove the claim false — not "if data disagrees"?
  3 = core_claim has all four elements AND falsifiability names a specific refuting pattern or null result
  2 = core_claim is directionally clear but missing one element, OR falsifiability is present but vague
  1 = core_claim is directional but non-specific, AND falsifiability says only "if data disagrees" or is absent
  0 = core_claim is untestable, unfalsifiable, or absent

STEP 3 — Critical Test Specificity (2 pts)
Read the critical_test field. Ask: Does it name a specific comparison, regression, or natural experiment using named data sources that cuts through confounds?
Failures: "collect more data", "run a survey", "analyze the data", naming only a method category without a specific dataset
  2 = Names a specific comparison or identification strategy with a named dataset (IHDS, NFHS, NSSO, etc.) and explains how it controls for the main confounds
  1 = A test is described but the data source is generic or the confound control is not explained
  0 = critical_test is absent, or describes only "collecting data" or "conducting a survey"

STEP 4 — Confound Depth (2 pts)
Check each confounds entry. Does it name a specific third variable, selection effect, or reverse causality — or is it generic?
Generic failures: "correlation is not causation", "confounding variables may exist", "other factors could explain this"
  2 = Every confound names a specific mechanism — the exact third variable, selection process, or reverse causality that produces the same pattern without the hypothesized cause
  1 = At least one confound is specific; rest are vague or generic
  0 = All confounds are generic — could apply to any social observation

STEP 5 — Citations (1 pt)
Count [index] citations across the full evaluation text.
  1 = At least 5 [index] citations appear, spread across at least two different sections
  0 = Fewer than 5 citations, or all clustered in one section, or absent entirely

SCORING: Add up points from each step. Do not round up. Do not give partial credit within a criterion.

Return ONLY valid JSON — no commentary, no markdown:
{{
  "step1_sentence_quality": <0-2>,
  "step2_hypothesis_precision": <0-3>,
  "step3_critical_test": <0-2>,
  "step4_confound_depth": <0-2>,
  "step5_citations": <0-1>,
  "score": <sum of all steps, 0-10>,
  "verdict": "<2-3 sentences naming the specific fields that failed and why>",
  "specific_failures": ["<exact field + exact reason it failed>"],
  "specific_wins": ["<exact field that met the standard and why>"]
}}

IDEA: {raw_idea}

EVALUATION:
{evaluation}
"""


SOC_JUDGE2_PROMPT = """You are a learning value auditor for a social science hypothesis evaluation system.

Your job: assess whether this evaluation would genuinely teach a researcher something non-obvious about the hypothesis's place in the sociological literature, its confounds, and its testability. You are NOT judging the hypothesis — you are grading whether the evaluation has real intellectual content.

MANDATORY THOUGHT PROCESS — work through each criterion before scoring:

STEP 1 — Analyst Take Quality (3 pts)
Read the analyst_take field carefully. Check ALL four of:
  (a) Does it NOT open with "As a sociologist", "As a researcher", "As a social scientist", or any role declaration?
  (b) Does it name a specific non-obvious insight — something that reframes the claim or connects it to an unexpected domain, NOT already stated in the prior_art or evidence_and_method sections?
  (c) Does it name the single most dangerous confound — not "confounding variables may exist" but the specific mechanism?
  (d) Does it tell the person ONE specific dataset, comparison, or natural experiment to run first — not "conduct further research" or "collect data"?
  3 = All four criteria met
  2 = Three criteria met
  1 = Two criteria met
  0 = Zero or one criteria met, or opens with a role declaration, or is a summary restatement

STEP 2 — Non-Obvious Insight (2 pts)
Ask: Does the evaluation surface an insight that reframes the hypothesis — connects it to an unexpected domain, reveals a hidden structural dynamic, or identifies why the conventional explanation of the pattern is incomplete?
  2 = The insight is genuinely surprising — it changes how you think about the claim and is not derivable from reading the hypothesis framing alone
  1 = The insight is interesting but predictable from the hypothesis framing
  0 = No genuine insight present — the evaluation only restates the hypothesis or reports the obvious

STEP 3 — India Context Specificity (2 pts)
Read india_social_context. Ask: Does it name a specific Indian institution that studies this domain, the correct funding body (ICSSR/CSDS/NCAER/DST) with realistic grant range, and explain what makes India structurally interesting or limiting for THIS particular hypothesis?
  2 = Specific institution + specific funding body + India-specific structural feature tied to this hypothesis
  1 = India mentioned with some specificity but not tied to the structural constraints of this particular hypothesis
  0 = Absent, or only "Indian universities are studying this" or "government funding is available"

STEP 4 — Prior Art Accuracy (2 pts)
Check closest_studies. Ask: Are the named studies real and verifiable? Do entries describe what those researchers found and how it relates to this hypothesis?
  2 = Named studies are real, findings are accurately described, relevance to this hypothesis is explained
  1 = Studies are named but described too briefly to verify, or relevance is stated without explanation
  0 = Studies appear invented, findings are misrepresented, or entries are generic field summaries

STEP 5 — Final Summary Actionability (1 pt)
Read final_summary. Does it end with ONE specific thing — a named dataset (NFHS, IHDS, NSSO, NES), a named institution, or a named researcher group — not a generic suggestion?
  1 = Ends with one specific, named next step
  0 = Ends vaguely or with generic advice to "review the literature" or "conduct research"

SCORING: Add up points from each step. Do not round up.

Return ONLY valid JSON — no commentary, no markdown:
{{
  "step1_analyst_take": <0-3>,
  "step2_nonobvious_insight": <0-2>,
  "step3_india_context": <0-2>,
  "step4_prior_art_accuracy": <0-2>,
  "step5_final_summary": <0-1>,
  "score": <sum of all steps, 0-10>,
  "verdict": "<2-3 sentences: what had real social science content and what was empty or generic>",
  "what_was_missing": ["<specific gap with the exact field or section it appears in>"],
  "what_worked": ["<specific thing that genuinely taught something non-obvious>"]
}}

IDEA: {raw_idea}

EVALUATION:
{evaluation}
"""


SOC_FIXER_PROMPT = """You are improving a social science evaluation prompt.

Current prompt (between the markers):
===BEGIN===
{current_prompt}
===END===

Judge 1 (Structural Quality) average score: {j1_avg}/10
Judge 2 (Learning Value) average score: {j2_avg}/10

Judge 1 failures across all evaluated ideas:
{j1_feedback}

Judge 2 failures across all evaluated ideas:
{j2_feedback}

Your task:
Rewrite the prompt to fix the specific failures above. Do NOT change the schema, classification labels, or scoring calibration. Do NOT make the prompt shorter. Focus only on:
- Tightening writing rules for fields that keep producing fragments
- Adding or strengthening examples for fields that keep producing vague or generic content
- Clarifying what "specific" means for confounds, critical_test, and required_data

Return ONLY the new prompt text. No JSON wrapper. No markdown. No commentary.
"""


# ── Society prompt extraction / replacement ──────────────────────────────────

def extract_society_prompt():
    with open(EVALUATOR_PATH, "r", encoding="utf-8") as f:
        content = f.read()
    match = re.search(r'SOCIETY_PROMPT = """(.+?)"""', content, re.DOTALL)
    if not match:
        raise ValueError("Could not find SOCIETY_PROMPT in evaluator.py")
    return match.group(1)


def replace_society_prompt(new_prompt):
    with open(EVALUATOR_PATH, "r", encoding="utf-8") as f:
        content = f.read()
    new_content = re.sub(
        r'(SOCIETY_PROMPT = """)(.+?)(""")',
        lambda m: m.group(1) + new_prompt + m.group(3),
        content,
        flags=re.DOTALL
    )
    with open(EVALUATOR_PATH, "w", encoding="utf-8") as f:
        f.write(new_content)


# ── Generic optimizer loop ────────────────────────────────────────────────────

CATEGORY_CONFIG = {
    "Business": {
        "judge1":         lambda: JUDGE1_PROMPT,
        "judge2":         lambda: JUDGE2_PROMPT,
        "fixer":          lambda: FIXER_PROMPT,
        "extract_prompt": extract_business_prompt,
        "replace_prompt": replace_business_prompt,
        "prompt_name":    "BUSINESS_PROMPT",
        "history_file":   lambda: os.path.join(PROJECT_ROOT, "prompt_history.json"),
        # step name → max points (must match judge JSON output keys)
        "judge1_steps": {
            "step1_sentence_quality":  2,
            "step2_unit_economics":    3,
            "step3_competitive_depth": 2,
            "step4_weakest_links":     2,
            "step5_citations":         1,
        },
        "judge2_steps": {
            "step1_analyst_take":       3,
            "step2_nonobvious_insight": 2,
            "step3_honest_positioning": 2,
            "step4_india_context":      2,
            "step5_final_summary":      1,
        },
    },
    "Technology": {
        "judge1":         lambda: TECH_JUDGE1_PROMPT,
        "judge2":         lambda: TECH_JUDGE2_PROMPT,
        "fixer":          lambda: TECH_FIXER_PROMPT,
        "extract_prompt": extract_technology_prompt,
        "replace_prompt": replace_technology_prompt,
        "prompt_name":    "TECHNOLOGY_PROMPT",
        "history_file":   lambda: os.path.join(PROJECT_ROOT, "tech_prompt_history.json"),
        "judge1_steps": {
            "step1_sentence_quality":      2,
            "step2_technical_specificity": 3,
            "step3_moat_honesty":          2,
            "step4_weakest_assumptions":   2,
            "step5_citations":             1,
        },
        "judge2_steps": {
            "step1_analyst_take":         3,
            "step2_nonobvious_insight":   2,
            "step3_india_context":        2,
            "step4_competitive_accuracy": 2,
            "step5_final_summary":        1,
        },
        # Steps where research availability limits achievable scores — use 50% floor instead of 75%
        "low_floor_steps": ["step3_india_context"],
    },
    "Engineering": {
        "judge1":         lambda: ENG_JUDGE1_PROMPT,
        "judge2":         lambda: ENG_JUDGE2_PROMPT,
        "fixer":          lambda: ENG_FIXER_PROMPT,
        "extract_prompt": extract_engineering_prompt,
        "replace_prompt": replace_engineering_prompt,
        "prompt_name":    "ENGINEERING_PROMPT",
        "history_file":   lambda: os.path.join(PROJECT_ROOT, "eng_prompt_history.json"),
        "judge1_steps": {
            "step1_sentence_quality":      2,
            "step2_engineering_specificity": 3,
            "step3_moat_honesty":          2,
            "step4_weakest_assumptions":   2,
            "step5_citations":             1,
        },
        "judge2_steps": {
            "step1_analyst_take":         3,
            "step2_nonobvious_insight":   2,
            "step3_india_context":        2,
            "step4_competitive_accuracy": 2,
            "step5_final_summary":        1,
        },
        "low_floor_steps": ["step3_india_context"],
    },
    "Science": {
        "judge1":         lambda: SCI_JUDGE1_PROMPT,
        "judge2":         lambda: SCI_JUDGE2_PROMPT,
        "fixer":          lambda: SCI_FIXER_PROMPT,
        "extract_prompt": extract_science_prompt,
        "replace_prompt": replace_science_prompt,
        "prompt_name":    "SCIENCE_PROMPT",
        "history_file":   lambda: os.path.join(PROJECT_ROOT, "sci_prompt_history.json"),
        "judge1_steps": {
            "step1_sentence_quality":     2,
            "step2_hypothesis_precision": 3,
            "step3_critical_experiment":  2,
            "step4_failure_modes":        2,
            "step5_citations":            1,
        },
        "judge2_steps": {
            "step1_analyst_take":       3,
            "step2_nonobvious_insight": 2,
            "step3_india_context":      2,
            "step4_prior_art_accuracy": 2,
            "step5_final_summary":      1,
        },
        "low_floor_steps": ["step3_india_context"],
    },
    "Mathematics": {
        "judge1":         lambda: MATH_JUDGE1_PROMPT,
        "judge2":         lambda: MATH_JUDGE2_PROMPT,
        "fixer":          lambda: MATH_FIXER_PROMPT,
        "extract_prompt": extract_mathematics_prompt,
        "replace_prompt": replace_mathematics_prompt,
        "prompt_name":    "MATHEMATICS_PROMPT",
        "history_file":   lambda: os.path.join(PROJECT_ROOT, "math_prompt_history.json"),
        "judge1_steps": {
            "step1_sentence_quality":    2,
            "step2_conjecture_precision": 3,
            "step3_critical_obstacle":   2,
            "step4_counterexample_risks": 2,
            "step5_citations":           1,
        },
        "judge2_steps": {
            "step1_analyst_take":       3,
            "step2_nonobvious_insight": 2,
            "step3_india_context":      2,
            "step4_prior_art_accuracy": 2,
            "step5_final_summary":      1,
        },
        "low_floor_steps": ["step3_india_context"],
    },
    "Other": {
        "judge1":         lambda: OTHER_JUDGE1_PROMPT,
        "judge2":         lambda: OTHER_JUDGE2_PROMPT,
        "fixer":          lambda: OTHER_FIXER_PROMPT,
        "extract_prompt": extract_other_prompt,
        "replace_prompt": replace_other_prompt,
        "prompt_name":    "OTHER_PROMPT",
        "history_file":   lambda: os.path.join(PROJECT_ROOT, "other_prompt_history.json"),
        "judge1_steps": {
            "step1_sentence_quality":        2,
            "step2_precision_and_dependency": 3,
            "step3_failure_modes":           2,
            "step4_minimum_viable_test":     2,
            "step5_citations":               1,
        },
        "judge2_steps": {
            "step1_analyst_take":           3,
            "step2_nonobvious_insight":     2,
            "step3_india_relevance":        2,
            "step4_prior_context_accuracy": 2,
            "step5_final_summary":          1,
        },
        "low_floor_steps": ["step3_india_relevance"],
    },
    "Personal": {
        "judge1":         lambda: PERS_JUDGE1_PROMPT,
        "judge2":         lambda: PERS_JUDGE2_PROMPT,
        "fixer":          lambda: PERS_FIXER_PROMPT,
        "extract_prompt": extract_personal_prompt,
        "replace_prompt": replace_personal_prompt,
        "prompt_name":    "PERSONAL_PROMPT",
        "history_file":   lambda: os.path.join(PROJECT_ROOT, "pers_prompt_history.json"),
        "judge1_steps": {
            "step1_sentence_quality":          2,
            "step2_implementation_specificity": 3,
            "step3_failure_modes":             2,
            "step4_mechanism_clarity":         2,
            "step5_citations":                 1,
        },
        "judge2_steps": {
            "step1_analyst_take":       3,
            "step2_nonobvious_insight": 2,
            "step3_india_context":      2,
            "step4_evidence_accuracy":  2,
            "step5_final_summary":      1,
        },
        "low_floor_steps": ["step3_india_context"],
    },
    "Philosophy": {
        "judge1":         lambda: PHIL_JUDGE1_PROMPT,
        "judge2":         lambda: PHIL_JUDGE2_PROMPT,
        "fixer":          lambda: PHIL_FIXER_PROMPT,
        "extract_prompt": extract_philosophy_prompt,
        "replace_prompt": replace_philosophy_prompt,
        "prompt_name":    "PHILOSOPHY_PROMPT",
        "history_file":   lambda: os.path.join(PROJECT_ROOT, "phil_prompt_history.json"),
        "judge1_steps": {
            "step1_sentence_quality":    2,
            "step2_argument_precision":  3,
            "step3_strongest_objection": 2,
            "step4_thought_experiment":  2,
            "step5_citations":           1,
        },
        "judge2_steps": {
            "step1_analyst_take":       3,
            "step2_nonobvious_insight": 2,
            "step3_india_context":      2,
            "step4_prior_art_accuracy": 2,
            "step5_final_summary":      1,
        },
        "low_floor_steps": ["step3_india_context"],
    },
    "Society": {
        "judge1":         lambda: SOC_JUDGE1_PROMPT,
        "judge2":         lambda: SOC_JUDGE2_PROMPT,
        "fixer":          lambda: SOC_FIXER_PROMPT,
        "extract_prompt": extract_society_prompt,
        "replace_prompt": replace_society_prompt,
        "prompt_name":    "SOCIETY_PROMPT",
        "history_file":   lambda: os.path.join(PROJECT_ROOT, "soc_prompt_history.json"),
        "judge1_steps": {
            "step1_sentence_quality":   2,
            "step2_hypothesis_precision": 3,
            "step3_critical_test":      2,
            "step4_confound_depth":     2,
            "step5_citations":          1,
        },
        "judge2_steps": {
            "step1_analyst_take":       3,
            "step2_nonobvious_insight": 2,
            "step3_india_context":      2,
            "step4_prior_art_accuracy": 2,
            "step5_final_summary":      1,
        },
        "low_floor_steps": ["step3_india_context"],
    },
}


def run_optimizer(category="Business"):
    cfg          = CATEGORY_CONFIG[category]
    history_path = cfg["history_file"]()
    history      = json.load(open(history_path)) if os.path.exists(history_path) else {"iterations": []}
    iteration    = len(history["iterations"])
    session_start = time.time()

    print(flush=True)
    log_sep("=")
    log(f"PROMPT OPTIMIZER — {category} Evaluator")
    log(f"Starting at iteration  : {iteration}")
    log(f"Stop threshold         : {THRESHOLD}/10 on BOTH judges")
    log(f"Max iterations         : {MAX_ITERATIONS}")
    log(f"History file           : {os.path.basename(history_path)}")
    log(f"Estimated time/iter    : ~7-10 min (judging + reprocess)")
    log_sep("=")

    while iteration <= MAX_ITERATIONS:
        iter_start = time.time()
        print(flush=True)
        log_sep()
        log(f"ITERATION {iteration} / {MAX_ITERATIONS}  --  started at {ts()}")
        log_sep()

        log(f"Loading current {cfg['prompt_name']} from evaluator.py...")
        current_prompt = cfg["extract_prompt"]()
        log(f"Prompt loaded  ({len(current_prompt)} chars)", indent=1)

        log(f"Loading {category} ideas from DB...")
        all_ideas      = load_all_ideas()
        target_ideas   = [i for i in all_ideas if i.get("category") == category]

        if not target_ideas:
            log(f"No {category} ideas found in DB. Submit some ideas first, then rerun.")
            return

        log(f"Found {len(target_ideas)} {category} ideas to judge", indent=1)

        print(flush=True)
        log(f"STEP 1/4 — Judging {len(target_ideas)} ideas (2 judges each = {len(target_ideas)*2} LLM calls)")

        idea_records = []
        j1_scores    = []
        j2_scores    = []

        j1_template = cfg["judge1"]()
        j2_template = cfg["judge2"]()

        for idx, idea in enumerate(target_ideas, 1):
            idea_t = time.time()
            log(f"Idea {idx}/{len(target_ideas)}  #{idea['id']}: {idea['raw_idea'][:55]}...")

            evaluation = idea["analysis"].get("evaluation", {})
            ev_str     = json.dumps(evaluation, indent=2)

            for jnum, (label, template) in enumerate(
                [("Judge 1 (Structural Quality)", j1_template),
                 ("Judge 2 (Learning Value)", j2_template)], 1
            ):
                log(f"Running {label}...", indent=2)
                jt = time.time()
                prompt   = template.format(raw_idea=idea["raw_idea"], evaluation=ev_str)
                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.2
                )
                raw = response.choices[0].message.content.strip()
                raw = re.sub(r"^```json\s*", "", raw)
                raw = re.sub(r"\s*```$", "", raw)
                try:
                    result = json.loads(raw)
                except Exception:
                    result = {"score": 0, "verdict": raw, "specific_failures": [],
                              "specific_wins": [], "what_was_missing": [], "what_worked": []}

                log(f"{label} done  ({elapsed(jt)})  ->  score: {result['score']}/10", indent=2)
                log(f"Verdict: {result.get('verdict','')[:100]}", indent=3)

                if jnum == 1:
                    j1 = result
                    j1_scores.append(j1["score"])
                    if j1.get("specific_failures"):
                        log(f"Failures: {j1['specific_failures']}", indent=3)
                else:
                    j2 = result
                    j2_scores.append(j2["score"])
                    if j2.get("what_was_missing"):
                        log(f"Missing: {j2['what_was_missing']}", indent=3)

            idea_records.append({
                "id":         idea["id"],
                "raw_idea":   idea["raw_idea"],
                "evaluation": evaluation,
                "judge1":     j1,
                "judge2":     j2,
            })
            log(f"Idea {idx} done  ({elapsed(idea_t)})", indent=1)

        j1_avg   = sum(j1_scores) / len(j1_scores)
        j2_avg   = sum(j2_scores) / len(j2_scores)
        combined = (j1_avg + j2_avg) / 2

        # Step-level gate: each criterion must average >= 75% of its max
        step_failures    = check_step_thresholds(idea_records, cfg)
        avgs_pass        = j1_avg >= THRESHOLD and j2_avg >= THRESHOLD
        threshold_met    = avgs_pass and not step_failures

        print(flush=True)
        log("-- Aggregate Scores --")
        log(f"Judge 1 (Structural)   avg : {j1_avg:.2f}/10   individual: {j1_scores}", indent=1)
        log(f"Judge 2 (Learning)     avg : {j2_avg:.2f}/10   individual: {j2_scores}", indent=1)
        log(f"Combined                   : {combined:.2f}/10", indent=1)
        log(f"Overall threshold ({THRESHOLD}) met : {'YES' if avgs_pass else 'NO'}", indent=1)
        if step_failures:
            log(f"Step-level gate (75%)      : FAILED -- {len(step_failures)} step(s) below floor", indent=1)
            for sf in step_failures:
                log(sf, indent=2)
        else:
            log(f"Step-level gate (75%)      : PASSED", indent=1)
        log(f"Both gates met             : {'YES' if threshold_met else 'NO -- will improve prompt'}", indent=1)

        print(flush=True)
        log("STEP 2/4 -- Saving iteration to history file...")
        history["iterations"].append({
            "iteration":   iteration,
            "timestamp":   datetime.now().isoformat(),
            "prompt":      current_prompt,
            "ideas":       idea_records,
            "scores": {
                "judge1_avg":    round(j1_avg, 2),
                "judge2_avg":    round(j2_avg, 2),
                "combined":      round(combined, 2),
                "step_failures": step_failures,
                "threshold_met": threshold_met,
            },
        })
        with open(history_path, "w", encoding="utf-8") as f:
            json.dump(history, f, indent=2)
        log(f"Saved  (iteration {iteration} now in history)", indent=1)

        if threshold_met:
            print(flush=True)
            log_sep("=")
            log(f"DONE -- Both judges >= {THRESHOLD} AND all steps >= 75%. Prompt is good.")
            log(f"Total session time: {elapsed(session_start)}")
            log_sep("=")
            return

        if iteration >= MAX_ITERATIONS:
            print(flush=True)
            log_sep("=")
            log(f"Max iterations ({MAX_ITERATIONS}) reached.")
            log(f"Total session time: {elapsed(session_start)}")
            log_sep("=")
            return

        print(flush=True)
        log(f"STEP 3/4 -- Generating improved {cfg['prompt_name']} via Fixer LLM...")
        fixer_prompt = cfg["fixer"]()
        j1_lines = []
        j2_lines = []
        for r in idea_records:
            label = f"Idea #{r['id']}: {r['raw_idea'][:55]}..."
            j1_lines.append(f"{label}\n  Score: {r['judge1']['score']}/10\n  Failures: {r['judge1'].get('specific_failures', [])}\n  Verdict: {r['judge1'].get('verdict', '')}")
            j2_lines.append(f"{label}\n  Score: {r['judge2']['score']}/10\n  Missing: {r['judge2'].get('what_was_missing', [])}\n  Verdict: {r['judge2'].get('verdict', '')}")

        step_gate_section = ""
        if step_failures:
            step_gate_section = (
                "\n\nSTEP-LEVEL GATE FAILURES (criteria averaging below 75% of max across all ideas):\n"
                + "\n".join(f"  - {sf}" for sf in step_failures)
                + "\nThese specific criteria MUST improve in the next iteration or the prompt will not pass."
            )

        fix_t    = time.time()
        fix_resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": fixer_prompt.format(
                current_prompt=current_prompt,
                j1_avg=round(j1_avg, 2),
                j2_avg=round(j2_avg, 2),
                j1_feedback="\n\n".join(j1_lines) + step_gate_section,
                j2_feedback="\n\n".join(j2_lines),
            )}],
            temperature=0.4
        )
        new_prompt = fix_resp.choices[0].message.content.strip()
        log(f"Fixer done  ({elapsed(fix_t)})  ->  new prompt: {len(new_prompt)} chars", indent=1)

        log(f"Replacing {cfg['prompt_name']} in core/evaluator.py...", indent=1)
        cfg["replace_prompt"](new_prompt)
        log("Replaced. evaluator.py updated.", indent=1)

        print(flush=True)
        log("STEP 4/4 -- Running reprocess with new prompt...")
        success = run_reprocess()
        if not success:
            log("Reprocess failed. Fix the error and rerun.")
            return

        log(f"Iteration {iteration} complete  (total: {elapsed(iter_start)})")
        iteration += 1

    log("Optimizer finished.")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--category", default="Business", choices=list(CATEGORY_CONFIG.keys()))
    args = parser.parse_args()
    run_optimizer(category=args.category)
