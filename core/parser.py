import json
import os
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def parse_json_with_repair(raw_response):
    """
    Attempt to parse JSON.
    If parsing fails, enter repair mode using secondary API call.
    """

    try:
        return json.loads(raw_response)

    except json.JSONDecodeError:
        print("----Parsing-----")

        repair_prompt = f"""
You are a JSON formatting assistant.

The following text was intended to be valid JSON but is malformed.

Your job:
- Return ONLY valid JSON.
- Do NOT add explanations.
- Do NOT add markdown.
- Do NOT change the meaning.
- Fix formatting only.

Malformed content:
{raw_response}
"""

        repair_response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": repair_prompt}],
            temperature=0
        )

        repaired_text = repair_response.choices[0].message.content

        try:
            return json.loads(repaired_text)

        except json.JSONDecodeError:
            raise ValueError("Repair attempt failed. Invalid JSON returned.")