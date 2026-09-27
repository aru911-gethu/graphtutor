from crewai.tools import tool
import httpx
from bs4 import BeautifulSoup


@tool("web_scraper")
def web_scraper(url: str) -> str:
    """
    Fetch a web page URL and extract its main readable text content.
    Strips scripts, styles, navigation bars, and boilerplate.
    """
    try:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        with httpx.Client(timeout=10.0, follow_redirects=True) as client:
            resp = client.get(url, headers=headers)
            if resp.status_code != 200:
                return f"Failed to fetch {url}: HTTP status {resp.status_code}"

            soup = BeautifulSoup(resp.text, "html.parser")
            for tag in soup(["script", "style", "nav", "footer", "header", "noscript", "aside"]):
                tag.decompose()

            article = soup.find("article") or soup.find("main") or soup.body
            if article:
                text = article.get_text(separator="\n", strip=True)
            else:
                text = soup.get_text(separator="\n", strip=True)

            lines = [line.strip() for line in text.splitlines() if line.strip()]
            cleaned_text = "\n".join(lines[:60])
            return f"Content extracted from {url}:\n\n{cleaned_text[:3000]}"
    except Exception as e:
        return f"Error scraping {url}: {str(e)}"
