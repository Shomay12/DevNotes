import uuid
import copy
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified
from backend.app.schemas.execution import ExecutionRequest, ExecutionResponse
from backend.app.models.execution import ExecutionRecord
from backend.app.models.notebook import Notebook
from backend.app.services.execution_provider import get_execution_provider

class ExecutionService:
    @staticmethod
    def run_code(
        db: Session,
        req: ExecutionRequest
    ) -> ExecutionResponse:
        exec_id = str(uuid.uuid4())
        provider = get_execution_provider()
        
        # Execute through execution provider
        result = provider.execute(
            code=req.code,
            language=req.language,
            timeout=req.timeout or 10.0,
            execution_id=exec_id
        )

        # Record in database
        try:
            record = ExecutionRecord(
                id=exec_id,
                notebook_id=req.notebook_id,
                block_id=req.block_id,
                language=req.language,
                code=req.code,
                output=result.output,
                error=result.error,
                status=result.status,
                execution_time_ms=result.execution_time_ms,
                created_at=datetime.now(timezone.utc)
            )
            db.add(record)

            # If associated with a notebook block, update the block in the document
            if req.notebook_id and req.block_id:
                notebook = db.query(Notebook).filter(Notebook.id == req.notebook_id).first()
                if notebook and isinstance(notebook.blocks, list):
                    updated_blocks = []
                    for b in notebook.blocks:
                        if b.get("id") == req.block_id:
                            b["output"] = result.output
                            b["error"] = result.error
                            b["status"] = result.status
                            b["execution_time_ms"] = result.execution_time_ms
                            
                            # Keep execution history
                            history = b.get("history", [])
                            history.insert(0, {
                                "id": exec_id,
                                "timestamp": datetime.now(timezone.utc).isoformat(),
                                "status": result.status,
                                "execution_time_ms": result.execution_time_ms,
                                "output": result.output[:500] if result.output else "",
                                "error": result.error[:500] if result.error else ""
                            })
                            b["history"] = history[:10]  # keep last 10 runs
                        updated_blocks.append(b)
                    
                    notebook.blocks = copy.deepcopy(updated_blocks)
                    flag_modified(notebook, "blocks")
                    notebook.last_edited_at = datetime.now(timezone.utc)

            db.commit()
        except Exception:
            db.rollback()

        return ExecutionResponse(
            execution_id=exec_id,
            status=result.status,
            output=result.output,
            error=result.error,
            execution_time_ms=result.execution_time_ms,
            language=req.language,
            block_id=req.block_id
        )

    @staticmethod
    def get_status(execution_id: str, db: Session) -> dict:
        provider = get_execution_provider()
        running = provider.is_running(execution_id)
        if running:
            return {
                "execution_id": execution_id,
                "status": "running",
                "is_running": True,
                "output": "",
                "error": "",
                "execution_time_ms": 0.0
            }

        # Check DB
        record = db.query(ExecutionRecord).filter(ExecutionRecord.id == execution_id).first()
        if record:
            return {
                "execution_id": record.id,
                "status": record.status,
                "is_running": False,
                "output": record.output,
                "error": record.error,
                "execution_time_ms": record.execution_time_ms
            }

        return {
            "execution_id": execution_id,
            "status": "unknown",
            "is_running": False,
            "output": "",
            "error": "Execution not found",
            "execution_time_ms": 0.0
        }

    @staticmethod
    def stop(execution_id: str) -> bool:
        provider = get_execution_provider()
        return provider.stop(execution_id)
