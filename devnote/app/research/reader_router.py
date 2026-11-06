"""
DevNote Research Reader — API Router.
Provides endpoints for retrieving native extracted documentation and checking frame restrictions.
"""

from fastapi import APIRouter, Query, HTTPException, status
from devnote.app.research.reader_service import reader_service
from devnote.app.research.providers.base_provider import ExtractedContent

router = APIRouter(prefix="/api/research", tags=["research"])


@router.get("/read", response_model=ExtractedContent)
async def read_research_content(
    url: str = Query(..., description="Target webpage, GitHub repo, or documentation URL to extract"),
    refresh: bool = Query(default=False, description="Bypass in-memory cache and re-extract from source")
):
    """
    Retrieves and renders documentation or technical articles natively.
    Automatically chooses the best extraction strategy (GitHub API, Documentation Extractor, or Article Provider).
    Guarantees strict SSRF protection and sanitization.
    """
    if not url or not url.strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Query parameter 'url' is required.")

    result = await reader_service.read_url(url=url.strip(), force_refresh=refresh)
    return result


@router.get("/check-frame")
async def check_iframe_support(
    url: str = Query(..., description="URL to check for iframe embedding permissions")
):
    """Checks whether a target URL permits embedding inside an iframe."""
    if not url or not url.strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Query parameter 'url' is required.")

    return await reader_service.check_iframe_framing(url.strip())
