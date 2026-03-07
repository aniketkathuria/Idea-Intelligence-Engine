from duckduckgo_search import DDGS
from config import DEFAULT_QUERY_COUNT, SEARCH_DEPTH


def generate_search_queries(idea, llm_client):
    prompt = f"""
        Generate {DEFAULT_QUERY_COUNT} search queries to research the following idea.

        Return ONLY a JSON array of queries.

        Idea:
        {idea}
        """

    response = llm_client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}]
    )

    import json
    return json.loads(response.choices[0].message.content)


def search_duckduckgo(queries, depth="balanced"):
    results_limit = SEARCH_DEPTH.get(depth, 10)

    collected_results = []

    with DDGS() as ddgs:
        for query in queries:
            results = ddgs.text(query, max_results=results_limit)

            for r in results:
                collected_results.append({
                    "title": r.get("title"),
                    "link": r.get("href"),
                    "snippet": r.get("body")
                })

    return collected_results