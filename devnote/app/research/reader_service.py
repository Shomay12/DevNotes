"""
DevNote Research Reader — Unified Reader Service.
Coordinates URL safety validation, source detection, caching, and provider-based
content extraction for the Integrated Research Reader.
"""

import time
from typing import Dict, Any, Optional
import httpx
from devnote.app.research.url_validator import validate_url_safety
from devnote.app.research.source_detector import detect_source, ReadingStrategy
from devnote.app.research.providers.base_provider import ExtractedContent
from devnote.app.research.providers.github_provider import GitHubReaderProvider
from devnote.app.research.providers.documentation_provider import DocumentationReaderProvider
from devnote.app.research.providers.article_provider import ArticleReaderProvider
from devnote.app.research.providers.stackoverflow_provider import StackOverflowReaderProvider
from devnote.app.research.providers.wikipedia_provider import WikipediaReaderProvider

# Simple In-Memory TTL Cache
CACHE_TTL_SECONDS = 900  # 15 minutes
MAX_CACHE_ENTRIES = 200


class ResearchReaderService:
    """Manages the full lifecycle of technical document extraction and rendering."""

    def __init__(self):
        self.github_provider = GitHubReaderProvider()
        self.doc_provider = DocumentationReaderProvider()
        self.stackoverflow_provider = StackOverflowReaderProvider()
        self.wikipedia_provider = WikipediaReaderProvider()
        self.article_provider = ArticleReaderProvider()
        self._cache: Dict[str, tuple[float, ExtractedContent]] = {}

    async def read_url(self, url: str, force_refresh: bool = False) -> ExtractedContent:
        """
        Validates, fetches, and extracts content for native viewing.
        Guarantees safe execution, SSRF protection, and graceful fallback.
        """
        if not url:
            return ExtractedContent(
                status="error",
                reading_strategy=ReadingStrategy.EXTERNAL_FALLBACK,
                url="",
                canonical_url="",
                title="Invalid URL",
                source_name="Unknown",
                error_message="A valid URL is required.",
                allows_framing=False
            )

        clean_url = url.strip()

        # 1. SSRF and Protocol Safety Validation
        is_safe, error_msg = validate_url_safety(clean_url)
        if not is_safe:
            return ExtractedContent(
                status="restricted",
                reading_strategy=ReadingStrategy.EXTERNAL_FALLBACK,
                url=clean_url,
                canonical_url=clean_url,
                title="Access Restricted",
                source_name="Security Shield",
                error_message=error_msg or "Access prohibited by DevNote security policy.",
                allows_framing=False
            )

        # 2. Check Cache
        now = time.time()
        if not force_refresh and clean_url in self._cache:
            cached_time, cached_content = self._cache[clean_url]
            if now - cached_time < CACHE_TTL_SECONDS:
                # Return copy with cached flag
                content_copy = cached_content.model_copy(deep=True)
                content_copy.metadata["cached"] = True
                return content_copy

        # 3. Detect Source and Select Provider
        detected = detect_source(clean_url)

        # 4. Execute extraction
        async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
            try:
                if self.github_provider.can_handle(detected):
                    result = await self.github_provider.extract(clean_url, detected, client)
                elif self.stackoverflow_provider.can_handle(detected):
                    result = await self.stackoverflow_provider.extract(clean_url, detected, client)
                elif self.wikipedia_provider.can_handle(detected):
                    result = await self.wikipedia_provider.extract(clean_url, detected, client)
                elif self.doc_provider.can_handle(detected):
                    result = await self.doc_provider.extract(clean_url, detected, client)
                else:
                    result = await self.article_provider.extract(clean_url, detected, client)
            except Exception as e:
                result = ExtractedContent(
                    status="error",
                    reading_strategy=ReadingStrategy.EXTERNAL_FALLBACK,
                    url=clean_url,
                    canonical_url=clean_url,
                    title=detected.get("source_name", "Web Resource"),
                    source_name=detected.get("source_name", "Web Resource"),
                    error_message=f"Reader extraction error: {str(e)}",
                    allows_framing=detected.get("allows_framing", False)
                )

        # Final check on canonical_url against SSRF (in case of redirect to internal)
        if result.canonical_url and result.canonical_url != clean_url:
            c_safe, c_reason = validate_url_safety(result.canonical_url)
            if not c_safe:
                return ExtractedContent(
                    status="restricted",
                    reading_strategy=ReadingStrategy.EXTERNAL_FALLBACK,
                    url=clean_url,
                    canonical_url=clean_url,
                    title="Redirect Blocked",
                    source_name="Security Shield",
                    error_message=f"Redirect to restricted address blocked: {c_reason}",
                    allows_framing=False
                )

        # 5. Cache result if successful or partial
        if result.status in ("success", "partial"):
            if len(self._cache) >= MAX_CACHE_ENTRIES:
                # Evict oldest entry
                oldest_key = min(self._cache, key=lambda k: self._cache[k][0])
                self._cache.pop(oldest_key, None)
            self._cache[clean_url] = (now, result)

        return result

    async def check_iframe_framing(self, url: str) -> Dict[str, Any]:
        """
        Quick diagnostic endpoint checking if a URL permits iframe embedding.
        Inspects headers without downloading full payload.
        """
        is_safe, error_msg = validate_url_safety(url)
        if not is_safe:
            return {"allows_framing": False, "reason": error_msg}

        detected = detect_source(url)
        if not detected.get("allows_framing", True):
            return {"allows_framing": False, "reason": "Known iframe-restricting domain."}

        try:
            async with httpx.AsyncClient(timeout=4.0, follow_redirects=True) as client:
                resp = await client.head(url, headers={"User-Agent": "DevNote-FrameCheck/1.0"})
                x_frame = resp.headers.get("x-frame-options", "").upper()
                csp = resp.headers.get("content-security-policy", "").lower()

                if x_frame in ("DENY", "SAMEORIGIN"):
                    return {"allows_framing": False, "header": f"X-Frame-Options: {x_frame}"}

                if "frame-ancestors 'none'" in csp or "frame-ancestors 'self'" in csp:
                    return {"allows_framing": False, "header": "CSP frame-ancestors"}

                return {"allows_framing": True}
        except Exception:
            return {"allows_framing": detected.get("allows_framing", False)}


# Singleton instance
reader_service = ResearchReaderService()
