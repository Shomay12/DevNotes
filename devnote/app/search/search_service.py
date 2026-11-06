import os
import asyncio
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from devnote.app.models.search_history import SearchHistory
from devnote.app.schemas.search import (
    SearchResultItem,
    SearchResponse,
    SearchQueryRequest,
    ProviderInfo
)
from devnote.app.search.base_provider import BaseSearchProvider
from devnote.app.search.cache import SearchCache
from devnote.app.search.query_classifier import QueryClassifier, QueryClassification
from devnote.app.search.ranking_engine import RankingEngine
from devnote.app.search.deduplication import ResultDeduplicator
from devnote.app.search.providers.devdocs_provider import DevDocsProvider
from devnote.app.search.providers.stackoverflow_provider import StackOverflowProvider
from devnote.app.search.providers.github_provider import GitHubProvider
from devnote.app.search.providers.google_provider import GoogleProvider
from devnote.app.search.providers.searxng_provider import SearXNGProvider
from devnote.app.search.providers.local_docs_provider import LocalDocsProvider
from devnote.app.search.providers.notebooks_provider import NotebooksSearchProvider
from devnote.app.search.providers.wikipedia_provider import WikipediaProvider
from devnote.app.search.providers.hackernews_provider import HackerNewsProvider
from devnote.app.search.providers.general_search_provider import GeneralSearchProvider

class UnifiedSearchService:
    def __init__(self):
        self.providers: Dict[str, BaseSearchProvider] = {
            "devdocs": DevDocsProvider(),
            "stackoverflow": StackOverflowProvider(),
            "github": GitHubProvider(),
            "google": GoogleProvider(),
            "searxng": SearXNGProvider(),
            "general": GeneralSearchProvider(),
            "wikipedia": WikipediaProvider(),
            "hackernews": HackerNewsProvider(),
            "local_docs": LocalDocsProvider(),
            "notebooks": NotebooksSearchProvider(),
        }
        self.cache = SearchCache(default_ttl_seconds=300, max_entries=500)

        # Seed local offline doc packs if DB is empty
        LocalDocsProvider.seed_bundled_indexes_if_needed()

    def get_providers_info(self) -> List[ProviderInfo]:
        infos = []
        for p_id, p in self.providers.items():
            infos.append(ProviderInfo(
                id=p.id,
                name=p.name,
                description=p.description,
                category=p.category,
                is_online=p.is_online,
                is_available=True,
                requires_api_key=p.requires_api_key,
                has_api_key=True if not p.requires_api_key else bool(getattr(p, "api_key", False))
            ))
        return infos

    async def search(
        self,
        request: SearchQueryRequest,
        db: Optional[Session] = None
    ) -> SearchResponse:
        q = request.query.strip()
        cat = (request.category or "all").lower()
        lang = request.language or ""
        fw = request.framework or ""
        prov = request.provider or ""

        # 1. Deterministic Query Classification
        classification = QueryClassifier.classify(q)

        # 2. Check Cache
        cache_key = SearchCache.make_key(q, cat, lang, fw, prov)
        cached_results = self.cache.get(cache_key)
        if cached_results:
            return SearchResponse(
                query=q,
                total_results=len(cached_results),
                results=cached_results,
                intent=classification.intent,
                detected_language=classification.language,
                detected_framework=classification.framework,
                active_providers=["cache"],
                cached=True
            )

        # 3. Determine target providers based on category & filters
        target_providers: List[BaseSearchProvider] = []
        if prov and prov in self.providers:
            target_providers = [self.providers[prov]]
        elif cat in ("web", "general", "it", "science"):
            # Comprehensive General Search: All sources appear together rather than just a specific one
            target_providers = [
                self.providers["general"],
                self.providers["devdocs"],
                self.providers["stackoverflow"],
                self.providers["github"],
                self.providers["wikipedia"],
                self.providers["local_docs"]
            ]
            if getattr(self.providers["searxng"], "endpoint", None):
                target_providers.insert(0, self.providers["searxng"])
        elif cat in ("wikipedia", "wiki"):
            target_providers = [self.providers["wikipedia"], self.providers["general"]]
        elif cat in ("hackernews", "news"):
            target_providers = [self.providers["hackernews"], self.providers["general"]]
        elif cat == "doc":
            target_providers = [self.providers["devdocs"], self.providers["local_docs"], self.providers["wikipedia"], self.providers["general"]]
        elif cat in ("stackoverflow", "error"):
            target_providers = [self.providers["stackoverflow"], self.providers["github"], self.providers["general"]]
        elif cat == "github":
            target_providers = [self.providers["github"], self.providers["general"]]
        elif cat == "code":
            target_providers = [self.providers["github"], self.providers["devdocs"], self.providers["notebooks"], self.providers["stackoverflow"]]
        elif cat == "offline":
            target_providers = [self.providers["local_docs"]]
        elif cat == "notebook":
            target_providers = [self.providers["notebooks"]]
        else:
            # "all": All results appear across general web, official docs, stackoverflow, github, wikipedia, local docs, and notebooks
            target_providers = [
                self.providers["general"],
                self.providers["devdocs"],
                self.providers["stackoverflow"],
                self.providers["github"],
                self.providers["wikipedia"],
                self.providers["local_docs"],
                self.providers["notebooks"]
            ]
            if getattr(self.providers["searxng"], "endpoint", None):
                target_providers.insert(0, self.providers["searxng"])

        # 4. Asynchronously query targeted providers in parallel
        filters = {
            "category": cat,
            "language": lang or classification.language,
            "framework": fw or classification.framework
        }

        tasks = [p.search(q, filters) for p in target_providers]
        raw_responses = await asyncio.gather(*tasks, return_exceptions=True)

        all_items: List[SearchResultItem] = []
        active_provider_names = []

        for p, resp in zip(target_providers, raw_responses):
            if isinstance(resp, list):
                all_items.extend(resp)
                active_provider_names.append(p.name)
            elif isinstance(resp, Exception):
                # Provider failure never crashes the search request
                print(f"Notice: provider '{p.id}' error: {resp}")

        # 5. Deduplicate Results
        deduped_items = ResultDeduplicator.deduplicate(all_items)

        # 6. Rank Results Multi-Dimensionally
        ranked_items = RankingEngine.rank(
            results=deduped_items,
            classification=classification,
            user_category=cat,
            user_language=lang,
            user_framework=fw
        )

        # 7. Record in Search History if db provided and query non-empty
        if db and q:
            try:
                history_entry = SearchHistory(
                    query=q,
                    category=cat,
                    language=lang or classification.language,
                    framework=fw or classification.framework,
                    provider=prov or "unified",
                    results_count=len(ranked_items)
                )
                db.add(history_entry)
                db.commit()
            except Exception:
                db.rollback()

        # 8. Cache response
        self.cache.set(cache_key, ranked_items, ttl=300)

        return SearchResponse(
            query=q,
            total_results=len(ranked_items),
            results=ranked_items[:request.limit or 20],
            intent=classification.intent,
            detected_language=classification.language,
            detected_framework=classification.framework,
            active_providers=active_provider_names,
            cached=False
        )

# Global singleton service
unified_search_service = UnifiedSearchService()
