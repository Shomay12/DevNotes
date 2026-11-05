import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Boolean, DateTime, JSON, Integer, Text
from devnote.app.database import Base

class Notebook(Base):
    __tablename__ = "notebooks"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    title = Column(String(255), nullable=False, default="Untitled Notebook", index=True)
    description = Column(Text, nullable=True, default="")
    tags = Column(JSON, nullable=False, default=list)
    blocks = Column(JSON, nullable=False, default=list)
    is_archived = Column(Boolean, nullable=False, default=False, index=True)
    is_pinned = Column(Boolean, nullable=False, default=False, index=True)
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    last_edited_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    pdf_export_path = Column(String(512), nullable=True)
    pdf_exported_at = Column(DateTime, nullable=True)
    version = Column(Integer, nullable=False, default=1)

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "tags": self.tags or [],
            "blocks": self.blocks or [],
            "is_archived": self.is_archived,
            "is_pinned": self.is_pinned,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "last_edited_at": self.last_edited_at.isoformat() if self.last_edited_at else None,
            "pdf_export_path": self.pdf_export_path,
            "pdf_exported_at": self.pdf_exported_at.isoformat() if self.pdf_exported_at else None,
            "version": self.version,
        }
