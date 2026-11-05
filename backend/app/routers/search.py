from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from backend.app.database import get_db
from backend.app.schemas.search import SearchResponse, WebSearchRequest
from backend.app.services.search_service import SearchService

router = APIRouter(prefix="/api/search", tags=["search"])

@router.get("/notebooks", response_model=SearchResponse)
def search_workspace(
    q: str = Query(default="", description="Search query string"),
    category: str = Query(default="all", description="Category: 'all', 'concept', 'doc', 'error', 'code', 'notebook'"),
    db: Session = Depends(get_db)
):
    return SearchService.search_all(db=db, query=q, category=category)

@router.post("/web", response_model=SearchResponse)
def search_web_resources(req: WebSearchRequest):
    return SearchService.search_web(query=req.query, category=req.category)
