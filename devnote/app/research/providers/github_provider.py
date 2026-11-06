"""
DevNote Research Reader — GitHub Provider.
Uses the official GitHub REST API to retrieve repository metadata and render
README content natively in markdown/HTML without iframe restrictions.
"""

import re
import base64
from typing import Dict, Any, List, Optional
import httpx
import markdown
from bs4 import BeautifulSoup
from devnote.app.research.providers.base_provider import BaseReaderProvider, ExtractedContent, CodeSnippet
from devnote.app.research.content_sanitizer import sanitize_html, extract_code_blocks
from devnote.app.research.source_detector import ReadingStrategy

GITHUB_API_BASE = "https://api.github.com"


class GitHubReaderProvider(BaseReaderProvider):
    """Fetches repository information and READMEs via GitHub REST API."""

    def can_handle(self, detected_source: Dict[str, Any]) -> bool:
        return detected_source.get("source_type") == "github"

    async def extract(self, url: str, detected_source: Dict[str, Any], client: httpx.AsyncClient) -> ExtractedContent:
        metadata = detected_source.get("metadata", {})
        owner = metadata.get("owner")
        repo = metadata.get("repo")
        branch = metadata.get("branch")
        file_path = metadata.get("file_path")

        if not owner or not repo:
            return ExtractedContent(
                status="error",
                reading_strategy=ReadingStrategy.EXTERNAL_FALLBACK,
                url=url,
                canonical_url=url,
                title="GitHub",
                source_name="GitHub",
                error_message="Invalid GitHub repository URL."
            )

        repo_meta = await self._fetch_repo_metadata(owner, repo, client)
        default_branch = repo_meta.get("default_branch") or branch or "main"
        description = repo_meta.get("description") or "GitHub Repository"
        stars = repo_meta.get("stargazers_count", 0)
        forks = repo_meta.get("forks_count", 0)
        language = repo_meta.get("language") or ""
        license_name = (repo_meta.get("license") or {}).get("name") if isinstance(repo_meta.get("license"), dict) else ""

        # Fetch README or specific file content
        content_html = ""
        raw_text = ""
        doc_title = f"{owner}/{repo}"

        if file_path:
            # Specific file in repo
            doc_title = f"{owner}/{repo}: {file_path}"
            file_content = await self._fetch_file_content(owner, repo, branch or default_branch, file_path, client)
            if file_content:
                if file_path.lower().endswith((".md", ".markdown")):
                    content_html = markdown.markdown(
                        file_content,
                        extensions=["fenced_code", "tables", "codehilite", "toc"]
                    )
                else:
                    ext = file_path.rsplit(".", 1)[-1] if "." in file_path else "code"
                    content_html = f"<pre><code class=\"language-{ext}\">{self._escape_html(file_content)}</code></pre>"
                raw_text = file_content
        else:
            # Fetch repository README
            readme_html, readme_raw = await self._fetch_readme(owner, repo, default_branch, client)
            content_html = readme_html
            raw_text = readme_raw

        # Construct Repository Header Card
        header_card = f"""
        <div class="reader-github-header-card">
          <div class="reader-gh-title-row">
            <h1 class="reader-gh-repo-name">{self._escape_html(owner)} / {self._escape_html(repo)}</h1>
          </div>
          <p class="reader-gh-description">{self._escape_html(description)}</p>
          <div class="reader-gh-badges">
            {f'<span class="reader-badge reader-badge-primary">{stars:,} stars</span>' if stars else ''}
            {f'<span class="reader-badge reader-badge-neutral">{forks:,} forks</span>' if forks else ''}
            {f'<span class="reader-badge reader-badge-lang">{self._escape_html(language)}</span>' if language else ''}
            {f'<span class="reader-badge reader-badge-neutral">{self._escape_html(license_name)}</span>' if license_name else ''}
            <span class="reader-badge reader-badge-neutral">{self._escape_html(default_branch)}</span>
          </div>
        </div>
        """

        full_html = header_card + f"""
        <div class="reader-github-content">
          <h2 class="reader-section-heading">README.md</h2>
          {content_html or "<p>No README found for this repository.</p>"}
        </div>
        """

        base_raw_url = f"https://raw.githubusercontent.com/{owner}/{repo}/{default_branch}/"
        sanitized_html = sanitize_html(full_html, base_url=base_raw_url)

        # Extract headings and code snippets
        soup = BeautifulSoup(sanitized_html, "html.parser")
        headings = [h.get_text().strip() for h in soup.find_all(["h1", "h2", "h3"]) if h.get_text().strip()]
        code_snippets_data = extract_code_blocks(sanitized_html)
        snippets = [CodeSnippet(**c) for c in code_snippets_data]

        canonical = repo_meta.get("html_url") or f"https://github.com/{owner}/{repo}"

        return ExtractedContent(
            status="success" if content_html else "partial",
            reading_strategy=ReadingStrategy.OFFICIAL_API,
            url=url,
            canonical_url=canonical,
            title=f"{owner}/{repo}: {description[:70]}",
            source_name="GitHub",
            author=owner,
            published_at=repo_meta.get("updated_at"),
            content_html=sanitized_html,
            raw_text=raw_text,
            code_snippets=snippets,
            headings=headings,
            allows_framing=False,
            metadata={
                "owner": owner,
                "repo": repo,
                "stars": stars,
                "forks": forks,
                "language": language,
                "default_branch": default_branch
            }
        )

    async def _fetch_repo_metadata(self, owner: str, repo: str, client: httpx.AsyncClient) -> Dict[str, Any]:
        """Fetches repo metadata from GitHub REST API with graceful fallback."""
        api_url = f"{GITHUB_API_BASE}/repos/{owner}/{repo}"
        headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "DevNote-Research-Reader/1.0"
        }
        try:
            resp = await client.get(api_url, headers=headers, timeout=8.0)
            if resp.status_code == 200:
                return resp.json()
        except Exception:
            pass
        return {"full_name": f"{owner}/{repo}", "default_branch": "main"}

    async def _fetch_readme(self, owner: str, repo: str, default_branch: str, client: httpx.AsyncClient) -> tuple[str, str]:
        """
        Retrieves README via GitHub API, falling back to raw.githubusercontent.com.
        Returns (html_string, raw_text).
        """
        # 1. Try GitHub HTML API
        api_url = f"{GITHUB_API_BASE}/repos/{owner}/{repo}/readme"
        headers = {
            "Accept": "application/vnd.github.html+json",
            "User-Agent": "DevNote-Research-Reader/1.0"
        }
        try:
            resp = await client.get(api_url, headers=headers, timeout=8.0)
            if resp.status_code == 200:
                html = resp.text
                return html, ""
        except Exception:
            pass

        # 2. Try raw.githubusercontent.com directly for branches: default, main, master
        for b in [default_branch, "main", "master"]:
            for name in ["README.md", "readme.md", "README.rst", "README"]:
                raw_url = f"https://raw.githubusercontent.com/{owner}/{repo}/{b}/{name}"
                try:
                    resp = await client.get(raw_url, timeout=5.0)
                    if resp.status_code == 200 and resp.text.strip():
                        rendered = markdown.markdown(
                            resp.text,
                            extensions=["fenced_code", "tables", "codehilite", "toc"]
                        )
                        return rendered, resp.text
                except Exception:
                    pass

        return "", ""

    async def _fetch_file_content(self, owner: str, repo: str, branch: str, file_path: str, client: httpx.AsyncClient) -> str:
        """Fetches raw file content from repository."""
        raw_url = f"https://raw.githubusercontent.com/{owner}/{repo}/{branch}/{file_path}"
        try:
            resp = await client.get(raw_url, timeout=8.0)
            if resp.status_code == 200:
                return resp.text
        except Exception:
            pass
        return ""

    def _escape_html(self, text: str) -> str:
        if not text:
            return ""
        return (
            text.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
            .replace("'", "&#039;")
        )
