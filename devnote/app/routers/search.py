import os
import uuid
import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import text
from devnote.app.database import get_db, engine
from devnote.app.models.search_history import SearchHistory
from devnote.app.models.saved_resource import SavedResource
from devnote.app.models.doc_index import DocIndex
from devnote.app.schemas.search import (
    SearchResponse,
    SearchQueryRequest,
    WebSearchRequest,
    ProviderInfo,
    SearchHistoryItem,
    SavedResourceCreate,
    SavedResourceResponse,
    DocIndexItem,
    DocDownloadRequest,
    SearchSettings,
    SearchSettingsUpdate,
    SearchResultItem,
)
from devnote.app.services.search_service import SearchService
from devnote.app.search.search_service import unified_search_service
from devnote.app.search.providers.local_docs_provider import BUNDLED_DOC_PACKS

router = APIRouter(prefix="/api/search", tags=["search"])

# ==========================================
# 1. Unified Search Endpoints
# ==========================================

@router.post("", response_model=SearchResponse)
async def unified_search(
    req: SearchQueryRequest,
    db: Session = Depends(get_db)
):
    """
    Unified DevSearch:
    Searches across DevDocs, Stack Overflow, GitHub, Google, Local Offline Docs,
    and Workspace Notebooks with intelligent query classification and ranking.
    """
    return await unified_search_service.search(request=req, db=db)

@router.get("/providers", response_model=List[ProviderInfo])
def get_search_providers():
    """Lists all configured search providers, their health, and key status."""
    return unified_search_service.get_providers_info()

# Backwards compatible endpoints for existing tests & clients
@router.get("/notebooks", response_model=SearchResponse)
def search_workspace(
    q: str = Query(default="", description="Search query string"),
    category: str = Query(default="all", description="Category: 'all', 'concept', 'doc', 'error', 'code', 'notebook'"),
    db: Session = Depends(get_db)
):
    """Backwards-compatible search endpoint for notebooks and concepts."""
    return SearchService.search_all(db=db, query=q, category=category)

@router.post("/web", response_model=SearchResponse)
async def search_web_resources(
    req: WebSearchRequest,
    db: Session = Depends(get_db)
):
    """SearXNG-powered developer web search endpoint with graceful knowledge base fallback."""
    query_req = SearchQueryRequest(
        query=req.query,
        category=req.category or "all",
        provider="searxng"
    )
    resp = await unified_search_service.search(request=query_req, db=db)
    if not resp.results:
        return SearchService.search_web(query=req.query, category=req.category)
    return resp

# ==========================================
# 2. Search History Endpoints
# ==========================================

