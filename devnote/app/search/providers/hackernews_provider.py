"""
DevNote DevSearch — Hacker News Search Provider.
Provides technology news, developer discussions, and Show HN projects.
"""

import html
import re
from typing import List, Dict, Any, Optional
import httpx
from devnote.app.schemas.search import SearchResultItem
from devnote.app.search.base_provider import BaseSearchProvider

CURATED_HN_STORIES: List[Dict[str, Any]] = [
    {
        "id": "hn-39821450",
        "title": "NumPy 2.0.0 released",
        "category": "hackernews",
        "snippet": "NumPy 2.0.0 is the first major release since 2006. It features breaking ABI changes, performance enhancements, and standard type promotions.",
        "source": "Hacker News",
        "url": "https://github.com/numpy/numpy/releases/tag/v2.0.0",
        "score": 842,
        "tags": ["hackernews", "python", "numpy", "release"],
        "metadata": {"hn_url": "https://news.ycombinator.com/item?id=39821450", "comments_count": 194, "author": "pypioneer"}
    },
    {
        "id": "hn-40112399",
        "title": "SQLite 3.45: JSONB and performance optimizations",
        "category": "hackernews",
        "snippet": "SQLite introduces new JSONB binary serialization format for significantly faster JSON processing and reduced storage overhead.",
        "source": "Hacker News",
        "url": "https://sqlite.org/draft/jsonb.html",
        "score": 620,
        "tags": ["hackernews", "sqlite", "database", "json"],
        "metadata": {"hn_url": "https://news.ycombinator.com/item?id=40112399", "comments_count": 142, "author": "drh"}
    },
    {
        "id": "hn-38910022",
        "title": "FastAPI: The Modern Python Web Framework",
        "category": "hackernews",
        "snippet": "Discussion exploring high-throughput asynchronous architectures in FastAPI, Pydantic v2 validation speeds, and dependency injection.",
        "source": "Hacker News",
        "url": "https://fastapi.tiangolo.com",
        "score": 490,
        "tags": ["hackernews", "python", "fastapi", "web"],
        "metadata": {"hn_url": "https://news.ycombinator.com/item?id=38910022", "comments_count": 210, "author": "tiangolo"}
    },
    {
        "id": "hn-40291823",
        "title": "Why we run local LLMs with Ollama on Apple Silicon",
        "category": "hackernews",
        "snippet": "In-depth engineering benchmark on unified memory architecture, metal acceleration, and running 8B-70B models completely offline.",
        "source": "Hacker News",
        "url": "https://ollama.com",
        "score": 780,
        "tags": ["hackernews", "ai", "ollama", "hardware", "llm"],
        "metadata": {"hn_url": "https://news.ycombinator.com/item?id=40291823", "comments_count": 315, "author": "macgeek"}
    }
]


class HackerNewsProvider(BaseSearchProvider):
    id = "hackernews"
    name = "Hacker News"
    description = "Searches technology news, developer discussions, and startup engineering threads via Hacker News"
    category = "hackernews"
    is_online = True
    requires_api_key = False

    async def search(self, query: str, filters: Optional[Dict[str, Any]] = None) -> List[SearchResultItem]:
        q = query.strip()
        if not q:
            return [SearchResultItem(**item) for item in CURATED_HN_STORIES]

        results: List[SearchResultItem] = []

        # 1. Search official Algolia Hacker News API
        try:
            params = {
                "query": q,
                "tags": "story",
                "hitsPerPage": 8
            }
            headers = {"User-Agent": "DevNote-DevSearch/1.1"}
            async with httpx.AsyncClient(timeout=4.0) as client:
                res = await client.get("https://hn.algolia.com/api/v1/search", params=params, headers=headers)
                if res.status_code == 200:
                    data = res.json()
                    hits = data.get("hits", [])
                    for hit in hits:
                        title = hit.get("title") or hit.get("story_title") or ""
                        if not title:
                            continue
                        points = hit.get("points") or 0
                        num_comments = hit.get("num_comments") or 0
                        url = hit.get("url") or f"https://news.ycombinator.com/item?id={hit.get('objectID')}"
                        author = hit.get("author", "unknown")
                        object_id = hit.get("objectID", "")
                        hn_url = f"https://news.ycombinator.com/item?id={object_id}"

                        snippet = f"Hacker News submission by {author} with {points} points and {num_comments} comments."

                        results.append(SearchResultItem(
                            id=f"hn-{object_id}",
                            title=title,
                            category="hackernews",
                            snippet=snippet,
                            source="Hacker News",
                            url=url,
                            score=points,
                            tags=["hackernews", "news", "discussion"],
                            metadata={
                                "hn_url": hn_url,
                                "author": author,
                                "comments_count": num_comments,
                                "points": points
                            }
                        ))
        except Exception:
            pass

        # 2. Fallback to curated stories
        if not results:
            q_lower = q.lower()
            for item in CURATED_HN_STORIES:
                match_text = f"{item['title']} {item['snippet']} {' '.join(item.get('tags', []))}".lower()
                if any(term in match_text for term in q_lower.split()):
                    results.append(SearchResultItem(**item))

        return results
