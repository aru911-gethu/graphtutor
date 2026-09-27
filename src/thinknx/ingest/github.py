import re
from typing import Dict, Any, Optional
import httpx
import structlog
from thinknx.ingest.text import TextIngestor

logger = structlog.get_logger(__name__)


class GitHubIngestor:
    """Analyzes GitHub repositories by inspecting README and repository metadata."""

    def __init__(self, text_ingestor: Optional[TextIngestor] = None):
        self.text_ingestor = text_ingestor or TextIngestor()

    async def ingest_repo(self, repo_url: str) -> Dict[str, Any]:
        """Fetch README and repo description from GitHub URL and extract concepts."""
        # Extract owner and repo from URL
        match = re.search(r"github\.com/([^/]+)/([^/]+)", repo_url)
        if not match:
            return {"error": "Invalid GitHub URL format", "concepts": []}

        owner, repo = match.group(1), match.group(2).rstrip(".git")
        readme_content = ""
        description = ""

        try:
            api_url = f"https://api.github.com/repos/{owner}/{repo}"
            headers = {"User-Agent": "thinknx-learning-agent"}

            async with httpx.AsyncClient(timeout=10.0) as client:
                res = await client.get(api_url, headers=headers)
                if res.status_code == 200:
                    description = res.json().get("description", "")

                # Fetch raw README
                raw_readme_url = f"https://raw.githubusercontent.com/{owner}/{repo}/main/README.md"
                readme_res = await client.get(raw_readme_url, headers=headers)
                if readme_res.status_code != 200:
                    raw_readme_url = f"https://raw.githubusercontent.com/{owner}/{repo}/master/README.md"
                    readme_res = await client.get(raw_readme_url, headers=headers)

                if readme_res.status_code == 200:
                    readme_content = readme_res.text[:4000]
        except Exception as e:
            logger.warning("Error fetching GitHub repo", error=str(e), repo=repo_url)

        combined_text = f"Repository: {owner}/{repo}\nDescription: {description}\n\n{readme_content}"
        concepts = await self.text_ingestor.extract_concepts(combined_text)

        return {
            "repo": f"{owner}/{repo}",
            "description": description,
            "concepts": concepts,
        }
