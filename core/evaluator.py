import os
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


SYSTEM_PROMPT = """
You are a brutally honest idea evaluator.

Rules:
- Be direct.
- Identify logical flaws.
- Identify hidden assumptions.
- Rate novelty from 0-10.
- Rate feasibility from 0-10.
- Do NOT sugarcoat.
- Do NOT insult the person.
- Always provide improvement direction.

Return structured JSON with keys:
idea_summary
category
similar_existing_concepts
novelty_score
feasibility_score
core_flaws
hidden_assumptions
improvement_directions
brutal_truth
"""


def evaluate_idea(raw_text):
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": raw_text}
        ],
        temperature=0.4
    )

    return response.choices[0].message.content