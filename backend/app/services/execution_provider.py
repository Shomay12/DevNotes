import os
import httpx
from abc import ABC, abstractmethod
from typing import Optional
from backend.app.config import (
    DEVNOTE_EDITION,
    DEVNOTE_CLOUD_EXECUTION_URL,
    DEFAULT_EXECUTION_TIMEOUT
)
from backend.app.sandbox.runner import (
    execute_code,
    stop_execution,
    is_execution_running,
    ExecutionResult
)

class BaseExecutionProvider(ABC):
    """Abstract execution provider decoupling code execution infrastructure."""

    @abstractmethod
    def execute(
        self,
        code: str,
        language: str,
        timeout: float = DEFAULT_EXECUTION_TIMEOUT,
        execution_id: Optional[str] = None
    ) -> ExecutionResult:
        pass

    @abstractmethod
    def stop(self, execution_id: str) -> bool:
        pass

    @abstractmethod
    def is_running(self, execution_id: str) -> bool:
        pass


class LocalSubprocessExecutionProvider(BaseExecutionProvider):
    """Local isolated subprocess execution with resource limits and timeouts."""

    def execute(
        self,
        code: str,
        language: str,
        timeout: float = DEFAULT_EXECUTION_TIMEOUT,
        execution_id: Optional[str] = None
    ) -> ExecutionResult:
        return execute_code(code=code, language=language, timeout=timeout, execution_id=execution_id)

    def stop(self, execution_id: str) -> bool:
        return stop_execution(execution_id)

    def is_running(self, execution_id: str) -> bool:
        return is_execution_running(execution_id)


class HostedCloudExecutionProvider(BaseExecutionProvider):
    """
    Cloud sandbox worker provider for the Hosted Edition.
    Dispatches execution requests to isolated cloud runner containers,
    falling back to local subprocess sandbox when cloud worker URL is not configured.
    """

    def __init__(self, worker_url: str = DEVNOTE_CLOUD_EXECUTION_URL):
        self.worker_url = worker_url
        self.local_fallback = LocalSubprocessExecutionProvider()

    def execute(
        self,
        code: str,
        language: str,
        timeout: float = DEFAULT_EXECUTION_TIMEOUT,
        execution_id: Optional[str] = None
    ) -> ExecutionResult:
        if not self.worker_url:
            # Safe fallback to local sandbox if worker URL is not defined
            return self.local_fallback.execute(code, language, timeout, execution_id)

        try:
            with httpx.Client(timeout=timeout + 3.0) as client:
                res = client.post(
                    f"{self.worker_url}/execute",
                    json={
                        "code": code,
                        "language": language,
                        "timeout": timeout,
                        "execution_id": execution_id
                    }
                )
                if res.status_code == 200:
                    d = res.json()
                    return ExecutionResult(
                        execution_id=d.get("execution_id", execution_id),
                        status=d.get("status", "success"),
                        output=d.get("output", ""),
                        error=d.get("error", ""),
                        execution_time_ms=d.get("execution_time_ms", 0.0)
                    )
        except Exception as e:
            # In case of cloud worker error, fallback or report isolated error
            pass

        return self.local_fallback.execute(code, language, timeout, execution_id)

    def stop(self, execution_id: str) -> bool:
        if self.worker_url:
            try:
                with httpx.Client(timeout=3.0) as client:
                    res = client.post(f"{self.worker_url}/executions/{execution_id}/stop")
                    if res.status_code == 200:
                        return True
            except Exception:
                pass
        return self.local_fallback.stop(execution_id)

    def is_running(self, execution_id: str) -> bool:
        return self.local_fallback.is_running(execution_id)


def get_execution_provider() -> BaseExecutionProvider:
    """Factory returning appropriate execution provider according to edition."""
    if DEVNOTE_EDITION == "hosted":
        return HostedCloudExecutionProvider()
    return LocalSubprocessExecutionProvider()
