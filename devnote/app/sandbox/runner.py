import os
import sys
import uuid
import time
import shutil
import tempfile
import subprocess
from typing import Dict, Tuple, Optional
from devnote.app.config import (
    PYTHON_BIN,
    NODE_BIN,
    DEFAULT_EXECUTION_TIMEOUT,
    MAX_OUTPUT_LENGTH,
    DEFAULT_MEMORY_LIMIT_MB
)
from devnote.app.sandbox.limits import apply_process_limits

# Active running processes registry for stop/cancel capability
ACTIVE_PROCESSES: Dict[str, subprocess.Popen] = {}

class ExecutionResult:
    def __init__(self, execution_id: str, status: str, output: str, error: str, execution_time_ms: float):
        self.execution_id = execution_id
        self.status = status
        self.output = output
        self.error = error
        self.execution_time_ms = execution_time_ms

    def to_dict(self):
        return {
            "execution_id": self.execution_id,
            "status": self.status,
            "output": self.output,
            "error": self.error,
            "execution_time_ms": self.execution_time_ms,
        }

class BaseLanguageRunner:
    def __init__(self, language: str):
        self.language = language

    def prepare_command(self, script_path: str) -> list[str]:
        raise NotImplementedError

    def get_extension(self) -> str:
        raise NotImplementedError

class PythonRunner(BaseLanguageRunner):
    def __init__(self):
        super().__init__("python")

    def prepare_command(self, script_path: str) -> list[str]:
        # -u for unbuffered binary stdout and stderr
        return [PYTHON_BIN, "-u", script_path]

    def get_extension(self) -> str:
        return ".py"

class JavaScriptRunner(BaseLanguageRunner):
    def __init__(self):
        super().__init__("javascript")

    def prepare_command(self, script_path: str) -> list[str]:
        return [NODE_BIN, script_path]

    def get_extension(self) -> str:
        return ".js"

# Registry of language runners - easily extensible for Ruby, Go, Bash, Rust, etc.
RUNNER_REGISTRY: Dict[str, BaseLanguageRunner] = {
    "python": PythonRunner(),
    "py": PythonRunner(),
    "javascript": JavaScriptRunner(),
    "js": JavaScriptRunner(),
}

def stop_execution(execution_id: str) -> bool:
    """Terminate a running execution process by its ID."""
    process = ACTIVE_PROCESSES.get(execution_id)
    if not process:
        return False

    try:
        process.terminate()
        try:
            process.wait(timeout=1.0)
        except subprocess.TimeoutExpired:
            process.kill()
        return True
    except Exception:
        return False
    finally:
        ACTIVE_PROCESSES.pop(execution_id, None)

def is_execution_running(execution_id: str) -> bool:
    process = ACTIVE_PROCESSES.get(execution_id)
    if not process:
        return False
    return process.poll() is None

def execute_code(
    code: str,
    language: str,
    timeout: float = DEFAULT_EXECUTION_TIMEOUT,
    execution_id: Optional[str] = None
) -> ExecutionResult:
    """
    Executes code in an isolated subprocess with strict environment isolation,
    resource limits, timeouts, and process tracking.
    """
    lang_key = language.strip().lower()
    runner = RUNNER_REGISTRY.get(lang_key)

    if not runner:
        return ExecutionResult(
            execution_id=execution_id or str(uuid.uuid4()),
            status="error",
            output="",
            error=f"Unsupported language: '{language}'. Supported languages: {list(RUNNER_REGISTRY.keys())}",
            execution_time_ms=0.0
        )

    exec_id = execution_id or str(uuid.uuid4())
    temp_dir = tempfile.mkdtemp(prefix=f"devnote_run_{exec_id[:8]}_")

    # Strictly isolated environment: DO NOT pass host secrets or credentials
    safe_env = {
        "PATH": os.environ.get("PATH", "/usr/local/bin:/usr/bin:/bin"),
        "LANG": "en_US.UTF-8",
        "LC_ALL": "en_US.UTF-8",
        "PYTHONIOENCODING": "utf-8",
        "NODE_ENV": "development",
        "HOME": temp_dir,
        "TMPDIR": temp_dir,
    }

    script_path = os.path.join(temp_dir, f"main{runner.get_extension()}")
    try:
        with open(script_path, "w", encoding="utf-8") as f:
            f.write(code)

        cmd = runner.prepare_command(script_path)
        start_time = time.perf_counter()

        def preexec():
            apply_process_limits(memory_limit_mb=DEFAULT_MEMORY_LIMIT_MB, cpu_timeout_secs=int(timeout + 2))

        proc = subprocess.Popen(
            cmd,
            cwd=temp_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env=safe_env,
            preexec_fn=preexec if sys.platform != "win32" else None,
        )

        ACTIVE_PROCESSES[exec_id] = proc

        stdout_data, stderr_data = "", ""
        status = "success"

        try:
            stdout_data, stderr_data = proc.communicate(timeout=timeout)
            duration_ms = round((time.perf_counter() - start_time) * 1000, 2)

            if proc.returncode != 0:
                status = "error"

        except subprocess.TimeoutExpired:
            proc.kill()
            try:
                stdout_data, stderr_data = proc.communicate(timeout=1.0)
            except Exception:
                pass
            duration_ms = round(timeout * 1000, 2)
            status = "timeout"
            stderr_data += f"\n[Execution Timeout: Exceeded {timeout}s limit. Process killed.]"

        # Check if output was truncated to prevent memory crash
        if len(stdout_data) > MAX_OUTPUT_LENGTH:
            stdout_data = stdout_data[:MAX_OUTPUT_LENGTH] + "\n... [Output truncated (exceeded 100,000 characters)]"

        if len(stderr_data) > MAX_OUTPUT_LENGTH:
            stderr_data = stderr_data[:MAX_OUTPUT_LENGTH] + "\n... [Error log truncated]"

        return ExecutionResult(
            execution_id=exec_id,
            status=status,
            output=stdout_data,
            error=stderr_data,
            execution_time_ms=duration_ms
        )

    except Exception as e:
        return ExecutionResult(
            execution_id=exec_id,
            status="error",
            output="",
            error=f"Execution failed to start: {str(e)}",
            execution_time_ms=0.0
        )
    finally:
        ACTIVE_PROCESSES.pop(exec_id, None)
        try:
            shutil.rmtree(temp_dir, ignore_errors=True)
        except Exception:
            pass
