import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Text, DateTime, JSON
from devnote.app.database import Base

class SavedResource(Base):
    __tablename__ = "saved_resources"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String(255), nullable=False)
    snippet = Column(Text, nullable=False)
    code = Column(Text, nullable=True)
    language = Column(String(50), nullable=True)
    source = Column(String(100), nullable=True)
    url = Column(String(500), nullable=True)
    category = Column(String(50), default="general")
    folder = Column(String(100), default="General")
    tags = Column(JSON, default=list)
    metadata_json = Column(JSON, default=dict)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "snippet": self.snippet,
            "code": self.code,
            "language": self.language,
            "source": self.source,
            "url": self.url,
            "category": self.category,
            "folder": self.folder,
            "tags": self.tags or [],
            "metadata": self.metadata_json or {},
            "created_at": self.created_at.isoformat() if self.created_at else None
        }