@router.get("/history", response_model=List[SearchHistoryItem])
def get_search_history(
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Returns persistent search history entries."""
    rows = db.query(SearchHistory).order_by(SearchHistory.created_at.desc()).limit(limit).all()
    return [
        SearchHistoryItem(
            id=r.id,
            query=r.query,
            category=r.category,
            language=r.language,
            framework=r.framework,
            results_count=r.results_count,
            created_at=r.created_at.isoformat() if r.created_at else None
        )
        for r in rows
    ]

@router.delete("/history/{search_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_search_history_entry(
    search_id: str,
    db: Session = Depends(get_db)
):
    """Deletes an individual search history entry."""
    entry = db.query(SearchHistory).filter(SearchHistory.id == search_id).first()
    if not entry:
        raise HTTPException(status_code=404, detail="Search history entry not found")
    db.delete(entry)
    db.commit()
    return None

@router.delete("/history", status_code=status.HTTP_204_NO_CONTENT)
def clear_all_search_history(db: Session = Depends(get_db)):
    """Clears all search history records."""
    db.query(SearchHistory).delete()
    db.commit()
    return None

# ==========================================
# 3. Local Offline Documentation Manager
# ==========================================

@router.get("/docs", response_model=SearchResponse)
async def search_offline_docs(
    q: str = Query(default="", description="Search query string"),
    index_id: Optional[str] = Query(default=None, description="Optional doc pack index ID filter")
):
    """
    Searches installed local documentation indexes using SQLite FTS5.
    Works completely offline with zero internet access!
    """
    provider = unified_search_service.providers.get("local_docs")
    if not provider:
        raise HTTPException(status_code=500, detail="Local docs provider not available")

    filters = {"index_id": index_id} if index_id else {}
    items = await provider.search(query=q, filters=filters)
    return SearchResponse(
        query=q,
        total_results=len(items),
        results=items,
        intent="concept",
        active_providers=["Local Offline Documentation"]
    )

@router.get("/docs/indexes", response_model=List[DocIndexItem])
def list_doc_indexes(db: Session = Depends(get_db)):
    """Lists available and downloaded local documentation packs."""
    indexes = db.query(DocIndex).all()
    return [
        DocIndexItem(
            id=idx.id,
            name=idx.name,
            version=idx.version,
            description=idx.description,
            category=idx.category,
            status=idx.status,
            entry_count=idx.entry_count,
            size_bytes=idx.size_bytes,
            downloaded_at=idx.downloaded_at.isoformat() if idx.downloaded_at else None,
            url=idx.url
        )
        for idx in indexes
    ]

@router.post("/docs/download", response_model=DocIndexItem)
def download_doc_index(
    req: DocDownloadRequest,
    db: Session = Depends(get_db)
):
    """
    Installs/downloads a documentation pack into the local SQLite FTS5 index.
    """
    # Find requested pack in bundled catalog
    pack = next((p for p in BUNDLED_DOC_PACKS if p["id"] == req.index_id), None)
    if not pack:
        raise HTTPException(status_code=404, detail=f"Documentation index '{req.index_id}' not found in catalog")

    doc_idx = db.query(DocIndex).filter(DocIndex.id == req.index_id).first()
    if not doc_idx:
        doc_idx = DocIndex(
            id=pack["id"],
            name=pack["name"],
            version=pack["version"],
            description=pack["description"],
            category=pack["category"],
            url=f"local://{pack['id']}"
        )
        db.add(doc_idx)

    # Ingest entries into FTS5 table
    try:
        with engine.connect() as conn:
            # Delete existing entries for this index to avoid duplicates
            conn.execute(text("DELETE FROM doc_entries_fts WHERE index_id = :idx_id"), {"idx_id": req.index_id})
            for e in pack["entries"]:
                conn.execute(
                    text("""
                        INSERT INTO doc_entries_fts(index_id, title, category, language, url, content, code)
                        VALUES (:idx_id, :title, :cat, :lang, :url, :content, :code)
                    """),
                    {
                        "idx_id": pack["id"],
                        "title": e["title"],
                        "cat": e["category"],
                        "lang": e["language"],
                        "url": e["url"],
                        "content": e["content"],
                        "code": e["code"]
                    }
                )
            conn.commit()

        doc_idx.status = "downloaded"
        doc_idx.entry_count = len(pack["entries"])
        doc_idx.size_bytes = len(str(pack["entries"]))
        doc_idx.downloaded_at = datetime.datetime.now(datetime.timezone.utc)
        db.commit()
        db.refresh(doc_idx)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to index documentation: {str(e)}")

    return DocIndexItem(
        id=doc_idx.id,
        name=doc_idx.name,
        version=doc_idx.version,
        description=doc_idx.description,
        category=doc_idx.category,
        status=doc_idx.status,
        entry_count=doc_idx.entry_count,
        size_bytes=doc_idx.size_bytes,
        downloaded_at=doc_idx.downloaded_at.isoformat() if doc_idx.downloaded_at else None,
        url=doc_idx.url
    )

@router.delete("/docs/indexes/{index_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_doc_index(
    index_id: str,
    db: Session = Depends(get_db)
):
    """Removes a downloaded documentation pack and purges its FTS5 index entries."""
    doc_idx = db.query(DocIndex).filter(DocIndex.id == index_id).first()
    if not doc_idx:
        raise HTTPException(status_code=404, detail="Documentation index not found")

    try:
        with engine.connect() as conn:
            conn.execute(text("DELETE FROM doc_entries_fts WHERE index_id = :idx_id"), {"idx_id": index_id})
            conn.commit()

        doc_idx.status = "available"
        doc_idx.entry_count = 0
        doc_idx.size_bytes = 0
        doc_idx.downloaded_at = None
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to remove documentation index: {str(e)}")

    return None

# ==========================================
# 4. Saved Resources (Bookmarks) Endpoints
# ==========================================

@router.post("/saved", response_model=SavedResourceResponse, status_code=status.HTTP_201_CREATED)
@router.post("/bookmarks", response_model=SavedResourceResponse, status_code=status.HTTP_201_CREATED)
def save_resource(
    req: SavedResourceCreate,
    db: Session = Depends(get_db)
):
    """Bookmarks/saves a developer search result into local storage."""
    resource = SavedResource(
        id=str(uuid.uuid4()),
        title=req.title,
        snippet=req.snippet,
        code=req.code,
        language=req.language,
        source=req.source,
        url=req.url,
        category=req.category or "general",
        folder=req.folder or "General",
        tags=req.tags or [],
        metadata_json=req.metadata or {}
    )
    db.add(resource)
    db.commit()
    db.refresh(resource)

    return SavedResourceResponse(
        id=resource.id,
        title=resource.title,
        snippet=resource.snippet,
        code=resource.code,
        language=resource.language,
        source=resource.source,
        url=resource.url,
        category=resource.category,
        folder=resource.folder,
        tags=resource.tags or [],
        metadata=resource.metadata_json or {},
        created_at=resource.created_at.isoformat() if resource.created_at else None
    )

@router.get("/saved", response_model=List[SavedResourceResponse])
@router.get("/bookmarks", response_model=List[SavedResourceResponse])
def get_saved_resources(
    folder: Optional[str] = Query(default=None, description="Filter by folder"),
    db: Session = Depends(get_db)
):
    """Retrieves all bookmarked search resources."""
    query = db.query(SavedResource)
    if folder:
        query = query.filter(SavedResource.folder == folder)
    rows = query.order_by(SavedResource.created_at.desc()).all()

    return [
        SavedResourceResponse(
            id=r.id,
            title=r.title,
            snippet=r.snippet,
            code=r.code,
            language=r.language,
            source=r.source,
            url=r.url,
            category=r.category,
            folder=r.folder,
            tags=r.tags or [],
            metadata=r.metadata_json or {},
            created_at=r.created_at.isoformat() if r.created_at else None
        )
        for r in rows
    ]

@router.delete("/saved/{resource_id}", status_code=status.HTTP_204_NO_CONTENT)
@router.delete("/bookmarks/{resource_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_saved_resource(
    resource_id: str,
    db: Session = Depends(get_db)
):
    """Deletes a bookmarked search resource."""
    item = db.query(SavedResource).filter(SavedResource.id == resource_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Saved resource not found")
    db.delete(item)
    db.commit()
    return None

# ==========================================
# 5. Search Settings Endpoints
# ==========================================

DEFAULT_SEARCH_PROVIDER = "searxng"

@router.get("/settings", response_model=SearchSettings)
def get_search_settings():
    """Returns current search engine configuration with SearXNG as default."""
    global DEFAULT_SEARCH_PROVIDER
    searxng = os.environ.get("SEARXNG_URL", "http://localhost:8080")
    google_key = os.environ.get("GOOGLE_API_KEY", "")
    google_cse = os.environ.get("GOOGLE_CSE_ID", "")
    gh_token = os.environ.get("GITHUB_TOKEN", "")

    return SearchSettings(
        searxng_url=searxng if searxng else "http://localhost:8080",
        google_cse_id=google_cse if google_cse else None,
        has_google_key=bool(google_key),
        has_github_token=bool(gh_token),
        default_provider=DEFAULT_SEARCH_PROVIDER,
        searxng_categories=["general", "it", "science"],
        enable_offline_search=True,
        enable_cache=unified_search_service.cache.enabled
    )

@router.put("/settings", response_model=SearchSettings)
def update_search_settings(req: SearchSettingsUpdate):
    """Updates search provider configuration in environment/service."""
    global DEFAULT_SEARCH_PROVIDER
    if req.default_provider is not None:
        DEFAULT_SEARCH_PROVIDER = req.default_provider

    if req.searxng_url is not None:
        os.environ["SEARXNG_URL"] = req.searxng_url.strip()
        if "searxng" in unified_search_service.providers:
            unified_search_service.providers["searxng"].endpoint = req.searxng_url.strip().rstrip("/")

    if req.google_api_key is not None:
        os.environ["GOOGLE_API_KEY"] = req.google_api_key
        if "google" in unified_search_service.providers:
            unified_search_service.providers["google"].api_key = req.google_api_key

    if req.google_cse_id is not None:
        os.environ["GOOGLE_CSE_ID"] = req.google_cse_id
        if "google" in unified_search_service.providers:
            unified_search_service.providers["google"].cse_id = req.google_cse_id

    if req.github_token is not None:
        os.environ["GITHUB_TOKEN"] = req.github_token

    if req.enable_cache is not None:
        unified_search_service.cache.enabled = req.enable_cache

    return get_search_settings()
