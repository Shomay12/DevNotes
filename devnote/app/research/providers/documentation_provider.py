"""
DevNote Research Reader — Technical Documentation Provider.
Specialized extractor for official programming language and framework documentation:
Python Docs, MDN Web Docs, FastAPI, NumPy, Docker, PostgreSQL, ReadTheDocs, and Sphinx.
"""

from typing import Dict, Any, List, Optional
import httpx
from bs4 import BeautifulSoup
from devnote.app.research.providers.base_provider import BaseReaderProvider, ExtractedContent, CodeSnippet
from devnote.app.research.content_sanitizer import sanitize_html, extract_code_blocks
from devnote.app.research.source_detector import ReadingStrategy

# Documentation content container selectors in priority order
DOC_CONTAINER_SELECTORS = {
    "python_docs": [
        "div.body[role='main']",
        "div.body",
        "div.document",
        "section",
    ],
    "mdn": [
        "article.main-page-content",
        "main#content",
        "article",
        "div.main-page-content",
    ],
    "fastapi": [
        "div.md-content__inner",
        "article.md-content__inner",
        "main.md-main",
        "article",
    ],
    "numpy": [
        "article.bd-article",
        "div.bd-article-container",
        "div.body",
        "section",
    ],
    "docker": [
        "main#main-content",
        "div.content",
        "main",
        "article",
    ],
    "postgres": [
        "div#docContent",
        "div.SECT1",
        "div.CHAPTER",
        "div.REFENTRY",
        "div#content",
    ],
    "technical_doc": [
        "article.md-content__inner",
        "div.md-content__inner",
        "div[itemprop='articleBody']",
        "div.document",
        "div.body",
        "article",
        "main",
        "div.content",
        "div.documentation",
    ]
}


class DocumentationReaderProvider(BaseReaderProvider):
    """Retrieves and cleanly extracts technical documentation from public sources."""

    def can_handle(self, detected_source: Dict[str, Any]) -> bool:
        strategy = detected_source.get("strategy")
        source_type = detected_source.get("source_type")
        return (
            strategy == ReadingStrategy.DOCUMENTATION_PROVIDER
            or source_type in ("python_docs", "mdn", "fastapi", "numpy", "docker", "postgres", "technical_doc")
        )

    async def extract(self, url: str, detected_source: Dict[str, Any], client: httpx.AsyncClient) -> ExtractedContent:
        source_type = detected_source.get("source_type", "technical_doc")
        source_name = detected_source.get("source_name", "Documentation")

        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
        }

        try:
            resp = await client.get(url, headers=headers, timeout=10.0, follow_redirects=True)
            if resp.status_code != 200:
                return ExtractedContent(
                    status="restricted" if resp.status_code in (401, 403) else "error",
                    reading_strategy=ReadingStrategy.DOCUMENTATION_PROVIDER,
                    url=url,
                    canonical_url=str(resp.url),
                    title=f"{source_name} ({resp.status_code})",
                    source_name=source_name,
                    error_message=f"HTTP {resp.status_code}: Unable to load content directly from source.",
                    allows_framing=False
                )

            html_text = resp.text
            final_url = str(resp.url)
        except httpx.TimeoutException:
            return ExtractedContent(
                status="error",
                reading_strategy=ReadingStrategy.DOCUMENTATION_PROVIDER,
                url=url,
                canonical_url=url,
                title=source_name,
                source_name=source_name,
                error_message="Connection timed out while retrieving documentation from source.",
                allows_framing=False
            )
        except Exception as e:
            return ExtractedContent(
                status="error",
                reading_strategy=ReadingStrategy.DOCUMENTATION_PROVIDER,
                url=url,
                canonical_url=url,
                title=source_name,
                source_name=source_name,
                error_message=f"Network error: {str(e)}",
                allows_framing=False
            )

        # Parse HTML
        soup = BeautifulSoup(html_text, "html.parser")

        # Extract title
        page_title = ""
        if soup.find("h1"):
            page_title = soup.find("h1").get_text().strip()
        elif soup.find("title"):
            page_title = soup.find("title").get_text().strip()
        if not page_title:
            page_title = f"{source_name} Reference"

        # Locate Main Documentation Container
        selectors = DOC_CONTAINER_SELECTORS.get(source_type, DOC_CONTAINER_SELECTORS["technical_doc"])
        content_element = None

        for sel in selectors:
            candidate = soup.select_one(sel)
            if candidate and len(candidate.get_text().strip()) > 100:
                content_element = candidate
                break

        # Fallback to main or article or body
        if not content_element:
            content_element = soup.find("main") or soup.find("article") or soup.find("body")

        if not content_element:
            return ExtractedContent(
                status="restricted",
                reading_strategy=ReadingStrategy.EXTERNAL_FALLBACK,
                url=url,
                canonical_url=final_url,
                title=page_title,
                source_name=source_name,
                error_message="Could not extract structured documentation content.",
                allows_framing=False
            )

        # Clean document tree: remove sidebars, headers, footers inside content element
        for selector in [
            "nav", "header", "footer", ".toc", ".sidebar", ".sphinxsidebar",
            ".md-sidebar", ".bd-sidebar", ".table-of-contents", ".navigation",
            ".pagination", ".edit-page", ".feedback-widget"
        ]:
            for tag in content_element.select(selector):
                tag.decompose()

        # Sanitize HTML
        raw_inner_html = str(content_element)
        sanitized_html = sanitize_html(raw_inner_html, base_url=final_url)

        # Extract Headings hierarchy and Code Blocks
        clean_soup = BeautifulSoup(sanitized_html, "html.parser")
        headings = [
            h.get_text().strip()
            for h in clean_soup.find_all(["h1", "h2", "h3"])
            if h.get_text().strip()
        ]
        raw_text = clean_soup.get_text(separator="\n", strip=True)

        code_snippets_data = extract_code_blocks(sanitized_html)
        snippets = [CodeSnippet(**c) for c in code_snippets_data]

        return ExtractedContent(
            status="success",
            reading_strategy=ReadingStrategy.DOCUMENTATION_PROVIDER,
            url=url,
            canonical_url=final_url,
            title=page_title,
            source_name=source_name,
            author=source_name,
            content_html=sanitized_html,
            raw_text=raw_text,
            code_snippets=snippets,
            headings=headings,
            allows_framing=False,
            metadata={"source_type": source_type}
        )
