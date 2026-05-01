"""
Automated Business prompt optimization loop.

Run from project root:
    python backend/prompt_optimizer.py

Each iteration:
  1. Judges all Business idea evaluations in DB (Judge 1: quality, Judge 2: learning value)
  2. Saves prompt + all outputs + scores to prompt_history.json
  3. If both judge averages >= THRESHOLD, exits (prompt is good)
  4. Otherwise, fixes the prompt and reruns reprocess
  5. Repeats up to MAX_ITERATIONS times

After running, review prompt_history.json and pick the prompt from whichever
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

def log_sep(char="─", width=56):
    print(f"[{ts()}] {char * width}", flush=True)

def elapsed(start):
    s = int(time.time() - start)
    return f"{s//60}m {s%60}s" if s >= 60 else f"{s}s"

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

PROJECT_ROOT   = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
EVALUATOR_PATH = os.path.join(PROJECT_ROOT, "core", "evaluator.py")
REPROCESS_PATH = os.path.join(PROJECT_ROOT, "backend", "reprocess.py")

MAX_ITERATIONS = 4
THRESHOLD      = 7.5  # both judge averages must reach this to stop early


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
You are a strict output quality auditor for a business idea evaluation system.

Your job: assess whether this evaluation is STRUCTURALLY COMPLETE and DATA-RICH.
You are not judging whether the business idea is good. You are judging whether the evaluation did its job.

SCORING RUBRIC (total 10 points):

Unit Economics (3 pts):
  3 — All fields have actual estimates or first-principles reasoning (numbers, ranges, logic)
  2 — Most fields estimated, 1-2 are "unverified assumption"
  1 — Majority are "unverified assumption" or empty
  0 — Entire section is empty or all "unverified assumption"

Research Citations (2 pts):
  2 — At least 4 [index] citations used across the full evaluation
  1 — 1-3 citations used
  0 — Zero citations

Competitive Analysis (2 pts):
  2 — Each player has specific business model, specific edge, specific weakness — not generic
  1 — Players named but descriptions are vague or generic
  0 — No meaningful competitive analysis

Weakest Links (2 pts):
  2 — Each weakness is specific to THIS idea's assumptions — not generic business risks
  1 — Mix of specific and generic
  0 — All generic ("high competition", "market risk", etc.)

Whitespace (1 pt):
  1 — Specific gap identified with clear reasoning
  0 — Vague, absent, or states the obvious

Return ONLY valid JSON — no commentary, no markdown:
{{
  "score": <0-10 integer>,
  "verdict": "<2-3 sentences: what structurally failed and what worked>",
  "specific_failures": ["<exact field or section that failed, with why>"],
  "specific_wins": ["<what the evaluation got right structurally>"]
}}

IDEA: {raw_idea}

EVALUATION:
{evaluation}
"""


