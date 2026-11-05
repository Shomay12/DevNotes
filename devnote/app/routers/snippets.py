from typing import List, Optional
from datetime import datetime, timezone
import uuid
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from devnote.app.database import get_db
from devnote.app.models.snippet import Snippet
from devnote.app.schemas.snippet import SnippetCreate, SnippetUpdate, SnippetResponse

router = APIRouter(prefix="/api/snippets", tags=["snippets"])

@router.get("", response_model=List[SnippetResponse])
def list_snippets(
    language: Optional[str] = None,
    q: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(Snippet)
    if language:
        query = query.filter(Snippet.language == language.lower())
    if q:
        query = query.filter(Snippet.title.ilike(f"%{q}%") | Snippet.code.ilike(f"%{q}%"))
    snippets = query.order_by(Snippet.updated_at.desc()).all()
    return [SnippetResponse(**s.to_dict()) for s in snippets]

@router.post("", response_model=SnippetResponse, status_code=status.HTTP_201_CREATED)
def create_snippet(snippet_in: SnippetCreate, db: Session = Depends(get_db)):
    snippet = Snippet(
        id=str(uuid.uuid4()),
        title=snippet_in.title,
        language=snippet_in.language.lower(),
        code=snippet_in.code,
        description=snippet_in.description or "",
        tags=snippet_in.tags or [],
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    db.add(snippet)
    db.commit()
    db.refresh(snippet)
    return SnippetResponse(**snippet.to_dict())

@router.get("/{snippet_id}", response_model=SnippetResponse)
def get_snippet(snippet_id: str, db: Session = Depends(get_db)):
    snippet = db.query(Snippet).filter(Snippet.id == snippet_id).first()
    if not snippet:
        raise HTTPException(status_code=404, detail="Snippet not found")
    return SnippetResponse(**snippet.to_dict())

@router.put("/{snippet_id}", response_model=SnippetResponse)
def update_snippet(snippet_id: str, snippet_in: SnippetUpdate, db: Session = Depends(get_db)):
    snippet = db.query(Snippet).filter(Snippet.id == snippet_id).first()
    if not snippet:
        raise HTTPException(status_code=404, detail="Snippet not found")

    if snippet_in.title is not None:
        snippet.title = snippet_in.title
    if snippet_in.language is not None:
        snippet.language = snippet_in.language.lower()
    if snippet_in.code is not None:
        snippet.code = snippet_in.code
    if snippet_in.description is not None:
        snippet.description = snippet_in.description
    if snippet_in.tags is not None:
        snippet.tags = snippet_in.tags

    snippet.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(snippet)
    return SnippetResponse(**snippet.to_dict())

@router.delete("/{snippet_id}", status_code=status.HTTP_200_OK)
def delete_snippet(snippet_id: str, db: Session = Depends(get_db)):
    snippet = db.query(Snippet).filter(Snippet.id == snippet_id).first()
    if not snippet:
        raise HTTPException(status_code=404, detail="Snippet not found")
    db.delete(snippet)
    db.commit()
    return {"message": "Snippet deleted", "id": snippet_id}
