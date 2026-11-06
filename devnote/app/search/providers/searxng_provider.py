import os
import re
import time
import httpx
from typing import List, Dict, Any, Optional
from devnote.app.schemas.search import SearchResultItem
from devnote.app.search.base_provider import BaseSearchProvider

class SearXNGProvider(BaseSearchProvider):
    id = "searxng"
    name = "SearXNG Meta-Search"
    description = "Searches web, IT documentation, and scientific resources via configurable SearXNG instance"
    category = "general"
    is_online = True
    requires_api_key = False

    def __init__(self):
        self.endpoint = os.environ.get("SEARXNG_URL", "http://localhost:8080").strip().rstrip("/")
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._cache_ttl = 300  # 5 minutes in-memory caching

    async def is_available(self) -> bool:
        return bool(self.endpoint)

    def _get_from_cache(self, key: str) -> Optional[List[SearchResultItem]]:
        if key in self._cache:
            entry = self._cache[key]
            if time.time() - entry["timestamp"] < self._cache_ttl:
                return entry["results"]
            del self._cache[key]
        return None

    def _set_cache(self, key: str, results: List[SearchResultItem]):
        if len(self._cache) > 200:
            oldest_key = min(self._cache.keys(), key=lambda k: self._cache[k]["timestamp"])
            del self._cache[oldest_key]
        self._cache[key] = {
            "results": results,
            "timestamp": time.time()
        }

    async def search(self, query: str, filters: Optional[Dict[str, Any]] = None) -> List[SearchResultItem]:
        q = query.strip()
        if not q:
            return []

        endpoint = self.endpoint or os.environ.get("SEARXNG_URL", "http://localhost:8080").strip().rstrip("/")
        if not endpoint:
            return []

        # Category mapping supporting: general, it, science
        category_filter = (filters.get("category") or "all").lower() if filters else "all"

        if category_filter == "it" or category_filter in ("code", "error"):
            categories = "it"
        elif category_filter == "science":
            categories = "science"
        elif category_filter in ("general", "web"):
            categories = "general"
        elif category_filter == "doc":
            categories = "it,general"
        elif category_filter in ("all", "unified"):
            categories = "general,it,science"
        else:
            categories = category_filter

        cache_key = f"{q}:{categories}:{filters.get('language') if filters else ''}"
        cached = self._get_from_cache(cache_key)
        if cached is not None:
            return cached

        results: List[SearchResultItem] = []
        try:
            params = {
                "q": q,
                "format": "json",
                "categories": categories,
                "safesearch": 0,
                "pageno": 1,
            }
            if filters and filters.get("language"):
                params["language"] = filters["language"]

            async with httpx.AsyncClient(timeout=5.0) as client:
                res = await client.get(f"{endpoint}/search", params=params)
                if res.status_code == 200:
                    data = res.json()
                    items = data.get("results", [])
                    for idx, item in enumerate(items[:20]):
                        title = item.get("title", "")
                        url = item.get("url", "")
                        content = item.get("content", "") or item.get("snippet", "")
                        engine_name = item.get("engine", "")
                        engines = item.get("engines", [])

                        if engines:
                            source_label = f"SearXNG ({', '.join(engines)})"
                        elif engine_name:
                            source_label = f"SearXNG ({engine_name})"
                        else:
                            source_label = "SearXNG"

                        # Extract code if present in markdown code blocks
                        extracted_code = None
                        if "```" in content:
                            code_match = re.search(r"```(?:\w+)?\n?(.*?)```", content, re.DOTALL)
                            if code_match:
                                extracted_code = code_match.group(1).strip()

                        raw_cat = item.get("category", "general")
                        item_cat = "code" if raw_cat == "it" else "web" if raw_cat == "general" else raw_cat

                        score_val = None
                        try:
                            score_val = float(item.get("score")) if item.get("score") is not None else None
                        except (ValueError, TypeError):
                            pass

                        results.append(SearchResultItem(
                            id=f"searxng-{idx}-{abs(hash(url)) % 100000}",
                            title=title,
                            category=item_cat,
                            snippet=content,
                            code=extracted_code,
                            language=filters.get("language") if filters else None,
                            source=source_label,
                            url=url,
                            relevance_score=score_val,
                            tags=["searxng", engine_name] if engine_name else ["searxng"]
                        ))

            if results:
                self._set_cache(cache_key, results)

        except Exception:
            # Fallback handling: if query specifically targeted web/searxng and instance is unreachable,
            # provide a clear setup card guiding the user to start docker-compose or configure endpoint
            if category_filter in ("web", "general", "it", "science", "all") and not results:
                results.append(SearchResultItem(
                    id=f"searxng-unreachable-{abs(hash(q)) % 10000}",
                    title=f"SearXNG Search: {q}",
                    category="web",
                    snippet=(
                        f"Could not connect to SearXNG at '{endpoint}'. "
                        "To use self-hosted SearXNG locally, run 'docker compose up -d' in the project directory, "
                        "or configure your preferred instance URL in DevSearch Settings."
                    ),
                    source="SearXNG",
                    url=f"{endpoint}/search?q={q.replace(' ', '+')}&categories=general,it,science",
                    tags=["searxng", "setup", "offline"]
                ))

        return results
