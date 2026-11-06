"""
DevNote Research Reader — Source Detection & Strategy Classification.
Identifies website category, documentation source, framing capabilities,
and optimal reading strategy for incoming URLs.
"""

import re
from urllib.parse import urlparse
from typing import Dict, Any, Optional

# Known domains that block iframe embedding via X-Frame-Options or CSP frame-ancestors
KNOWN_IFRAME_BLOCKED_DOMAINS = {
    "github.com",
    "raw.githubusercontent.com",
    "google.com",
    "www.google.com",
    "stackoverflow.com",
    "serverfault.com",
    "superuser.com",
    "askubuntu.com",
    "docs.python.org",
    "developer.mozilla.org",
    "medium.com",
    "reddit.com",
    "twitter.com",
    "x.com",
    "en.wikipedia.org",
    "wikipedia.org",
    "arxiv.org",
    "pypi.org",
    "npmjs.com",
    "dev.to",
    "hackernoon.com",
    "news.ycombinator.com",
}

# Paywalled or strict bot-gated sites where external browser fallback should be prioritized
KNOWN_RESTRICTED_DOMAINS = {
    "medium.com",
    "towardsdatascience.com",
    "bloomberg.com",
    "nytimes.com",
    "wsj.com",
}


class ReadingStrategy:
    NATIVE_DOCUMENT = "native_document"
    OFFICIAL_API = "official_api"
    DOCUMENTATION_PROVIDER = "documentation_provider"
    PUBLIC_ARTICLE = "public_article"
    EXTERNAL_FALLBACK = "external_fallback"


def detect_source(url: str) -> Dict[str, Any]:
    """
    Analyzes URL to determine content source, metadata, framing support,
    and the most suitable reading strategy.
    """
    if not url:
        return {
            "source_type": "unknown",
            "source_name": "Unknown",
            "strategy": ReadingStrategy.EXTERNAL_FALLBACK,
            "allows_framing": False,
            "metadata": {}
        }

    parsed = urlparse(url)
    hostname = (parsed.hostname or "").lower()
    path = parsed.path

    metadata: Dict[str, Any] = {
        "hostname": hostname,
        "path": path,
    }

    # Default framing assumption
    allows_framing = hostname not in KNOWN_IFRAME_BLOCKED_DOMAINS and not any(hostname.endswith("." + d) for d in KNOWN_IFRAME_BLOCKED_DOMAINS)

    # 1. GitHub Repositories & Files
    if hostname in ("github.com", "www.github.com"):
        gh_match = re.match(r"^/([^/]+)/([^/]+)(?:/(?:blob|tree)/([^/]+)/(.+))?", path)
        if gh_match:
            owner, repo = gh_match.group(1), gh_match.group(2)
            # Remove .git suffix if present
            if repo.endswith(".git"):
                repo = repo[:-4]
            metadata.update({
                "owner": owner,
                "repo": repo,
                "branch": gh_match.group(3) or None,
                "file_path": gh_match.group(4) or None,
            })
            return {
                "source_type": "github",
                "source_name": "GitHub",
                "strategy": ReadingStrategy.OFFICIAL_API,
                "allows_framing": False,
                "metadata": metadata
            }

    # 2. Official Python Documentation
    if hostname == "docs.python.org":
        return {
            "source_type": "python_docs",
            "source_name": "Python 3 Documentation",
            "strategy": ReadingStrategy.DOCUMENTATION_PROVIDER,
            "allows_framing": False,
            "metadata": metadata
        }

    # 3. MDN Web Docs
    if hostname in ("developer.mozilla.org", "mdn.dev"):
        return {
            "source_type": "mdn",
            "source_name": "MDN Web Docs",
            "strategy": ReadingStrategy.DOCUMENTATION_PROVIDER,
            "allows_framing": False,
            "metadata": metadata
        }

    # 4. FastAPI Documentation
    if hostname in ("fastapi.tiangolo.com", "www.fastapi.tiangolo.com"):
        return {
            "source_type": "fastapi",
            "source_name": "FastAPI Documentation",
            "strategy": ReadingStrategy.DOCUMENTATION_PROVIDER,
            "allows_framing": False,
            "metadata": metadata
        }

    # 5. NumPy & SciPy Documentation
    if hostname in ("numpy.org", "docs.scipy.org", "scipy.org"):
        return {
            "source_type": "numpy",
            "source_name": "NumPy Documentation",
            "strategy": ReadingStrategy.DOCUMENTATION_PROVIDER,
            "allows_framing": False,
            "metadata": metadata
        }

    # 6. Docker Documentation
    if hostname in ("docs.docker.com", "docker.com"):
        return {
            "source_type": "docker",
            "source_name": "Docker Documentation",
            "strategy": ReadingStrategy.DOCUMENTATION_PROVIDER,
            "allows_framing": False,
            "metadata": metadata
        }

    # 7. PostgreSQL Documentation
    if hostname in ("postgresql.org", "www.postgresql.org"):
        return {
            "source_type": "postgres",
            "source_name": "PostgreSQL Documentation",
            "strategy": ReadingStrategy.DOCUMENTATION_PROVIDER,
            "allows_framing": False,
            "metadata": metadata
        }

    # 8. Stack Overflow / Stack Exchange (Official API Extraction)
    if hostname in ("stackoverflow.com", "serverfault.com", "superuser.com", "askubuntu.com") or hostname.endswith(".stackexchange.com"):
        return {
            "source_type": "stackoverflow",
            "source_name": "Stack Overflow",
            "strategy": ReadingStrategy.OFFICIAL_API,
            "allows_framing": False,
            "metadata": metadata
        }

    # 9. Wikipedia (Official API / Encyclopedic Reference)
    if hostname in ("en.wikipedia.org", "wikipedia.org") or hostname.endswith(".wikipedia.org"):
        return {
            "source_type": "wikipedia",
            "source_name": "Wikipedia Reference",
            "strategy": ReadingStrategy.OFFICIAL_API,
            "allows_framing": False,
            "metadata": metadata
        }

    # 10. Generic Documentation Sites
    if hostname.startswith("docs.") or "readthedocs.io" in hostname or "/docs/" in path or "/documentation/" in path or "/api/" in path:
        return {
            "source_type": "technical_doc",
            "source_name": hostname,
            "strategy": ReadingStrategy.DOCUMENTATION_PROVIDER,
            "allows_framing": allows_framing,
            "metadata": metadata
        }

    # 10. Paywalled / Heavily Restricted Domains
    if hostname in KNOWN_RESTRICTED_DOMAINS or any(hostname.endswith("." + d) for d in KNOWN_RESTRICTED_DOMAINS):
        return {
            "source_type": "restricted_article",
            "source_name": hostname,
            "strategy": ReadingStrategy.EXTERNAL_FALLBACK,
            "allows_framing": False,
            "metadata": metadata
        }

    # 11. General Web Articles / Technical Blogs
    return {
        "source_type": "web_article",
        "source_name": hostname,
        "strategy": ReadingStrategy.PUBLIC_ARTICLE,
        "allows_framing": allows_framing,
        "metadata": metadata
    }
