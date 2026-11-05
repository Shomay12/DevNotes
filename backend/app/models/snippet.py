import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Text, DateTime, JSON
from backend.app.database import Base

class Snippet(Base):
    __tablename__ = "snippets"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    title = Column(String(255), nullable=False, index=True)
    language = Column(String(50), nullable=False, default="python")
    code = Column(Text, nullable=False)
    description = Column(Text, nullable=True, default="")
    tags = Column(JSON, nullable=False, default=list)
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "language": self.language,
            "code": self.code,
            "description": self.description,
            "tags": self.tags or [],
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
