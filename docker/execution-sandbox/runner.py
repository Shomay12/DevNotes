import sys
import json
import subprocess
import time

def main():
    if len(sys.argv) < 3:
        print(json.dumps({"status": "error", "output": "", "error": "Usage: runner.py <language> <script_path>"}))
        sys.exit(1)

    language = sys.argv[1].lower()
    script_path = sys.argv[2]
    timeout = float(sys.argv[3]) if len(sys.argv) > 3 else 10.0

    cmd = ["python3", "-u", script_path] if language == "python" else ["node", script_path]

    start_time = time.perf_counter()
    try:
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        stdout, stderr = proc.communicate(timeout=timeout)
        duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
        status = "success" if proc.returncode == 0 else "error"
    except subprocess.TimeoutExpired:
        proc.kill()
        stdout, stderr = proc.communicate()
        duration_ms = round(timeout * 1000, 2)
        status = "timeout"
        stderr += f"\n[Timeout exceeded {timeout}s]"

    print(json.dumps({
        "status": status,
        "output": stdout,
        "error": stderr,
        "execution_time_ms": duration_ms
    }))

if __name__ == "__main__":
    main()
