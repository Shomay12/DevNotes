from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime
from devnote.app.database import Base

class DocIndex(Base):
    __tablename__ = "doc_indexes"

    id = Column(String(50), primary_key=True)  # e.g. "python-core", "fastapi-docs", "javascript-web", "docker-cli", "git-reference"
    name = Column(String(100), nullable=False)
    version = Column(String(50), default="latest")
    description = Column(String(255), nullable=True)
    category = Column(String(50), default="language")
    status = Column(String(50), default="available")  # "downloaded", "available", "downloading"
    entry_count = Column(Integer, default=0)
    size_bytes = Column(Integer, default=0)
    downloaded_at = Column(DateTime, nullable=True)
    url = Column(String(500), nullable=True)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "category": self.category,
            "status": self.status,
            "entry_count": self.entry_count,
            "size_bytes": self.size_bytes,
            "downloaded_at": self.downloaded_at.isoformat() if self.downloaded_at else None,
            "url": self.url
        }
