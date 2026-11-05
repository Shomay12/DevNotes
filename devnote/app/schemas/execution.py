from typing import Optional
from pydantic import BaseModel, Field

class ExecutionRequest(BaseModel):
    language: str = Field(..., description="Programming language: 'python' or 'javascript'")
    code: str = Field(..., description="Code string to execute")
    notebook_id: Optional[str] = None
    block_id: Optional[str] = None
    timeout: Optional[float] = Field(default=10.0, le=30.0, description="Execution timeout in seconds")

class ExecutionResponse(BaseModel):
    execution_id: str
    status: str  # success, error, timeout, stopped
    output: str
    error: str
    execution_time_ms: float
    language: str
    block_id: Optional[str] = None

class ExecutionStatusResponse(BaseModel):
    execution_id: str
    status: str
    is_running: bool
    output: Optional[str] = ""
    error: Optional[str] = ""
    execution_time_ms: Optional[float] = 0.0
