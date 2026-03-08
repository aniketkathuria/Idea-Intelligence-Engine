import os
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def evaluate_idea(raw_text, research_results):
    formatted_research = ""

    for item in research_results[:15]:  # limit context
        formatted_research += f"""
Title: {item['title']}
Snippet: {item['snippet']}
Link: {item['link']}
"""

    prompt = f"""
You are a brutally honest idea evaluator.

User Idea:
{raw_text}

Web Research Findings:
{formatted_research}

Rules:
- Be direct.
- Identify logical flaws.
- Identify hidden assumptions.
- Rate novelty from 0-10.
- Rate feasibility from 0-10.
- Do NOT sugarcoat.
- Do NOT insult.
- Always provide improvement direction.
- Return ONLY valid JSON.
- Market analysis looks for product who currently exists (tell big companies and how much match is it)

Return JSON with keys:
idea_summary
Market_analysis
category
similar_existing_concepts
novelty_score
feasibility_score
core_flaws
hidden_assumptions
improvement_directions
brutal_truth
"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.4
    )

    return response.choices[0].message.content