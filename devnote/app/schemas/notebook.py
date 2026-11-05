from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime

class BlockSchema(BaseModel):
    id: str
    type: str  # heading, paragraph, code, drawing, math, table, checklist, image
    content: Optional[str] = ""
    level: Optional[int] = 2
    language: Optional[str] = "python"
    code: Optional[str] = ""
    output: Optional[str] = ""
    error: Optional[str] = ""
    execution_time_ms: Optional[float] = 0.0
    status: Optional[str] = "idle"
    strokes: Optional[List[Any]] = []
    image_data: Optional[str] = None
    checked: Optional[bool] = False
    rows: Optional[List[List[str]]] = None
    metadata: Optional[Dict[str, Any]] = None

    class Config:
        extra = "allow"

class NotebookCreate(BaseModel):
    title: Optional[str] = "Untitled Notebook"
    description: Optional[str] = ""
    tags: Optional[List[str]] = []
    blocks: Optional[List[Dict[str, Any]]] = None

class NotebookUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    tags: Optional[List[str]] = None
    blocks: Optional[List[Dict[str, Any]]] = None
    is_archived: Optional[bool] = None
    is_pinned: Optional[bool] = None
    version: Optional[int] = None

class NotebookContentPatch(BaseModel):
    blocks: List[Dict[str, Any]]
    title: Optional[str] = None
    tags: Optional[List[str]] = None
    version: Optional[int] = None

class NotebookSummary(BaseModel):
    id: str
    title: str
    description: Optional[str] = ""
    tags: List[str] = []
    block_count: int = 0
    is_archived: bool = False
    is_pinned: bool = False
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    last_edited_at: Optional[str] = None
    pdf_export_path: Optional[str] = None
    pdf_exported_at: Optional[str] = None
    version: int = 1

class NotebookResponse(BaseModel):
    id: str
    title: str
    description: Optional[str] = ""
    tags: List[str] = []
    blocks: List[Dict[str, Any]] = []
    is_archived: bool = False
    is_pinned: bool = False
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    last_edited_at: Optional[str] = None
    pdf_export_path: Optional[str] = None
    pdf_exported_at: Optional[str] = None
    version: int = 1
