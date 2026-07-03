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


QUERY_INSTRUCTIONS = {
    "Engineering": """
Generate {n} search queries to deeply research the following engineering idea.

Focus ONLY on:
- The underlying physics, thermodynamics, fluid dynamics, or materials science
- Prior art: existing systems, patents, or prototypes that attempted something similar
- Real-world implementations or experiments (what has actually been built or tested)
- Technical failure modes or constraints (what makes this hard)
- Relevant academic papers, standards, or engineering analyses
- ONE query MUST target the governing equation directly: include the formula name, the key variables, and "equation" or "formula" or "derivation" — e.g., "laser beam intensity formula divergence angle calculation watts per cm2" or "Carnot efficiency formula hot cold reservoir equation derivation"

DO NOT generate market size, competitor, India, or business queries.
Queries must be specific and technical — think like an engineer searching for prior art, not a consultant sizing a market.
Bad example: "market for pressure-based rocket separation"
Good example: "pneumatic stage separation rocket cold gas pressure mechanism"
""",

    "Science": """
Generate {n} search queries to deeply research the following scientific idea or hypothesis.

Structure your queries to cover ALL of these angles:
- The KEY EXPERIMENT or measurement: search for the specific named study, paper, or research group that produced the most important quantitative result related to this hypothesis (author + topic + measurement type)
- The QUANTITATIVE RESULT: search for the actual measured values — effect sizes, rates, concentrations, lifetimes, detection thresholds — not just whether something was studied
- What is ALREADY PROVEN vs what is STILL OPEN: prior art, replication attempts, contradicting studies
- The COMPETING THEORY or mechanism: what is the established scientific consensus, and what evidence supports it
- The BLOCKING CONSTRAINT: what specific instrument sensitivity, sample size, or technical barrier prevents this from being tested more directly
- ONE query MUST target the governing equation or physical law directly: include the formula name, the key constants or variables, and "equation" or "formula" or "derivation" — e.g., "thermal decoherence time equation Planck constant Boltzmann temperature formula" or "magnetoreception torque equation magnetite crystal magnetic moment formula"

DO NOT generate market, business, or India queries.
Queries must be precise enough to return primary research papers, not news articles or Wikipedia summaries.
BAD: "quantum effects in photosynthesis" — too broad, returns news articles
GOOD: "Fleming FMO complex quantum coherence femtoseconds 2007 site:nature.com OR site:science.org"
BAD: "magnetoreception humans research"
GOOD: "Caltech human magnetoreception alpha wave EEG 2019 Kirschvink"
""",

    "Mathematics": """
Generate {n} search queries to deeply research the following mathematical idea or conjecture.

Focus ONLY on:
- Related theorems, proofs, or conjectures already in the literature
- Mathematicians or research groups working on adjacent problems
- Computational or algorithmic approaches to exploring this
- Historical context of the problem
- Relevant fields of mathematics (number theory, topology, combinatorics, etc.)

DO NOT generate market, business, or India queries.
""",

    "Philosophy": """
Generate {n} search queries to research the following philosophical idea using academic sources.

Structure your queries to cover ALL of these angles:
- ONE query targeting the Stanford Encyclopedia of Philosophy (SEP) entry most relevant to this idea — e.g., "site:plato.stanford.edu discipline virtue ethics" or "site:plato.stanford.edu obsession motivation philosophy"
- ONE query targeting named philosophers or classic arguments in this domain — include philosopher name + concept + "argument" or "paper" — e.g., "Aristotle eudaimonia discipline habituation virtue ethics"
- ONE query targeting PhilPapers or JSTOR for academic papers — e.g., "obsession compulsion agency autonomy philosophy paper philpapers"
- ONE query targeting counterarguments or the strongest objection in the literature — e.g., "critique of willpower discipline philosophy self-control failure counterargument"
- ONE query for Indian philosophical tradition relevance — e.g., "Nyaya epistemology discipline motivation Indian philosophy" or "Advaita Vedanta self-control obsession consciousness"

DO NOT generate market, business, or self-help blog queries. Queries must return academic philosophy sources, not motivational content.
BAD: "obsession vs discipline motivation productivity" — returns self-help blogs
GOOD: "Frankfurt caring obsession agency philosophy paper" — returns academic philosophy
BAD: "why discipline is important success" — returns lifestyle content
GOOD: "site:plato.stanford.edu self-control akrasia weakness of will" — returns SEP
""",

    "Personal": """
Generate {n} search queries to research the following personal development or behavioural idea using scientific sources.

Structure your queries to cover ALL of these angles:
- ONE query targeting the specific psychological mechanism by name — e.g., "implementation intention Gollwitzer habit formation RCT" or "identity-based habits Duhigg cue routine reward neuroscience"
- ONE query targeting the key researcher or lab — e.g., "BJ Fogg Tiny Habits Stanford behavior design study" or "Wendy Wood habit automaticity dual-process"
- ONE query for the best RCT or empirical study on this specific behaviour — e.g., "walking fat loss RCT heart rate zone comparison calories 2022"
- ONE query targeting failure modes or contradicting evidence — e.g., "habit formation failure relapse rate willpower depletion ego depletion critique"
- ONE query for India-specific context — e.g., "exercise habit adherence India urban study" or "sleep deprivation India working hours survey NSSO"

DO NOT generate business, market, or generic motivational queries. Queries must return scientific papers, not self-help articles.
BAD: "how to build discipline habits" — returns self-help blogs
GOOD: "Phillippa Lally habit formation 18 days 254 days UCL study 2010" — returns the actual research
BAD: "walking vs running weight loss tips"
GOOD: "low intensity exercise fat oxidation zone 2 training RCT heart rate comparison"
""",

    "Business": """
Generate {n} search queries to research the following business idea.

Structure your queries to cover ALL of these angles:
- {n_global} queries covering:
  - Global market size with a specific data source (name the category, segment, and year)
  - Existing players and their exact business model — how do they price, who pays, what's the margin?
  - ONE query targeting unit economics benchmarks: "CAC LTV gross margin [business type]" or "[business type] unit economics payback period"
- {n_india} queries covering:
  - Indian competitors or alternatives — name them specifically, not generically
  - India-specific regulatory or operational constraint (GST, RBI, FSSAI, MSME Act, pricing ceiling)
  - Adoption evidence: has any similar business succeeded or failed in India? Name it.

Queries must be specific — name the domain, product type, customer segment, and geography.
BAD: "innovative business idea market"
GOOD: "B2B SaaS GST reconciliation tool India CA firm pricing 2024"
BAD: "food delivery India"
GOOD: "meal kit delivery India urban household CAC retention subscription economics"
""",

    "Technology": """
Generate {n} search queries to research the following technology idea.

Structure your queries to cover ALL of these angles:
- {n_global} queries covering:
  - Existing tools or platforms doing exactly this — name the specific product category and approach
  - Technical architecture: what APIs, models, or infrastructure does this require? What are the hard parts?
  - Open source alternatives or related projects with adoption or GitHub star data
  - ONE query targeting pricing and unit economics: "[product type] pricing model revenue per user SaaS" or "monetization strategy [product category] developer tool"
- {n_india} queries covering:
  - Indian startups or apps in this exact space — name the product or founder if known
  - India-specific constraint: mobile-first, pricing ceiling (₹499–999/month), latency, language localization, or regulatory requirement
  - How did similar tools get traction in India?

Queries must be specific and technical — name the exact use case and user persona.
BAD: "AI productivity tool market"
GOOD: "LLM-powered async code review GitHub PR latency benchmark 2024"
BAD: "screen monitoring app India"
GOOD: "real-time developer screen activity monitoring pricing model India startup 2024"
""",

    "Society": """
Generate {n} search queries to research the following social or cultural observation using academic sources.

Structure your queries to cover ALL of these angles:
- {n_global} queries covering:
  - ONE query for the closest academic study — name the phenomenon + researcher or journal — e.g., "Putnam social capital bowling alone study 1995" or "norm diffusion social network analysis paper"
  - ONE query for quantitative data — name the specific dataset or survey — e.g., "IHDS caste mobility income panel data India" or "NFHS-5 gender education attainment district level"
  - ONE query for the strongest confound or alternative explanation — e.g., "selection bias social mobility India critique reverse causality"
- {n_india} queries covering:
  - Named India-specific study, NSSO/NFHS/IHDS/CMIE dataset relevant to this hypothesis
  - India institutional context — CSDS, NCAER, ICSSR — e.g., "CSDS National Election Study India social trust 2019"
  - ONE query for a natural experiment or policy change in India relevant to this — e.g., "Mandal Commission caste reservation India social mobility before after study"

DO NOT generate self-help, news, or generic social commentary queries. Queries must return academic sociology, economics, or anthropology papers.
BAD: "why India has poor social mobility" — returns news opinion
GOOD: "intergenerational income mobility India IHDS panel caste Emran Shilpi 2015" — returns research paper
""",

    "Other": """
Generate {n} search queries to research the following idea, focusing on what already exists and what would need to be true for it to work.

Structure your queries to cover:
- ONE query for the closest named real-world project or implementation — include project name + outcome — e.g., "Sidewalk Toronto smart city experiment outcome lessons" or "Brazil participatory budgeting Porto Alegre results"
- ONE query for the critical technical or operational dependency — e.g., "last-mile cold chain India rural village feasibility cost" or "quadratic voting implementation blockchain cost per vote"
- ONE query for academic or policy research on this domain — include institution or journal — e.g., "MIT Media Lab urban sensing deployment study" or "World Bank community governance India panchayat effectiveness"
- ONE query targeting failure modes or why similar ideas failed — e.g., "smart city India failure reasons Dholera SIR lessons"
- ONE query for India-specific actor or programme — e.g., "NITI Aayog urban mobility pilot India smart infrastructure"

DO NOT generate generic "market analysis" queries. Each query must be specific enough to return a named project, paper, or report.
BAD: "innovative urban infrastructure ideas" — too vague
GOOD: "Medellín cable car urban mobility low-income area social impact study" — returns specific project analysis
""",
}


