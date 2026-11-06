from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class SearchResultItem(BaseModel):
    id: str
    title: str
    category: str  # 'doc', 'concept', 'error', 'code', 'stackoverflow', 'github', 'web', 'offline', 'notebook', 'snippet'
    snippet: str
    code: Optional[str] = None
    language: Optional[str] = None
    framework: Optional[str] = None
    source: Optional[str] = None
    source_icon: Optional[str] = None
    url: Optional[str] = None
    notebook_id: Optional[str] = None
    block_id: Optional[str] = None
    relevance_score: Optional[float] = None
    date: Optional[str] = None
    stars: Optional[int] = None
    score: Optional[int] = None
    is_answered: Optional[bool] = None
    tags: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None

class SearchQueryRequest(BaseModel):
    query: str
    category: Optional[str] = "all"
    language: Optional[str] = None
    framework: Optional[str] = None
    provider: Optional[str] = None
    page: Optional[int] = 1
    limit: Optional[int] = 20

class SearchResponse(BaseModel):
    query: str
    total_results: int
    results: List[SearchResultItem]
    intent: Optional[str] = None
    detected_language: Optional[str] = None
    detected_framework: Optional[str] = None
    active_providers: Optional[List[str]] = None
    cached: Optional[bool] = False

class WebSearchRequest(BaseModel):
    query: str
    category: Optional[str] = "all"

class ProviderInfo(BaseModel):
    id: str
    name: str
    description: str
    category: str
    is_online: bool
    is_available: bool
    requires_api_key: bool
    has_api_key: bool

class SearchHistoryItem(BaseModel):
    id: str
    query: str
    category: str
    language: Optional[str] = None
    framework: Optional[str] = None
    results_count: int = 0
    created_at: Optional[str] = None

class SavedResourceCreate(BaseModel):
    title: str
    snippet: str
    code: Optional[str] = None
    language: Optional[str] = None
    source: Optional[str] = None
    url: Optional[str] = None
    category: Optional[str] = "general"
    folder: Optional[str] = "General"
    tags: Optional[List[str]] = []
    metadata: Optional[Dict[str, Any]] = {}

class SavedResourceResponse(BaseModel):
    id: str
    title: str
    snippet: str
    code: Optional[str] = None
    language: Optional[str] = None
    source: Optional[str] = None
    url: Optional[str] = None
    category: str
    folder: str
    tags: List[str] = []
    metadata: Dict[str, Any] = {}
    created_at: Optional[str] = None

class DocIndexItem(BaseModel):
    id: str
    name: str
    version: str
    description: Optional[str] = None
    category: str
    status: str
    entry_count: int
    size_bytes: int
    downloaded_at: Optional[str] = None
    url: Optional[str] = None

class DocDownloadRequest(BaseModel):
    index_id: str

class SearchSettings(BaseModel):
    searxng_url: Optional[str] = "http://localhost:8080"
    default_provider: str = "searxng"
    searxng_categories: Optional[List[str]] = ["general", "it", "science"]
    enable_offline_search: bool = True
    enable_cache: bool = True
    google_cse_id: Optional[str] = None
    has_google_key: bool = False
    has_github_token: bool = False

class SearchSettingsUpdate(BaseModel):
    searxng_url: Optional[str] = None
    default_provider: Optional[str] = None
    searxng_categories: Optional[List[str]] = None
    enable_offline_search: Optional[bool] = None
    enable_cache: Optional[bool] = None
    google_api_key: Optional[str] = None
    google_cse_id: Optional[str] = None
    github_token: Optional[str] = None
