import logging
from concurrent.futures import ThreadPoolExecutor, as_completed

import httpx
from lxml.html import fromstring
from ddgs import DDGS
from config import DEFAULT_QUERY_COUNT, SEARCH_DEPTH

logger = logging.getLogger(__name__)

FETCH_TIMEOUT    = 8    # seconds per article fetch
FETCH_WORKERS    = 6    # parallel fetches
CONTENT_MAX_CHARS = 2000 # chars kept per article


def generate_search_queries(idea, llm_client):
    prompt = f"""
Generate {DEFAULT_QUERY_COUNT} search queries to research the following idea.

Return ONLY a JSON array of queries.
Make sure to have no comments, output will be going directly to json.loads
Idea:
{idea}
"""

    response = llm_client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0
    )

    from core.parser import parse_json_with_repair
    raw_output = response.choices[0].message.content
    return parse_json_with_repair(raw_output)


def _fetch_content(url: str) -> str | None:
    """Fetch and extract readable text from a URL. Returns None on any failure."""
    try:
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
            "Accept": "text/html,application/xhtml+xml",
        }
        resp = httpx.get(url, timeout=FETCH_TIMEOUT, headers=headers,
                         follow_redirects=True)

        if resp.status_code != 200:
            return None

        tree = fromstring(resp.text)

        # Strip noise elements
        for tag in tree.xpath("//script|//style|//nav|//footer|//header|//aside|//form"):
            p = tag.getparent()
            if p is not None:
                p.remove(tag)

        raw = tree.text_content()
        lines = [l.strip() for l in raw.splitlines() if l.strip()]
        content = " ".join(lines)
        return content[:CONTENT_MAX_CHARS] if content else None

    except Exception as e:
        logger.debug(f"Content fetch failed for {url}: {e}")
        return None


def _enrich_with_content(results: list[dict]) -> list[dict]:
    """Parallel-fetch full article content for each result."""
    enriched = [None] * len(results)

    def fetch_one(idx, item):
        content = _fetch_content(item["link"])
        return idx, {**item, "content": content or item["snippet"]}

    with ThreadPoolExecutor(max_workers=FETCH_WORKERS) as pool:
        futures = {pool.submit(fetch_one, i, r): i for i, r in enumerate(results)}
        for future in as_completed(futures):
            try:
                idx, enriched_item = future.result()
                enriched[idx] = enriched_item
            except Exception:
                idx = futures[future]
                enriched[idx] = {**results[idx], "content": results[idx]["snippet"]}

    return enriched


def search_duckduckgo(queries, depth="balanced"):
    results_limit = SEARCH_DEPTH.get(depth, 10)

    collected_results = []
    seen_links = set()

    with DDGS() as ddgs:
        for query in queries:
            results = ddgs.text(query, max_results=results_limit)
            for r in results:
                link = r.get("href")
                if link and link not in seen_links:
                    seen_links.add(link)
                    collected_results.append({
                        "title":   r.get("title"),
                        "link":    link,
                        "snippet": r.get("body"),
                    })

    logger.info(f"Fetching full article content for {len(collected_results)} results...")
    enriched = _enrich_with_content(collected_results)
    fetched = sum(1 for r in enriched if r.get("content") != r.get("snippet"))
    logger.info(f"Content fetched: {fetched}/{len(enriched)} articles")

    return enriched