from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from backend.app.database import get_db
from backend.app.schemas.execution import ExecutionRequest, ExecutionResponse, ExecutionStatusResponse
from backend.app.services.execution_service import ExecutionService

router = APIRouter(prefix="/api", tags=["execution"])

@router.post("/execute", response_model=ExecutionResponse)
def execute_code_block(req: ExecutionRequest, db: Session = Depends(get_db)):
    if req.language.lower() not in ["python", "javascript", "py", "js"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported language '{req.language}'. Only 'python' and 'javascript' are supported."
        )
    return ExecutionService.run_code(db, req)

@router.get("/executions/{execution_id}", response_model=ExecutionStatusResponse)
def get_execution_status(execution_id: str, db: Session = Depends(get_db)):
    status_info = ExecutionService.get_status(execution_id, db)
    return ExecutionStatusResponse(**status_info)

@router.post("/executions/{execution_id}/stop")
def stop_running_execution(execution_id: str):
    stopped = ExecutionService.stop(execution_id)
    return {"execution_id": execution_id, "stopped": stopped}