def _strip_site_restrictions(queries: list[str]) -> list[str]:
    """Remove site: directives from queries for fallback search when original queries return 0 results."""
    import re
    simplified = []
    for q in queries:
        q = re.sub(r'\s+OR\s+site:\S+', '', q)
        q = re.sub(r'\s+site:\S+', '', q)
        simplified.append(q.strip())
    return simplified


def generate_search_queries(idea, llm_client, category=None):
    n = DEFAULT_QUERY_COUNT
    n_india = max(1, n // 3)
    n_global = n - n_india

    template = QUERY_INSTRUCTIONS.get(category, QUERY_INSTRUCTIONS["Other"])
    instructions = template.format(n=n, n_global=n_global, n_india=n_india)

    prompt = f"""You are a research specialist. Your job is to generate the best possible search queries to find information about the idea below.

{instructions}

Return ONLY a JSON array of exactly {n} strings. No explanation, no markdown. Output goes directly to json.loads().

Idea:
{idea}
"""

    response = llm_client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
        response_format={"type": "json_object"}
    )

    import json
    raw = response.choices[0].message.content
    parsed = json.loads(raw)
    # model returns {"queries": [...]} or just an array — normalise
    if isinstance(parsed, list):
        return parsed
    for v in parsed.values():
        if isinstance(v, list):
            return v
    return list(parsed.values())


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