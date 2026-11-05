from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
import copy
from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified
from backend.app.models.notebook import Notebook
from backend.app.schemas.notebook import NotebookContentPatch

class AutosaveService:
    @staticmethod
    def autosave_content(
        db: Session,
        notebook_id: str,
        patch: NotebookContentPatch
    ) -> Optional[Notebook]:
        notebook = db.query(Notebook).filter(Notebook.id == notebook_id).first()
        if not notebook:
            return None

        # Update blocks with clean deepcopy and flag modified
        notebook.blocks = copy.deepcopy(patch.blocks)
        flag_modified(notebook, "blocks")

        if patch.title is not None and patch.title.strip():
            notebook.title = patch.title.strip()

        if patch.tags is not None:
            notebook.tags = copy.deepcopy(patch.tags)
            flag_modified(notebook, "tags")

        # Increment version and update timestamps
        notebook.version = (notebook.version or 1) + 1
        notebook.updated_at = datetime.now(timezone.utc)
        notebook.last_edited_at = datetime.now(timezone.utc)

        db.commit()
        db.refresh(notebook)
        return notebook
