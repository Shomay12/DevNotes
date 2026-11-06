"""
DevNote DevSearch — Wikipedia Search Provider.
Provides authoritative encyclopedia summaries, algorithmic foundations,
and computer science references directly from Wikipedia.
"""

import html
import re
from typing import List, Dict, Any, Optional
import httpx
from devnote.app.schemas.search import SearchResultItem
from devnote.app.search.base_provider import BaseSearchProvider

CURATED_WIKI_TOPICS: List[Dict[str, Any]] = [
    {
        "id": "wiki-numpy",
        "title": "NumPy",
        "category": "wikipedia",
        "snippet": "NumPy is a library for the Python programming language, adding support for large, multi-dimensional arrays and matrices, along with a large collection of high-level mathematical functions.",
        "source": "Wikipedia",
        "url": "https://en.wikipedia.org/wiki/NumPy",
        "tags": ["python", "arrays", "data-science", "math", "matrices"]
    },
    {
        "id": "wiki-python",
        "title": "Python (programming language)",
        "category": "wikipedia",
        "snippet": "Python is a high-level, general-purpose programming language. Its design philosophy emphasizes code readability with the use of significant indentation.",
        "source": "Wikipedia",
        "url": "https://en.wikipedia.org/wiki/Python_(programming_language)",
        "tags": ["python", "language", "programming"]
    },
    {
        "id": "wiki-fft",
        "title": "Fast Fourier Transform",
        "category": "wikipedia",
        "snippet": "A fast Fourier transform (FFT) is an algorithm that computes the discrete Fourier transform (DFT) of a sequence, or its inverse, reducing time complexity from O(N²) to O(N log N).",
        "source": "Wikipedia",
        "url": "https://en.wikipedia.org/wiki/Fast_Fourier_transform",
        "tags": ["algorithms", "math", "signal-processing", "fft"]
    },
    {
        "id": "wiki-docker",
        "title": "Docker (software)",
        "category": "wikipedia",
        "snippet": "Docker is a set of platform as a service (PaaS) products that use OS-level virtualization to deliver software in packages called containers.",
        "source": "Wikipedia",
        "url": "https://en.wikipedia.org/wiki/Docker_(software)",
        "tags": ["devops", "containers", "linux", "virtualization"]
    },
    {
        "id": "wiki-bst",
        "title": "Binary Search Tree",
        "category": "wikipedia",
        "snippet": "A binary search tree (BST) is a rooted binary tree data structure with the key of each internal node greater than all keys in the left subtree and less than those in the right.",
        "source": "Wikipedia",
        "url": "https://en.wikipedia.org/wiki/Binary_search_tree",
        "tags": ["data-structures", "trees", "algorithms", "search"]
    },
    {
        "id": "wiki-rest",
        "title": "REST (Representational State Transfer)",
        "category": "wikipedia",
        "snippet": "Representational state transfer (REST) is a software architectural style that defines a set of constraints to be used for creating Web services.",
        "source": "Wikipedia",
        "url": "https://en.wikipedia.org/wiki/REST",
        "tags": ["api", "web", "http", "architecture"]
    },
    {
        "id": "wiki-git",
        "title": "Git",
        "category": "wikipedia",
        "snippet": "Git is a distributed version control system designed to track changes in any set of computer files, usually used for coordinating work among programmers.",
        "source": "Wikipedia",
        "url": "https://en.wikipedia.org/wiki/Git",
        "tags": ["vcs", "version-control", "git", "collaboration"]
    }
]


class WikipediaProvider(BaseSearchProvider):
    id = "wikipedia"
    name = "Wikipedia Reference"
    description = "Searches Wikipedia encyclopedia references, computer science concepts, and mathematical foundations"
    category = "wikipedia"
    is_online = True
    requires_api_key = False

    async def search(self, query: str, filters: Optional[Dict[str, Any]] = None) -> List[SearchResultItem]:
        q = query.strip()
        if not q:
            return [SearchResultItem(**item) for item in CURATED_WIKI_TOPICS[:5]]

        results: List[SearchResultItem] = []

        # 1. Search online OpenSearch API
        try:
            params = {
                "action": "opensearch",
                "search": q,
                "limit": 6,
                "namespace": 0,
                "format": "json"
            }
            headers = {"User-Agent": "DevNote-DevSearch/1.1 (Developer Technical Notebook)"}

            async with httpx.AsyncClient(timeout=4.0) as client:
                res = await client.get("https://en.wikipedia.org/w/api.php", params=params, headers=headers)
                if res.status_code == 200:
                    data = res.json()
                    # OpenSearch format: [query, [titles], [descriptions], [urls]]
                    if len(data) >= 4:
                        titles = data[1]
                        descriptions = data[2]
                        urls = data[3]
                        for idx, (t, d, u) in enumerate(zip(titles, descriptions, urls)):
                            if not t:
                                continue
                            snippet = d or f"Wikipedia encyclopedia article covering {t}."
                            results.append(SearchResultItem(
                                id=f"wiki-{t.replace(' ', '-').lower()}",
                                title=t,
                                category="wikipedia",
                                snippet=snippet,
                                source="Wikipedia",
                                url=u,
                                tags=["wikipedia", "reference", "encyclopedia"]
                            ))
        except Exception:
            pass

        # 2. Check curated offline database if online returned no results
        if not results:
            q_lower = q.lower()
            for item in CURATED_WIKI_TOPICS:
                match_text = f"{item['title']} {item['snippet']} {' '.join(item.get('tags', []))}".lower()
                if any(term in match_text for term in q_lower.split()):
                    results.append(SearchResultItem(**item))

        return results
