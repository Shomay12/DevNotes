"""
DevNote Research Reader — General Technical Article & Tutorial Provider.
Extracts clean, readable content, headings, and code snippets from technical blogs,
programming tutorials, and developer Q&A sites (such as Stack Overflow).
"""

import re
from typing import Dict, Any, List, Optional
import httpx
from bs4 import BeautifulSoup
from devnote.app.research.providers.base_provider import BaseReaderProvider, ExtractedContent, CodeSnippet
from devnote.app.research.content_sanitizer import sanitize_html, extract_code_blocks
from devnote.app.research.source_detector import ReadingStrategy


class ArticleReaderProvider(BaseReaderProvider):
    """Extracts public technical articles, tutorials, and Q&A threads."""

    def can_handle(self, detected_source: Dict[str, Any]) -> bool:
        return True  # Catch-all provider for web articles and blogs

    async def extract(self, url: str, detected_source: Dict[str, Any], client: httpx.AsyncClient) -> ExtractedContent:
        source_name = detected_source.get("source_name", "Article")
        source_type = detected_source.get("source_type", "web_article")

        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
        }

        try:
            resp = await client.get(url, headers=headers, timeout=10.0, follow_redirects=True)
            if resp.status_code != 200:
                fallback = self._get_fallback_article(url, source_name)
                if fallback:
                    return fallback
                return ExtractedContent(
                    status="restricted" if resp.status_code in (401, 403, 429) else "error",
                    reading_strategy=ReadingStrategy.EXTERNAL_FALLBACK,
                    url=url,
                    canonical_url=str(resp.url),
                    title=f"{source_name} ({resp.status_code})",
                    source_name=source_name,
                    error_message=f"HTTP {resp.status_code}: Website restricted access or returned error.",
                    allows_framing=False
                )

            html_text = resp.text
            final_url = str(resp.url)
        except httpx.TimeoutException:
            fallback = self._get_fallback_article(url, source_name)
            if fallback:
                return fallback
            return ExtractedContent(
                status="error",
                reading_strategy=ReadingStrategy.EXTERNAL_FALLBACK,
                url=url,
                canonical_url=url,
                title=source_name,
                source_name=source_name,
                error_message="Connection timed out while loading source webpage.",
                allows_framing=False
            )
        except Exception as e:
            fallback = self._get_fallback_article(url, source_name)
            if fallback:
                return fallback
            return ExtractedContent(
                status="error",
                reading_strategy=ReadingStrategy.EXTERNAL_FALLBACK,
                url=url,
                canonical_url=url,
                title=source_name,
                source_name=source_name,
                error_message=f"Network error: {str(e)}",
                allows_framing=False
            )

        soup = BeautifulSoup(html_text, "html.parser")

        # Handle Stack Overflow / Stack Exchange specifically
        if source_type == "stackoverflow" or "stackoverflow.com" in final_url:
            return self._extract_stackoverflow(soup, url, final_url)

        # 1. Metadata Extraction
        title = self._extract_title(soup, source_name)
        author = self._extract_author(soup)
        published_at = self._extract_published_date(soup)

        # 2. Main Content Extraction
        content_element = self._find_article_container(soup)

        if not content_element or len(content_element.get_text().strip()) < 80:
            return ExtractedContent(
                status="restricted",
                reading_strategy=ReadingStrategy.EXTERNAL_FALLBACK,
                url=url,
                canonical_url=final_url,
                title=title,
                source_name=source_name,
                author=author,
                published_at=published_at,
                error_message="Content could not be automatically extracted from this webpage.",
                allows_framing=detected_source.get("allows_framing", False)
            )

        # Sanitize HTML
        raw_inner_html = str(content_element)
        sanitized_html = sanitize_html(raw_inner_html, base_url=final_url)

        clean_soup = BeautifulSoup(sanitized_html, "html.parser")
        headings = [h.get_text().strip() for h in clean_soup.find_all(["h1", "h2", "h3"]) if h.get_text().strip()]
        raw_text = clean_soup.get_text(separator="\n", strip=True)

        code_snippets_data = extract_code_blocks(sanitized_html)
        snippets = [CodeSnippet(**c) for c in code_snippets_data]

        return ExtractedContent(
            status="success",
            reading_strategy=ReadingStrategy.PUBLIC_ARTICLE,
            url=url,
            canonical_url=final_url,
            title=title,
            source_name=source_name,
            author=author,
            published_at=published_at,
            content_html=sanitized_html,
            raw_text=raw_text,
            code_snippets=snippets,
            headings=headings,
            allows_framing=detected_source.get("allows_framing", False)
        )

    def _extract_title(self, soup: BeautifulSoup, fallback: str) -> str:
        og_title = soup.find("meta", property="og:title")
        if og_title and og_title.get("content"):
            return og_title["content"].strip()

        h1 = soup.find("h1")
        if h1 and h1.get_text().strip():
            return h1.get_text().strip()

        title_tag = soup.find("title")
        if title_tag and title_tag.get_text().strip():
            return title_tag.get_text().strip()

        return fallback

    def _extract_author(self, soup: BeautifulSoup) -> Optional[str]:
        author_meta = soup.find("meta", attrs={"name": "author"}) or soup.find("meta", property="article:author")
        if author_meta and author_meta.get("content"):
            return author_meta["content"].strip()

        author_tag = soup.find(class_=re.compile(r"author|byline", re.I))
        if author_tag:
            return author_tag.get_text().strip()

        return None

    def _extract_published_date(self, soup: BeautifulSoup) -> Optional[str]:
        date_meta = soup.find("meta", property="article:published_time") or soup.find("meta", attrs={"name": "date"})
        if date_meta and date_meta.get("content"):
            return date_meta["content"].strip()

        time_tag = soup.find("time")
        if time_tag:
            return time_tag.get("datetime") or time_tag.get_text().strip()

        return None

    def _find_article_container(self, soup: BeautifulSoup) -> Optional[Any]:
        # Priority content selectors
        candidates = [
            "article",
            "main",
            "div[role='main']",
            "div[itemprop='articleBody']",
            "div.article-content",
            "div.post-content",
            "div.entry-content",
            "div.content",
            "div.markdown-body",
        ]
        for sel in candidates:
            found = soup.select_one(sel)
            if found and len(found.get_text().strip()) > 150:
                return found

        # Fallback: find div with largest paragraph count
        divs = soup.find_all("div")
        best_div = None
        max_p_len = 0
        for d in divs:
            p_len = sum(len(p.get_text()) for p in d.find_all("p"))
            if p_len > max_p_len:
                max_p_len = p_len
                best_div = d

        return best_div

    def _extract_stackoverflow(self, soup: BeautifulSoup, url: str, final_url: str) -> ExtractedContent:
        """Extracts structured Q&A format from Stack Overflow."""
        q_title = ""
        q_header = soup.find("h1", itemprop="name") or soup.find("h1")
        if q_header:
            q_title = q_header.get_text().strip()
        else:
            q_title = "Stack Overflow Question"

        question_body = soup.select_one(".question .js-post-body") or soup.select_one(".postcell .js-post-body")
        answers = soup.select(".answer .js-post-body")

        combined_html = f"<h1>{q_title}</h1>"
        if question_body:
            combined_html += f"<div class='so-question-section'><h2>Question</h2>{str(question_body)}</div>"

        if answers:
            combined_html += "<div class='so-answers-section'><h2>Top Answer(s)</h2>"
            for i, ans in enumerate(answers[:3]):
                combined_html += f"<div class='so-answer-card'>{str(ans)}</div><hr/>"
            combined_html += "</div>"

        sanitized_html = sanitize_html(combined_html, base_url=final_url)
        clean_soup = BeautifulSoup(sanitized_html, "html.parser")
        headings = [h.get_text().strip() for h in clean_soup.find_all(["h1", "h2", "h3"]) if h.get_text().strip()]
        code_snippets_data = extract_code_blocks(sanitized_html)
        snippets = [CodeSnippet(**c) for c in code_snippets_data]

        return ExtractedContent(
            status="success",
            reading_strategy=ReadingStrategy.PUBLIC_ARTICLE,
            url=url,
            canonical_url=final_url,
            title=q_title,
            source_name="Stack Overflow",
            content_html=sanitized_html,
            raw_text=clean_soup.get_text(separator="\n", strip=True),
            code_snippets=snippets,
            headings=headings,
            allows_framing=False
        )

    def _get_fallback_article(self, url: str, source_name: str) -> Optional[ExtractedContent]:
        url_lower = url.lower()
        try:
            from devnote.app.search.providers.general_search_provider import CURATED_GENERAL_KNOWLEDGE
            from devnote.app.search.providers.local_docs_provider import BUNDLED_DOC_PACKS

            for item in CURATED_GENERAL_KNOWLEDGE:
                i_url = item.get("url", "").lower()
                if (i_url and i_url in url_lower) or any(k in url_lower for k in item.get("tags", [])):
                    lang = item.get("language", "python")
                    code = item.get("code", "")
                    snippet = item.get("snippet", "")
                    title = item.get("title", source_name)
                    code_html = f"<pre><code class=\"language-{lang}\">{code}</code></pre>" if code else ""
                    content_html = f"""
                    <div class="reader-doc-article">
                        <h2>{title}</h2>
                        <p>{snippet}</p>
                        {code_html}
                    </div>
                    """
                    snippets = [CodeSnippet(code=code, language=lang)] if code else []
                    return ExtractedContent(
                        status="success",
                        reading_strategy=ReadingStrategy.PUBLIC_ARTICLE,
                        url=url,
                        canonical_url=item.get("url", url),
                        title=title,
                        source_name=item.get("source", source_name),
                        content_html=content_html,
                        raw_text=f"{title}\n\n{snippet}\n\n{code}",
                        code_snippets=snippets,
                        allows_framing=False
                    )

            for pack in BUNDLED_DOC_PACKS:
                for entry in pack.get("entries", []):
                    e_url = entry.get("url", "").lower()
                    if e_url and e_url in url_lower:
                        lang = entry.get("language", "python")
                        code = entry.get("code", "")
                        content = entry.get("content", "")
                        title = entry.get("title", source_name)
                        code_html = f"<pre><code class=\"language-{lang}\">{code}</code></pre>" if code else ""
                        content_html = f"""
                        <div class="reader-doc-article">
                            <h2>{title}</h2>
                            <p>{content}</p>
                            {code_html}
                        </div>
                        """
                        snippets = [CodeSnippet(code=code, language=lang)] if code else []
                        return ExtractedContent(
                            status="success",
                            reading_strategy=ReadingStrategy.PUBLIC_ARTICLE,
                            url=url,
                            canonical_url=entry.get("url", url),
                            title=title,
                            source_name=f"{source_name} (Reference)",
                            content_html=content_html,
                            raw_text=f"{title}\n\n{content}\n\n{code}",
                            code_snippets=snippets,
                            allows_framing=False
                        )
        except Exception:
            pass
        return None
