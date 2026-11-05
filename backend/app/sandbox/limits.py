import os
import sys

def apply_process_limits(memory_limit_mb: int = 256, cpu_timeout_secs: int = 15):
    """
    Apply resource limits to child process via preexec_fn on Unix/macOS.
    Gracefully handles platforms where certain limits are unsupported.
    """
    if sys.platform == "win32":
        return

    try:
        import resource

        # Limit CPU time
        try:
            resource.setrlimit(resource.RLIMIT_CPU, (cpu_timeout_secs, cpu_timeout_secs + 2))
        except (ValueError, OSError):
            pass

        # Limit Max File Size created by process (e.g., 20 MB max output/file)
        try:
            max_file_bytes = 20 * 1024 * 1024
            resource.setrlimit(resource.RLIMIT_FSIZE, (max_file_bytes, max_file_bytes))
        except (ValueError, OSError):
            pass

        # Limit Virtual Memory (Address Space) if supported
        try:
            mem_bytes = memory_limit_mb * 1024 * 1024
            # On macOS, RLIMIT_AS or RLIMIT_DATA can throw if set too low
            # Test safely
            resource.setrlimit(resource.RLIMIT_AS, (mem_bytes * 2, mem_bytes * 2))
        except (ValueError, OSError):
            pass

    except ImportError:
        pass
