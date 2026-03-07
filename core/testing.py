from ddgs import DDGS

with DDGS() as ddgs:
    results = list(ddgs.text("AI startup ideas", max_results=5))
    print(results)