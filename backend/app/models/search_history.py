import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime
from backend.app.database import Base

class SearchHistory(Base):
    __tablename__ = "search_history"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    query = Column(String(255), nullable=False)
    category = Column(String(50), default="all")
    language = Column(String(50), nullable=True)
    framework = Column(String(50), nullable=True)
    provider = Column(String(50), nullable=True)
    results_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "query": self.query,
            "category": self.category,
            "language": self.language,
            "framework": self.framework,
            "provider": self.provider,
            "results_count": self.results_count,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }
