from typing import List, Optional
from pydantic import BaseModel

class SnippetCreate(BaseModel):
    title: str
    language: str = "python"
    code: str
    description: Optional[str] = ""
    tags: Optional[List[str]] = []

class SnippetUpdate(BaseModel):
    title: Optional[str] = None
    language: Optional[str] = None
    code: Optional[str] = None
    description: Optional[str] = None
    tags: Optional[List[str]] = None

class SnippetResponse(BaseModel):
    id: str
    title: str
    language: str
    code: str
    description: Optional[str] = ""
    tags: List[str] = []
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
