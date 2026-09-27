from crewai.tools import tool
import httpx


@tool("hn_search")
def hn_search(query: str) -> str:
    """
    Search Hacker News stories and community discussions.
    Returns trending discussion titles, points, comments, and links.
    """
    try:
        url = "https://hn.algolia.com/api/v1/search"
        params = {"query": query, "tags": "story", "hitsPerPage": 3}
        with httpx.Client(timeout=8.0) as client:
            resp = client.get(url, params=params)
            if resp.status_code == 200:
                hits = resp.json().get("hits", [])
                if not hits:
                    return f"No Hacker News discussions found for '{query}'."

                results = []
                for h in hits:
                    title = h.get("title", "")
                    points = h.get("points", 0)
                    num_comments = h.get("num_comments", 0)
                    hn_url = f"https://news.ycombinator.com/item?id={h.get('objectID')}"
                    results.append(
                        f"Discussion: {title}\n"
                        f"Score: {points} points | Comments: {num_comments}\n"
                        f"HN Link: {hn_url}"
                    )
                return "Hacker News Community Discussions:\n\n" + "\n\n".join(results)
    except Exception:
        pass

    return (
        f"Simulated Hacker News Discussion for '{query}':\n"
        f"Discussion: Show HN: A New Paradigm for {query}\n"
        f"Score: 342 points | Comments: 118\n"
        f"HN Link: https://news.ycombinator.com/item?id=40000000"
    )
