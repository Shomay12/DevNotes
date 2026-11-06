"""
DevNote DevSearch — General Web & Knowledge Search Provider.
Processes raw text queries and returns rich informational snippets, definitions,
and technical discussions without requiring third-party API keys or dumping dummy Google URLs.
"""

import html
import re
from typing import List, Dict, Any, Optional
import httpx
from devnote.app.schemas.search import SearchResultItem
from devnote.app.search.base_provider import BaseSearchProvider
from devnote.app.search.providers.searxng_provider import SearXNGProvider
from devnote.app.search.providers.wikipedia_provider import WikipediaProvider
from devnote.app.search.providers.hackernews_provider import HackerNewsProvider

CURATED_GENERAL_KNOWLEDGE: List[Dict[str, Any]] = [
    {
        "id": "gen-numpy-array",
        "title": "NumPy Multidimensional Array Computing in Python",
        "category": "general",
        "snippet": "NumPy provides high-performance N-dimensional array objects (ndarray) and tools for working with these arrays. It is the fundamental package for scientific computing with Python, offering linear algebra, Fourier transforms, and random number generation capabilities.",
        "code": "import numpy as np\n# Create a 2D array\narr = np.array([[1, 2, 3], [4, 5, 6]])\nprint('Shape:', arr.shape)\nprint('Sum by column:', np.sum(arr, axis=0))",
        "language": "python",
        "source": "Scientific Computing Guide",
        "url": "https://numpy.org/doc/stable/user/whatisnumpy.html",
        "tags": ["numpy", "python", "arrays", "data-science"]
    },
    {
        "id": "gen-python-print-array",
        "title": "Python: How to Print Full Array Without Truncation",
        "category": "general",
        "snippet": "By default, NumPy truncates large arrays with ellipsis (...) when printing. To display all elements completely without truncation, configure the threshold parameter using numpy.set_printoptions(threshold=sys.maxsize).",
        "code": "import sys\nimport numpy as np\nnp.set_printoptions(threshold=sys.maxsize)\narr = np.arange(500)\nprint(arr) # Prints all 500 items",
        "language": "python",
        "source": "Python Developer Guide",
        "url": "https://docs.python.org/3/library/sys.html#sys.maxsize",
        "tags": ["python", "numpy", "formatting", "arrays"]
    },
    {
        "id": "gen-fastapi-quickstart",
        "title": "FastAPI Modern Asynchronous Web Framework",
        "category": "general",
        "snippet": "FastAPI is a modern, fast web framework for building APIs with Python 3.8+ based on standard Python type hints. It provides automatic OpenAPI interactive docs, data validation via Pydantic, and native async/await performance.",
        "code": "from fastapi import FastAPI\napp = FastAPI()\n\n@app.get('/')\ndef read_root():\n    return {'status': 'healthy'}",
        "language": "python",
        "source": "FastAPI Guide",
        "url": "https://fastapi.tiangolo.com",
        "tags": ["fastapi", "python", "api", "async"]
    },
    {
        "id": "gen-docker-containers",
        "title": "Docker Containers & Microservices Architecture",
        "category": "general",
        "snippet": "Containers package application code, system libraries, and dependencies together into an isolated runtime unit. This guarantees reproducible execution across developer laptops, CI/CD pipelines, and cloud environments.",
        "code": "docker build -t my-app:latest .\ndocker run -d -p 8000:8000 my-app:latest",
        "language": "bash",
        "source": "DevOps Handbook",
        "url": "https://docs.docker.com/get-started/",
        "tags": ["docker", "containers", "devops"]
    },
    {
        "id": "gen-git-workflow",
        "title": "Git Distributed Version Control & Branching Workflows",
        "category": "general",
        "snippet": "Git is an open source distributed version control system designed to handle everything from small to very large projects with speed and efficiency. Key workflows include trunk-based development and feature branches.",
        "code": "git checkout -b feature/search-engine\ngit add .\ngit commit -m 'feat: improve search'\ngit push origin feature/search-engine",
        "language": "bash",
        "source": "Git Documentation",
        "url": "https://git-scm.com/doc",
        "tags": ["git", "vcs", "collaboration"]
    }
]


class GeneralSearchProvider(BaseSearchProvider):
    id = "general"
    name = "General Web & Knowledge"
    description = "Searches general web articles, technical concepts, encyclopedia resources, and discussions directly from raw text"
    category = "general"
    is_online = True
    requires_api_key = False

    def __init__(self):
        self.searxng = SearXNGProvider()
        self.wiki = WikipediaProvider()
        self.hn = HackerNewsProvider()

    async def search(self, query: str, filters: Optional[Dict[str, Any]] = None) -> List[SearchResultItem]:
        q = query.strip()
        if not q:
            return [SearchResultItem(**item) for item in CURATED_GENERAL_KNOWLEDGE]

        results: List[SearchResultItem] = []

        # 1. First, check if SearXNG is running and returns results
        try:
            searx_items = await self.searxng.search(q, filters)
            if searx_items:
                results.extend(searx_items)
        except Exception:
            pass

        # 2. Query Wikipedia for authoritative encyclopedic definitions
        try:
            wiki_items = await self.wiki.search(q, filters)
            if wiki_items:
                results.extend(wiki_items[:4])
        except Exception:
            pass

        # 3. Query Hacker News for technology discussions and news
        try:
            hn_items = await self.hn.search(q, filters)
            if hn_items:
                results.extend(hn_items[:3])
        except Exception:
            pass

        # 4. Fallback: match curated knowledge base
        q_lower = q.lower()
        for item in CURATED_GENERAL_KNOWLEDGE:
            text = f"{item['title']} {item['snippet']} {' '.join(item.get('tags', []))}".lower()
            if any(term in text for term in q_lower.split()):
                # Avoid duplicate title
                if not any(r.title == item["title"] for r in results):
                    results.append(SearchResultItem(**item))

        # 5. If still no results, generate structured informative concept card
        if not results:
            clean_q = html.escape(q)
            results.append(SearchResultItem(
                id=f"gen-concept-{q.replace(' ', '-').lower()[:20]}",
                title=f"Technical Overview: {q.capitalize()}",
                category="general",
                snippet=f"Information and programming resources for '{q}'. You can read detailed documentation, search related repositories on GitHub, or capture evidence and study notes directly into DevNote.",
                source="DevNote Knowledge Base",
                url=f"https://en.wikipedia.org/wiki/{q.replace(' ', '_')}",
                tags=[t.lower() for t in q.split()[:4]] + ["general", "concept"]
            ))

        return results
