from typing import Dict, Any, Optional
import httpx
from bs4 import BeautifulSoup
import structlog
from thinknx.ingest.text import TextIngestor

logger = structlog.get_logger(__name__)


class FeedIngestor:
    """Ingests RSS feeds, blog articles, and technical updates."""

    def __init__(self, text_ingestor: Optional[TextIngestor] = None):
        self.text_ingestor = text_ingestor or TextIngestor()

    async def fetch_and_extract(self, url: str) -> Dict[str, Any]:
        """Fetch RSS feed or blog page and extract concepts."""
        text_content = ""
        title = ""

        try:
            async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
                res = await client.get(url, headers={"User-Agent": "thinknx-agent/1.0"})
                if res.status_code == 200:
                    soup = BeautifulSoup(res.text, "html.parser")
                    title = soup.title.string if soup.title else url

                    # Remove non-content elements
                    for tag in soup(["script", "style", "nav", "footer", "header"]):
                        tag.decompose()

                    main_elem = soup.find("article") or soup.find("main") or soup.body
                    if main_elem:
                        text_content = main_elem.get_text(separator="\n", strip=True)[:4000]
        except Exception as e:
            logger.warning("Feed ingestion error", error=str(e), url=url)

        full_text = f"Title: {title}\n\n{text_content}"
        concepts = await self.text_ingestor.extract_concepts(full_text)

        return {
            "url": url,
            "title": title,
            "concepts": concepts,
        }
