import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Text, Float, DateTime
from backend.app.database import Base

class ExecutionRecord(Base):
    __tablename__ = "execution_records"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    notebook_id = Column(String(36), nullable=True, index=True)
    block_id = Column(String(64), nullable=True, index=True)
    language = Column(String(50), nullable=False)
    code = Column(Text, nullable=False)
    output = Column(Text, nullable=False, default="")
    error = Column(Text, nullable=False, default="")
    status = Column(String(50), nullable=False, default="success")  # success, error, timeout, stopped
    execution_time_ms = Column(Float, nullable=False, default=0.0)
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        return {
            "id": self.id,
            "notebook_id": self.notebook_id,
            "block_id": self.block_id,
            "language": self.language,
            "code": self.code,
            "output": self.output,
            "error": self.error,
            "status": self.status,
            "execution_time_ms": self.execution_time_ms,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
