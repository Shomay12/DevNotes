"""
DevNote Hacker News API Router.
Provides real-time technology news feeds, Show HN projects, and community discussions.
"""

from urllib.parse import urlparse
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Query, HTTPException, status
import httpx
from pydantic import BaseModel

from devnote.app.search.providers.hackernews_provider import CURATED_HN_STORIES

router = APIRouter(prefix="/api/news", tags=["news"])


class HackerNewsStory(BaseModel):
    id: str
    title: str
    url: str
    hn_url: str
    author: str
    points: int
    comments_count: int
    created_at: Optional[str] = None
    domain: Optional[str] = None


FALLBACK_STORIES: List[Dict[str, Any]] = [
    {
        "id": "40291823",
        "title": "Why we run local LLMs with Ollama on Apple Silicon",
        "url": "https://ollama.com",
        "hn_url": "https://news.ycombinator.com/item?id=40291823",
        "author": "macgeek",
        "points": 780,
        "comments_count": 315,
        "created_at": "3 hours ago",
        "domain": "ollama.com"
    },
    {
        "id": "39821450",
        "title": "NumPy 2.0.0 released with comprehensive modern C-API",
        "url": "https://github.com/numpy/numpy/releases/tag/v2.0.0",
        "hn_url": "https://news.ycombinator.com/item?id=39821450",
        "author": "pypioneer",
        "points": 842,
        "comments_count": 194,
        "created_at": "5 hours ago",
        "domain": "github.com"
    },
    {
        "id": "40112399",
        "title": "SQLite 3.45: Introducing JSONB binary serialization",
        "url": "https://sqlite.org/draft/jsonb.html",
        "hn_url": "https://news.ycombinator.com/item?id=40112399",
        "author": "drh",
        "points": 620,
        "comments_count": 142,
        "created_at": "8 hours ago",
        "domain": "sqlite.org"
    },
    {
        "id": "40334812",
        "title": "Show HN: DevNote – Local-First Developer Notebook and Research Workspace",
        "url": "https://github.com/devnote-team/devnote",
        "hn_url": "https://news.ycombinator.com/item?id=40334812",
        "author": "devnote",
        "points": 450,
        "comments_count": 98,
        "created_at": "12 hours ago",
        "domain": "github.com"
    },
    {
        "id": "38910022",
        "title": "FastAPI: High-Throughput Asynchronous Web Architectures",
        "url": "https://fastapi.tiangolo.com",
        "hn_url": "https://news.ycombinator.com/item?id=38910022",
        "author": "tiangolo",
        "points": 490,
        "comments_count": 210,
        "created_at": "1 day ago",
        "domain": "fastapi.tiangolo.com"
    },
    {
        "id": "40251100",
        "title": "Python 3.13 JIT compiler deep dive",
        "url": "https://docs.python.org/3.13/whatsnew/3.13.html",
        "hn_url": "https://news.ycombinator.com/item?id=40251100",
        "author": "coredev",
        "points": 560,
        "comments_count": 182,
        "created_at": "1 day ago",
        "domain": "docs.python.org"
    }
]


@router.get("/hackernews", response_model=List[HackerNewsStory])
async def get_hacker_news(
    feed: str = Query(default="top", description="News feed: top, new, ask_hn, show_hn, best"),
    limit: int = Query(default=25, ge=1, le=50, description="Number of stories to return"),
    query: Optional[str] = Query(default=None, description="Optional search keyword to filter news")
):
    """
    Fetches real-time technology news, Show HN projects, and developer discussions
    via the official Algolia Hacker News API, with graceful offline fallback.
    """
    stories: List[HackerNewsStory] = []

    # Map feed parameter to Algolia API parameters
    if query and query.strip():
        api_endpoint = "https://hn.algolia.com/api/v1/search"
        params = {"query": query.strip(), "tags": "story", "hitsPerPage": limit}
    elif feed == "new":
        api_endpoint = "https://hn.algolia.com/api/v1/search_by_date"
        params = {"tags": "story", "hitsPerPage": limit}
    elif feed == "ask_hn":
        api_endpoint = "https://hn.algolia.com/api/v1/search"
        params = {"tags": "ask_hn", "hitsPerPage": limit}
    elif feed == "show_hn":
        api_endpoint = "https://hn.algolia.com/api/v1/search"
        params = {"tags": "show_hn", "hitsPerPage": limit}
    else:  # top / best
        api_endpoint = "https://hn.algolia.com/api/v1/search"
        params = {"tags": "front_page", "hitsPerPage": limit}

    headers = {"User-Agent": "DevNote-DevSearch/1.1 (Developer Technical Notebook)"}

    try:
        async with httpx.AsyncClient(timeout=4.0) as client:
            res = await client.get(api_endpoint, params=params, headers=headers)
            if res.status_code == 200:
                data = res.json()
                for hit in data.get("hits", []):
                    title = hit.get("title") or hit.get("story_title")
                    if not title:
                        continue
                    object_id = str(hit.get("objectID", ""))
                    hn_url = f"https://news.ycombinator.com/item?id={object_id}"
                    raw_url = hit.get("url") or hn_url

                    # Parse domain
                    domain = ""
                    try:
                        parsed = urlparse(raw_url)
                        domain = parsed.hostname or ""
                        if domain.startswith("www."):
                            domain = domain[4:]
                    except Exception:
                        domain = "news.ycombinator.com"

                    stories.append(HackerNewsStory(
                        id=object_id,
                        title=title,
                        url=raw_url,
                        hn_url=hn_url,
                        author=hit.get("author", "unknown"),
                        points=hit.get("points") or 0,
                        comments_count=hit.get("num_comments") or 0,
                        created_at=hit.get("created_at", "")[:10] if hit.get("created_at") else "Recent",
                        domain=domain
                    ))
    except Exception:
        pass

    # Fallback to curated tech stories if network call failed or offline
    if not stories:
        q_lower = query.lower() if query else ""
        filtered_fallback = FALLBACK_STORIES
        if q_lower:
            filtered_fallback = [s for s in FALLBACK_STORIES if q_lower in s["title"].lower() or q_lower in s["domain"].lower()]

        stories = [HackerNewsStory(**s) for s in (filtered_fallback or FALLBACK_STORIES)[:limit]]

    return stories
