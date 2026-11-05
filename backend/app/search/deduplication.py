import re
from typing import List
from urllib.parse import urlparse, urlunparse
from backend.app.schemas.search import SearchResultItem

class ResultDeduplicator:
    @staticmethod
    def normalize_url(url: str) -> str:
        if not url:
            return ""
        try:
            parsed = urlparse(url)
            # Remove tracking params (utm_*, ref, etc.)
            clean_query = "&".join(
                param for param in parsed.query.split("&")
                if not param.startswith(("utm_", "ref=", "source=", "fbclid=", "gclid="))
            )
            # Strip trailing slash from path
            clean_path = parsed.path.rstrip("/")
            normalized = urlunparse((
                parsed.scheme.lower(),
                parsed.netloc.lower(),
                clean_path,
                parsed.params,
                clean_query,
                parsed.fragment
            ))
            return normalized
        except Exception:
            return url.strip().rstrip("/")

    @classmethod
    def deduplicate(cls, items: List[SearchResultItem]) -> List[SearchResultItem]:
        seen_urls = set()
        seen_titles = set()
        deduped = []

        for item in items:
            norm_url = cls.normalize_url(item.url) if item.url else ""
            norm_title = re.sub(r"[^\w\s]", "", item.title.lower()).strip()

            if norm_url and norm_url in seen_urls:
                continue
            if norm_title and norm_title in seen_titles:
                continue

            if norm_url:
                seen_urls.add(norm_url)
            if norm_title:
                seen_titles.add(norm_title)

            deduped.append(item)

        return deduped