JUDGE2_PROMPT = """
You are a learning value auditor for a business idea evaluation system.

The purpose of this system is not to score pitches — it is to help people LEARN.
The ideal output feels like a conversation with a brilliant friend who has read everything:
takes the idea seriously, tells you where it already exists, what you got right, what to read next.

Your job: assess whether this evaluation would actually teach someone something new.

SCORING RUBRIC (total 10 points):

Non-obvious Market Insight (2 pts):
  2 — Reveals something the person likely didn't know: a specific trend, dynamic, or number
  1 — Some market context present but mostly states the obvious
  0 — Generic or superficial / no meaningful market insight

Competitive Intelligence (2 pts):
  2 — Reveals something non-obvious about a competitor: a specific weakness, gap, or surprising model
  1 — Names competitors but reveals nothing new
  0 — No competitive intelligence

Honest Positioning (2 pts):
  2 — Precise, unhedged verdict on where the idea actually sits in the landscape
  1 — Hedged, vague, or diplomatically empty
  0 — Absent or meaningless

Analyst Take (3 pts):
  3 — Reads like a person with a distinct POV: names one non-obvious insight, one biggest structural threat, one clear next action — in first person, not a report
  2 — Has a point of view but is generic or safe — could apply to any similar idea
  1 — Reads like a summary, not an opinion — no clear voice or stance
  0 — Absent or indistinguishable from the rest of the evaluation

Actionable Next Step (1 pt):
  1 — Final summary ends with one specific article, search term, or person to investigate
  0 — Vague, absent, or just repeats search queries already listed

Return ONLY valid JSON — no commentary, no markdown:
{{
  "score": <0-10 integer>,
  "verdict": "<2-3 sentences: what was intellectually useful and what was empty>",
  "what_was_missing": ["<specific thing that would have made this more educational>"],
  "what_worked": ["<what actually taught something>"]
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
    log_sep("·")
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
You are a strict output quality auditor for a technology idea evaluation system.

Your job: assess whether this evaluation is STRUCTURALLY COMPLETE and TECHNICALLY SPECIFIC.
You are not judging whether the tech idea is good. You are judging whether the evaluation did its job.

SCORING RUBRIC (total 10 points):

Technical Assessment (3 pts):
  3 — feasibility, core challenge, build complexity, stack requirements all have specific reasoning — no vague answers like "depends on implementation"
  2 — most fields are specific, 1-2 are vague or generic
  1 — majority are generic or empty
  0 — section is empty or useless

Competitive Analysis (2 pts):
  2 — each player has a specific approach, specific technical edge, specific weakness — not generic "large user base" type answers
  1 — players named but descriptions are shallow
  0 — no real competitive intelligence

Moat Analysis (2 pts):
  2 — moat is named precisely (network effects, proprietary data, switching costs, etc.) and explained for THIS idea specifically — OR honestly states there is no real moat
  1 — vague moat claim like "better UX" or "first mover" without specifics
  0 — moat field is empty or meaningless

Weakest Assumptions (2 pts):
  2 — each assumption is specific to THIS idea's structure — not generic tech risks like "user adoption is hard"
  1 — mix of specific and generic
  0 — all generic

Whitespace (1 pt):
  1 — exact gap named with clear reasoning why funded players haven't filled it
  0 — vague or obvious

Return ONLY valid JSON — no commentary, no markdown:
{{
  "score": <0-10 integer>,
  "verdict": "<2-3 sentences: what structurally failed and what worked>",
  "specific_failures": ["<exact field or section that failed, with why>"],
  "specific_wins": ["<what the evaluation got right structurally>"]
}}

IDEA: {raw_idea}

EVALUATION:
{evaluation}
"""


