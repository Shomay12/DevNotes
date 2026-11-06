"""
DevNote Research Reader — Base Provider Interface & Content Models.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
import httpx
from pydantic import BaseModel, Field


class CodeSnippet(BaseModel):
    language: str = "code"
    code: str


class ExtractedContent(BaseModel):
    status: str = "success"  # "success", "partial", "restricted", "error"
    reading_strategy: str
    url: str
    canonical_url: str
    title: str
    source_name: str
    author: Optional[str] = None
    published_at: Optional[str] = None
    content_html: str = ""
    raw_text: str = ""
    code_snippets: List[CodeSnippet] = Field(default_factory=list)
    headings: List[str] = Field(default_factory=list)
    allows_framing: bool = False
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class BaseReaderProvider(ABC):
    """Abstract interface for source-specific research content providers."""

    @abstractmethod
    def can_handle(self, detected_source: Dict[str, Any]) -> bool:
        """Determines if this provider can handle the given detected source."""
        pass

    @abstractmethod
    async def extract(self, url: str, detected_source: Dict[str, Any], client: httpx.AsyncClient) -> ExtractedContent:
        """Fetches and extracts reader content from the target URL."""
        pass
