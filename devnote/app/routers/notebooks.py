import json
import re
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status, Response, UploadFile, File, Form
from sqlalchemy.orm import Session
from devnote.app.database import get_db
from devnote.app.schemas.notebook import (
    NotebookCreate,
    NotebookUpdate,
    NotebookContentPatch,
    NotebookResponse,
    NotebookSummary,
)
from devnote.app.services.notebook_service import NotebookService
from devnote.app.services.autosave_service import AutosaveService
from devnote.app.services.storage_provider import get_storage_provider
from devnote.app.models.notebook import Notebook
from datetime import datetime, timezone

router = APIRouter(prefix="/api/notebooks", tags=["notebooks"])

@router.get("", response_model=List[NotebookSummary])
def list_notebooks(
    skip: int = 0,
    limit: int = 100,
    archived: bool = False,
    tag: Optional[str] = None,
    query: Optional[str] = None,
    db: Session = Depends(get_db)
):
    notebooks = NotebookService.get_notebooks(db, skip=skip, limit=limit, archived=archived, tag=tag, query=query)
    summaries = []
    for nb in notebooks:
        d = nb.to_dict()
        d["block_count"] = len(nb.blocks) if isinstance(nb.blocks, list) else 0
        summaries.append(NotebookSummary(**d))
    return summaries

@router.get("/recent", response_model=List[NotebookSummary])
def get_recent_notebooks(limit: int = 5, db: Session = Depends(get_db)):
    notebooks = NotebookService.get_recent_notebooks(db, limit=limit)
    summaries = []
    for nb in notebooks:
        d = nb.to_dict()
        d["block_count"] = len(nb.blocks) if isinstance(nb.blocks, list) else 0
        summaries.append(NotebookSummary(**d))
    return summaries

@router.post("", response_model=NotebookResponse, status_code=status.HTTP_201_CREATED)
def create_notebook(notebook_in: NotebookCreate, db: Session = Depends(get_db)):
    notebook = NotebookService.create_notebook(db, notebook_in)
    return NotebookResponse(**notebook.to_dict())

@router.get("/{notebook_id}", response_model=NotebookResponse)
def get_notebook(notebook_id: str, db: Session = Depends(get_db)):
    notebook = NotebookService.get_notebook_by_id(db, notebook_id)
    if not notebook:
        raise HTTPException(status_code=404, detail="Notebook not found")
    return NotebookResponse(**notebook.to_dict())

@router.put("/{notebook_id}", response_model=NotebookResponse)
def update_notebook(notebook_id: str, notebook_in: NotebookUpdate, db: Session = Depends(get_db)):
    notebook = NotebookService.update_notebook(db, notebook_id, notebook_in)
    if not notebook:
        raise HTTPException(status_code=404, detail="Notebook not found")
    return NotebookResponse(**notebook.to_dict())

@router.patch("/{notebook_id}/content", response_model=NotebookResponse)
def autosave_content(notebook_id: str, patch: NotebookContentPatch, db: Session = Depends(get_db)):
    notebook = AutosaveService.autosave_content(db, notebook_id, patch)
    if not notebook:
        raise HTTPException(status_code=404, detail="Notebook not found")
    return NotebookResponse(**notebook.to_dict())

@router.delete("/{notebook_id}", status_code=status.HTTP_200_OK)
def delete_notebook(notebook_id: str, db: Session = Depends(get_db)):
    success = NotebookService.delete_notebook(db, notebook_id)
    if not success:
        raise HTTPException(status_code=404, detail="Notebook not found")
    return {"message": "Notebook deleted successfully", "id": notebook_id}

@router.get("/{notebook_id}/export-json")
def export_notebook_json(notebook_id: str, db: Session = Depends(get_db)):
    notebook = NotebookService.get_notebook_by_id(db, notebook_id)
    if not notebook:
        raise HTTPException(status_code=404, detail="Notebook not found")

    storage = get_storage_provider()
    json_bytes = storage.export_notebook_json(notebook.to_dict())
    safe_title = re.sub(r'[^a-zA-Z0-9_\-]', '_', notebook.title.strip()) or "notebook"
    filename = f"{safe_title}_{notebook.id[:8]}.devnote.json"

    return Response(
        content=json_bytes,
        media_type="application/json",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"'
        }
    )

@router.post("/import-json", response_model=NotebookResponse)
async def import_notebook_json(
    file: Optional[UploadFile] = File(None),
    raw_json: Optional[str] = Form(None),
    target_notebook_id: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    storage = get_storage_provider()
    payload = None

    if file:
        content = await file.read()
        payload = storage.parse_notebook_json(content)
    elif raw_json:
        payload = storage.parse_notebook_json(raw_json.encode("utf-8"))
    else:
        raise HTTPException(status_code=400, detail="Either file or raw_json must be provided.")

    incoming_id = payload.get("notebook_id")
    title = payload.get("title", "Imported Notebook")
    description = payload.get("description", "")
    tags = payload.get("tags", [])
    blocks = payload.get("blocks", [])

    # Check if target notebook was specified or if a notebook with this stable ID exists
    target_id = target_notebook_id or incoming_id
    existing = None
    if target_id:
        existing = db.query(Notebook).filter(Notebook.id == target_id).first()

    if existing:
        # Re-importing into existing: preserve stable ID, update blocks without duplicates
        existing.title = title
        existing.description = description
        existing.tags = tags
        existing.blocks = blocks
        existing.version = (existing.version or 1) + 1
        existing.updated_at = datetime.now(timezone.utc)
        existing.last_edited_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(existing)
        return NotebookResponse(**existing.to_dict())
    else:
        # Create canonical notebook with stable ID
        import uuid
        new_nb = Notebook(
            id=incoming_id or str(uuid.uuid4()),
            title=title,
            description=description,
            tags=tags,
            blocks=blocks,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            last_edited_at=datetime.now(timezone.utc),
            version=1
        )
        db.add(new_nb)
        db.commit()
        db.refresh(new_nb)
        return NotebookResponse(**new_nb.to_dict())