TECH_JUDGE2_PROMPT = """
You are a learning value auditor for a technology idea evaluation system.

The purpose of this system is not to score pitches — it is to help people LEARN.
The ideal output feels like a conversation with a senior engineer who has shipped products and seen what fails:
takes the idea seriously, tells you what's actually hard, who's already doing it, and what to build first.

Your job: assess whether this evaluation would actually teach a builder something useful.

SCORING RUBRIC (total 10 points):

Non-obvious Technical Insight (2 pts):
  2 — reveals something the person likely didn't know: a specific technical constraint, competitor approach, or infrastructure requirement
  1 — mostly states the obvious ("scaling is hard", "you need users")
  0 — no real technical insight

Honest Moat Assessment (2 pts):
  2 — gives a precise, unhedged verdict on whether there's a real moat and why
  1 — hedged or diplomatically empty
  0 — absent or misleading

India / Distribution Reality (2 pts):
  2 — specifically addresses why this might fail in India (pricing, infra, language, payment) OR why India is actually the right market
  1 — India mentioned but generically
  0 — India entirely absent

Analyst Take (3 pts):
  3 — reads like a technologist with a real opinion: names the specific non-obvious insight, names the specific thing that kills this, tells the person exactly what to build or validate first — not generic advice
  2 — has a point of view but could apply to any similar tech idea
  1 — reads like a summary, no distinct voice or stance
  0 — absent or indistinguishable from rest of evaluation

Actionable Next Step (1 pt):
  1 — final summary ends with one specific repo, paper, company, or person to study
  0 — vague, absent, or just repeats search queries

Return ONLY valid JSON — no commentary, no markdown:
{{
  "score": <0-10 integer>,
  "verdict": "<2-3 sentences: what was technically useful and what was empty>",
  "what_was_missing": ["<specific thing that would have made this more useful to a builder>"],
  "what_worked": ["<what actually taught something>"]
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
3. Technical assessment: force the LLM to always be specific — vague answers like "depends on implementation" or "requires engineering effort" are not acceptable.
4. Moat: require honest assessment — "better UX" and "first mover" are not moats. If there is no real moat, say so.
5. Citations: require minimum 5 [index] citations spread across problem space, competitive landscape, and technical assessment.
6. Competitive analysis: require identifying the single most dangerous competitor and explaining in one sentence exactly why they kill this idea if they ship one feature.
7. India context: require direct analysis of why this specifically fails or succeeds in India — not generic India market commentary.
8. Final summary: must end with one specific repo, paper, company, or person to study next.
9. Maintain the same structure: role framing → rules → classification → idea/research injection → schema.
10. Output must be placed verbatim inside triple quotes in Python — no escape issues, no markdown fences.

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
    },
    "Technology": {
        "judge1":         lambda: TECH_JUDGE1_PROMPT,
        "judge2":         lambda: TECH_JUDGE2_PROMPT,
        "fixer":          lambda: TECH_FIXER_PROMPT,
        "extract_prompt": extract_technology_prompt,
        "replace_prompt": replace_technology_prompt,
        "prompt_name":    "TECHNOLOGY_PROMPT",
        "history_file":   lambda: os.path.join(PROJECT_ROOT, "tech_prompt_history.json"),
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
        log(f"ITERATION {iteration} / {MAX_ITERATIONS}  —  started at {ts()}")
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
                    model="gpt-4o",
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

        j1_avg        = sum(j1_scores) / len(j1_scores)
        j2_avg        = sum(j2_scores) / len(j2_scores)
        combined      = (j1_avg + j2_avg) / 2
        threshold_met = j1_avg >= THRESHOLD and j2_avg >= THRESHOLD

        print(flush=True)
        log("-- Aggregate Scores --")
        log(f"Judge 1 (Structural)   avg : {j1_avg:.2f}/10   individual: {j1_scores}", indent=1)
        log(f"Judge 2 (Learning)     avg : {j2_avg:.2f}/10   individual: {j2_scores}", indent=1)
        log(f"Combined                   : {combined:.2f}/10", indent=1)
        log(f"Threshold ({THRESHOLD}) met    : {'YES' if threshold_met else 'NO -- will improve prompt'}", indent=1)

        print(flush=True)
        log("STEP 2/4 -- Saving iteration to history file...")
        history["iterations"].append({
            "iteration":  iteration,
            "timestamp":  datetime.now().isoformat(),
            "prompt":     current_prompt,
            "ideas":      idea_records,
            "scores": {
                "judge1_avg":    round(j1_avg, 2),
                "judge2_avg":    round(j2_avg, 2),
                "combined":      round(combined, 2),
                "threshold_met": threshold_met,
            },
        })
        with open(history_path, "w", encoding="utf-8") as f:
            json.dump(history, f, indent=2)
        log(f"Saved  (iteration {iteration} now in history)", indent=1)

        if threshold_met:
            print(flush=True)
            log_sep("=")
            log(f"DONE -- Both judges above {THRESHOLD}. Prompt is good.")
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

        fix_t    = time.time()
        fix_resp = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": fixer_prompt.format(
                current_prompt=current_prompt,
                j1_avg=round(j1_avg, 2),
                j2_avg=round(j2_avg, 2),
                j1_feedback="\n\n".join(j1_lines),
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
