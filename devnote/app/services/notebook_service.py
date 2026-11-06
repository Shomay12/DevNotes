import uuid
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from devnote.app.models.notebook import Notebook
from devnote.app.schemas.notebook import NotebookCreate, NotebookUpdate

def get_default_blocks() -> List[Dict[str, Any]]:
    """Generates initial template blocks for a new notebook."""
    return [
        {
            "id": f"block-{uuid.uuid4().hex[:8]}",
            "type": "heading",
            "level": 1,
            "content": "Welcome to DevNote",
            "metadata": {}
        },
        {
            "id": f"block-{uuid.uuid4().hex[:8]}",
            "type": "paragraph",
            "content": "DevNote is an interactive developer notebook combining rich technical notes, executable code blocks, and Apple Pencil handwriting.",
            "metadata": {}
        },
        {
            "id": f"block-{uuid.uuid4().hex[:8]}",
            "type": "code",
            "language": "python",
            "code": "def fibonacci(n):\n    a, b = 0, 1\n    for _ in range(n):\n        yield a\n        a, b = b, a + b\n\nprint('First 8 Fibonacci numbers:', list(fibonacci(8)))",
            "output": "",
            "error": "",
            "execution_time_ms": 0.0,
            "status": "idle",
            "history": []
        },
        {
            "id": f"block-{uuid.uuid4().hex[:8]}",
            "type": "paragraph",
            "content": "Click the **Run** button above or press `Cmd/Ctrl + Enter` to execute. You can insert code blocks, drawings, math formulas, or search docs anywhere using the `/` slash menu.",
            "metadata": {}
        }
    ]

class NotebookService:
    @staticmethod
    def get_notebooks(
        db: Session,
        skip: int = 0,
        limit: int = 100,
        archived: bool = False,
        tag: Optional[str] = None,
        query: Optional[str] = None
    ) -> List[Notebook]:
        q = db.query(Notebook).filter(Notebook.is_archived == archived)
        if query:
            q = q.filter(Notebook.title.ilike(f"%{query}%"))
        q = q.order_by(Notebook.is_pinned.desc(), Notebook.updated_at.desc())
        notebooks = q.offset(skip).limit(limit).all()
        if tag:
            notebooks = [nb for nb in notebooks if tag in (nb.tags or [])]
        return notebooks

    @staticmethod
    def get_recent_notebooks(db: Session, limit: int = 5) -> List[Notebook]:
        return db.query(Notebook)\
            .filter(Notebook.is_archived == False)\
            .order_by(Notebook.last_edited_at.desc())\
            .limit(limit)\
            .all()

    @staticmethod
    def get_notebook_by_id(db: Session, notebook_id: str) -> Optional[Notebook]:
        return db.query(Notebook).filter(Notebook.id == notebook_id).first()

    @staticmethod
    def create_notebook(db: Session, notebook_in: NotebookCreate) -> Notebook:
        notebook_id = str(uuid.uuid4())
        blocks = notebook_in.blocks if notebook_in.blocks is not None else get_default_blocks()
        
        notebook = Notebook(
            id=notebook_id,
            title=notebook_in.title or "Untitled Notebook",
            description=notebook_in.description or "",
            tags=notebook_in.tags or [],
            blocks=blocks,
            is_archived=False,
            is_pinned=False,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            last_edited_at=datetime.now(timezone.utc),
            version=1,
        )
        db.add(notebook)
        db.commit()
        db.refresh(notebook)
        return notebook

    @staticmethod
    def update_notebook(db: Session, notebook_id: str, notebook_in: NotebookUpdate) -> Optional[Notebook]:
        notebook = db.query(Notebook).filter(Notebook.id == notebook_id).first()
        if not notebook:
            return None

        update_data = notebook_in.model_dump(exclude_unset=True) if hasattr(notebook_in, "model_dump") else notebook_in.dict(exclude_unset=True)
        for key, value in update_data.items():
            if key != "version":
                setattr(notebook, key, value)

        notebook.version = (notebook.version or 1) + 1
        notebook.updated_at = datetime.now(timezone.utc)
        notebook.last_edited_at = datetime.now(timezone.utc)

        db.commit()
        db.refresh(notebook)
        return notebook

    @staticmethod
    def delete_notebook(db: Session, notebook_id: str) -> bool:
        notebook = db.query(Notebook).filter(Notebook.id == notebook_id).first()
        if not notebook:
            return False
        db.delete(notebook)
        db.commit()
        return True
