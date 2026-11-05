import os
import httpx
from typing import List, Dict, Any, Optional
from devnote.app.schemas.search import SearchResultItem
from devnote.app.search.base_provider import BaseSearchProvider

class GoogleProvider(BaseSearchProvider):
    id = "google"
    name = "Google Search"
    description = "Searches technical articles, tutorials, and developer discussions via Google Custom Search API"
    category = "web"
    is_online = True
    requires_api_key = True

    def __init__(self):
        self.api_key = os.environ.get("GOOGLE_API_KEY", "").strip()
        self.cse_id = os.environ.get("GOOGLE_CSE_ID", "").strip()

    async def is_available(self) -> bool:
        return bool(self.api_key and self.cse_id)

    async def search(self, query: str, filters: Optional[Dict[str, Any]] = None) -> List[SearchResultItem]:
        q = query.strip()
        if not q:
            return []

        # Check credentials
        api_key = self.api_key or os.environ.get("GOOGLE_API_KEY", "").strip()
        cse_id = self.cse_id or os.environ.get("GOOGLE_CSE_ID", "").strip()

        if not api_key or not cse_id:
            # As per Section 2.A: Do NOT scrape Google result pages.
            # Return helpful developer web search citation so user knows how to enable or can click to open in browser
            return [
                SearchResultItem(
                    id=f"google-web-{q.replace(' ', '-')[:20]}",
                    title=f"Google Search: {q}",
                    category="web",
                    snippet=f"Search Google for '{q}' programming concepts, tutorials, and discussions. (To enable inline Google API results, configure GOOGLE_API_KEY and GOOGLE_CSE_ID in DevSearch Settings).",
                    source="Google",
                    url=f"https://www.google.com/search?q={q.replace(' ', '+')}",
                    tags=["google", "web", "search"]
                )
            ]

        results: List[SearchResultItem] = []
        try:
            params = {
                "key": api_key,
                "cx": cse_id,
                "q": q,
                "num": 8
            }
            async with httpx.AsyncClient(timeout=4.0) as client:
                res = await client.get("https://www.googleapis.com/customsearch/v1", params=params)
                if res.status_code == 200:
                    data = res.json()
                    items = data.get("items", [])
                    for idx, item in enumerate(items):
                        results.append(SearchResultItem(
                            id=f"google-{idx}-{item.get('cacheId', '')}",
                            title=item.get("title", ""),
                            category="web",
                            snippet=item.get("snippet", ""),
                            source=item.get("displayLink", "Google Search"),
                            url=item.get("link", "")
                        ))
        except Exception:
            pass

        return results
