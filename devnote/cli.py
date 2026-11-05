#!/usr/bin/env python3
"""
DevNote CLI — Cross-Platform Developer Command-Line Interface.
Supported on macOS (Apple Silicon & Intel), Linux, and Windows.
"""

import os
import sys
import json
import time
import socket
import signal
import secrets
import argparse
import platform
import subprocess
import webbrowser
from pathlib import Path
from typing import Optional

_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from devnote.paths import (
    get_user_data_dir,
    get_user_config_dir,
    get_frontend_dir,
    ensure_storage_dirs,
    get_pid_file,
    get_config_file,
    get_log_file,
)

CLI_VERSION = "0.1.0"


def get_lan_ip() -> str:
    """Detects local LAN IP address for local network access (e.g. iPad Safari)."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(0.5)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"


def is_port_in_use(host: str, port: int) -> bool:
    """Checks whether the given host and port are already bound."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.bind((host, port))
            return False
        except OSError:
            return True


def is_devnote_server_running(host: str, port: int) -> bool:
    """Checks if a DevNote instance is already actively responding on host:port."""
    try:
        import urllib.request
        check_host = "127.0.0.1" if host in ("0.0.0.0", "") else host
        url = f"http://{check_host}:{port}/api/health"
        req = urllib.request.Request(url, headers={"User-Agent": "DevNote-CLI"})
        with urllib.request.urlopen(req, timeout=1.0) as resp:
            if resp.status == 200:
                data = json.loads(resp.read().decode())
                return data.get("app") == "DevNote"
    except Exception:
        pass
    return False


def get_active_storage_dir(args_dir: Optional[str] = None) -> Path:
    """Returns active storage directory based on arguments, config file, or system default."""
    if args_dir:
        return Path(args_dir).resolve()

    cfg_file = get_config_file()
    if cfg_file.exists():
        try:
            with open(cfg_file, "r", encoding="utf-8") as f:
                cfg = json.load(f)
                if "data_dir" in cfg and cfg["data_dir"]:
                    return Path(cfg["data_dir"]).resolve()
        except Exception:
            pass

    dev_storage = Path(__file__).resolve().parent.parent / "storage"
    if dev_storage.exists():
        return dev_storage
    return get_user_data_dir()


def write_pid(pid: int, host: str, port: int, token: str, data_dir: Path):
    """Saves daemon/foreground process PID to data directory."""
    pid_file = get_pid_file(data_dir)
    try:
        with open(pid_file, "w", encoding="utf-8") as f:
            json.dump({
                "pid": pid,
                "host": host,
                "port": port,
                "token": token,
                "started_at": time.time(),
                "data_dir": str(data_dir)
            }, f, indent=2)
    except Exception:
        pass


def read_pid(data_dir: Path) -> Optional[dict]:
    """Reads PID record if file exists."""
    pid_file = get_pid_file(data_dir)
    if pid_file.exists():
        try:
            with open(pid_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return None


def remove_pid(data_dir: Path):
    """Deletes PID file safely."""
    pid_file = get_pid_file(data_dir)
    try:
        if pid_file.exists():
            pid_file.unlink()
    except Exception:
        pass


# ----------------------------------------------------------------------
# CLI Commands
# ----------------------------------------------------------------------

def cmd_init(args):
    """Initializes DevNote storage, configuration, and database."""
    target_data_dir = get_active_storage_dir(args.dir)
    ensure_storage_dirs(target_data_dir)

    config_data = {
        "version": CLI_VERSION,
        "data_dir": str(target_data_dir),
        "default_host": "127.0.0.1",
        "default_port": 8000,
        "edition": "local"
    }

    config_dir = get_user_config_dir()
    config_dir.mkdir(parents=True, exist_ok=True)
    config_file = get_config_file(config_dir)
    with open(config_file, "w", encoding="utf-8") as f:
        json.dump(config_data, f, indent=2)

    # Initialize database tables
    os.environ["DEVNOTE_DATA_DIR"] = str(target_data_dir)
    try:
        from devnote.app.database import init_db
        init_db()
    except Exception as e:
        print(f"Warning: Database initialization notice: {e}")

    db_path = target_data_dir / "devnote.db"
    print("=" * 65)
    print("✨ DevNote initialized successfully!")
    print(f"   Config path:  {config_file}")
    print(f"   Storage path: {target_data_dir}")
    print(f"   Database:     {db_path}")
    print("=" * 65)
    print("Run 'devnote start' to launch your workspace.")


def cmd_start(args):
    """Launches the DevNote application server with optional local network access."""
    target_data_dir = get_active_storage_dir(args.dir)
    ensure_storage_dirs(target_data_dir)
    os.environ["DEVNOTE_DATA_DIR"] = str(target_data_dir)

    host = args.host or "127.0.0.1"
    port = args.port or 8000
    edition = args.edition or "local"
    is_network = (host == "0.0.0.0" or host not in ("127.0.0.1", "localhost"))

    # Security: If listening beyond localhost, enforce an access token
    auth_token = args.token or os.environ.get("DEVNOTE_AUTH_TOKEN", "")
    if is_network and not auth_token:
        auth_token = secrets.token_urlsafe(16)

    # Check port availability and handle conflict clearly
    if is_port_in_use(host, port):
        if is_devnote_server_running(host, port):
            print("=" * 65)
            print(f"✓ DevNote is already running at http://{host}:{port}")
            print("=" * 65)
            if not args.no_browser:
                url = f"http://127.0.0.1:{port}"
                if auth_token:
                    url += f"?token={auth_token}"
                print(f"Opening {url} in browser...")
                webbrowser.open(url)
            return
        else:
            print(f"Error: Port {port} on {host} is already in use by another application.")
            print(f"Please specify a different port: devnote start --port <available_port>")
            sys.exit(1)

    # Setup environment variables
    env = os.environ.copy()
    env["DEVNOTE_HOST"] = host
    env["DEVNOTE_PORT"] = str(port)
    env["DEVNOTE_EDITION"] = edition
    env["DEVNOTE_DATA_DIR"] = str(target_data_dir)
    if auth_token:
        env["DEVNOTE_AUTH_TOKEN"] = auth_token

    lan_ip = get_lan_ip()
    local_url = f"http://127.0.0.1:{port}"
    if auth_token:
        local_url += f"?token={auth_token}"
    network_url = f"http://{lan_ip}:{port}?token={auth_token}" if auth_token else f"http://{lan_ip}:{port}"
    db_path = target_data_dir / "devnote.db"

    print("=" * 65)
    print(f"🚀 DevNote {CLI_VERSION} ({edition.capitalize()} Edition)")
    print("=" * 65)
    print(f"   Local URL:    http://127.0.0.1:{port}")
    print(f"   Storage path: {target_data_dir}")
    print(f"   Database:     {db_path}")
    if is_network:
        print(f"   iPad / LAN:   {network_url}")
        print(f"   Access Token: {auth_token}")
        print("   🔒 Network Access Protected by Token Authentication")
    print("   Press CTRL+C to stop server")
    print("=" * 65)

    if args.daemon:
        # Run in daemon/background mode
        log_file = get_log_file(target_data_dir)
        with open(log_file, "a") as f_out:
            proc = subprocess.Popen(
                [sys.executable, "-m", "uvicorn", "devnote.app.main:app", "--host", host, "--port", str(port)],
                env=env,
                stdout=f_out,
                stderr=subprocess.STDOUT
            )
        write_pid(proc.pid, host, port, auth_token, target_data_dir)
        print(f"✓ DevNote running in background (PID: {proc.pid})")
        print(f"  Logs: {log_file}")
        print(f"  Use 'devnote stop' to terminate.")
        return

    # Auto open browser
    if not args.no_browser:
        def open_browser():
            time.sleep(1.2)
            webbrowser.open(local_url)
        import threading
        threading.Thread(target=open_browser, daemon=True).start()

    # Launch uvicorn in foreground
    write_pid(os.getpid(), host, port, auth_token, target_data_dir)

    def handle_signal(sig, frame):
        remove_pid(target_data_dir)
        print("\nDevNote stopped gracefully.")
        sys.exit(0)

    signal.signal(signal.SIGTERM, handle_signal)
    signal.signal(signal.SIGINT, handle_signal)

    try:
        import uvicorn
        uvicorn.run("devnote.app.main:app", host=host, port=port, log_level="info")
    except KeyboardInterrupt:
        print("\nDevNote stopped gracefully.")
    finally:
        remove_pid(target_data_dir)


def cmd_stop(args):
    """Stops background DevNote daemon process."""
    target_data_dir = get_active_storage_dir(args.dir)
    data = read_pid(target_data_dir)

    if not data or not data.get("pid"):
        print("No running DevNote background process found.")
        return

    pid = data.get("pid")
    try:
        if platform.system() == "Windows":
            subprocess.run(["taskkill", "/F", "/PID", str(pid)], check=False)
        else:
            os.kill(pid, signal.SIGTERM)
        print(f"✓ DevNote server (PID: {pid}) stopped.")
    except ProcessLookupError:
        print("DevNote process already terminated.")
    except Exception as e:
        print(f"Error stopping process: {e}")
    finally:
        remove_pid(target_data_dir)


def cmd_open(args):
    """Opens active DevNote instance in default browser."""
    target_data_dir = get_active_storage_dir(args.dir)
    port = args.port or 8000
    token = ""

    data = read_pid(target_data_dir)
    if data:
        port = data.get("port", port)
        token = data.get("token", "")

    target = f"http://127.0.0.1:{port}"
    if token:
        target += f"?token={token}"
    print(f"Opening {target} in browser...")
    webbrowser.open(target)


def cmd_list(args):
    """Lists notebooks in SQLite database directly from CLI."""
    target_data_dir = get_active_storage_dir(args.dir)
    os.environ["DEVNOTE_DATA_DIR"] = str(target_data_dir)

    try:
        from devnote.app.database import SessionLocal
        from devnote.app.models.notebook import Notebook
        db = SessionLocal()
        notebooks = db.query(Notebook).filter(Notebook.is_archived == args.archived).order_by(Notebook.updated_at.desc()).all()
        db.close()

        if not notebooks:
            print("No notebooks found.")
            return

        print(f"{'TITLE':<35} {'BLOCKS':<8} {'TAGS':<20} {'ID':<38}")
        print("-" * 105)
        for nb in notebooks:
            block_count = len(nb.blocks) if isinstance(nb.blocks, list) else 0
            tags_str = ", ".join(nb.tags) if nb.tags else "-"
            print(f"{nb.title[:33]:<35} {block_count:<8} {tags_str[:18]:<20} {nb.id:<38}")
    except Exception as e:
        print(f"Error listing notebooks: {e}")


def cmd_export(args):
    """Exports a notebook to PDF or canonical JSON format from terminal."""
    target_data_dir = get_active_storage_dir(args.dir)
    os.environ["DEVNOTE_DATA_DIR"] = str(target_data_dir)

    notebook_id = args.notebook_id
    fmt = (args.format or "pdf").lower()

    try:
        from devnote.app.database import SessionLocal
        from devnote.app.models.notebook import Notebook
        db = SessionLocal()
        nb = db.query(Notebook).filter(Notebook.id == notebook_id).first()
        if not nb:
            print(f"Error: Notebook '{notebook_id}' not found.")
            db.close()
            return

        if fmt == "json":
            from devnote.app.services.storage_provider import get_storage_provider
            storage = get_storage_provider()
            json_bytes = storage.export_notebook_json(nb.to_dict())
            out_path = Path(args.output) if args.output else Path(f"{nb.title[:30]}_{nb.id[:8]}.devnote.json")
            with open(out_path, "wb") as f:
                f.write(json_bytes)
            print(f"✓ Exported JSON notebook to: {out_path.resolve()} ({len(json_bytes)} bytes)")
        else:
            from devnote.app.services.pdf_service import PDFService
            res = PDFService.export_notebook_to_pdf(db, notebook_id)
            print(f"✓ Exported PDF notebook ({res['page_count']} pages): {res['filename']}")
            print(f"  File: {nb.pdf_export_path}")

        db.close()
    except Exception as e:
        print(f"Export error: {e}")


def cmd_import(args):
    """Imports a PDF or JSON notebook directly into canonical database without duplicates."""
    target_data_dir = get_active_storage_dir(args.dir)
    os.environ["DEVNOTE_DATA_DIR"] = str(target_data_dir)

    file_path = Path(args.file)
    if not file_path.exists():
        print(f"Error: File '{file_path}' does not exist.")
        return

    content = file_path.read_bytes()
    filename = file_path.name.lower()

    try:
        from devnote.app.database import SessionLocal
        db = SessionLocal()

        if filename.endswith(".json") or filename.endswith(".devnote"):
            from devnote.app.services.storage_provider import get_storage_provider
            from devnote.app.models.notebook import Notebook
            from datetime import datetime, timezone

            storage = get_storage_provider()
            payload = storage.parse_notebook_json(content)
            incoming_id = payload.get("notebook_id")
            target_id = args.target or incoming_id

            existing = None
            if target_id:
                existing = db.query(Notebook).filter(Notebook.id == target_id).first()

            if existing:
                existing.title = payload.get("title", existing.title)
                existing.description = payload.get("description", existing.description)
                existing.tags = payload.get("tags", existing.tags)
                existing.blocks = payload.get("blocks", existing.blocks)
                existing.version = (existing.version or 1) + 1
                existing.updated_at = datetime.now(timezone.utc)
                db.commit()
                print(f"✓ Updated existing canonical notebook '{existing.title}' (ID: {existing.id}) without duplicates.")
            else:
                import uuid
                new_nb = Notebook(
                    id=incoming_id or str(uuid.uuid4()),
                    title=payload.get("title", "Imported Notebook"),
                    description=payload.get("description", ""),
                    tags=payload.get("tags", []),
                    blocks=payload.get("blocks", []),
                    version=1
                )
                db.add(new_nb)
                db.commit()
                print(f"✓ Reconstructed notebook '{new_nb.title}' (ID: {new_nb.id}) with {len(new_nb.blocks)} blocks.")
        elif filename.endswith(".pdf"):
            from devnote.app.services.pdf_service import PDFService
            res = PDFService.import_notebook_from_pdf(db, content, target_notebook_id=args.target)
            print(f"✓ {res['message']} (Notebook ID: {res['notebook_id']})")
        else:
            print("Error: Unsupported format. Supported files: .pdf, .json, .devnote")

        db.close()
    except Exception as e:
        print(f"Import error: {e}")


def cmd_doctor(args):
    """Checks system environment, dependencies, sandbox, and network capabilities."""
    print("=" * 65)
    print(f"🩺 DevNote Environment Doctor ({platform.system()} {platform.machine()})")
    print("=" * 65)

    all_good = True

    # 1. Python Check (Python 3.10+)
    py_ver = sys.version.split()[0]
    py_ok = sys.version_info >= (3, 10)
    print(f" [{'✓' if py_ok else '✗'}] Python Runtime: {py_ver} (>= 3.10 required)")
    if not py_ok:
        all_good = False

    # 2. Node.js Check
    node_ok = False
    node_ver = "Not installed"
    try:
        out = subprocess.check_output(["node", "--version"], text=True, stderr=subprocess.DEVNULL)
        node_ver = out.strip()
        node_ok = True
    except Exception:
        pass
    print(f" [{'✓' if node_ok else '!'}] Node.js Engine: {node_ver} (Used for JavaScript execution)")

    # 3. Database & Storage Check
    storage_dir = get_active_storage_dir(args.dir)
    db_writable = False
    try:
        storage_dir.mkdir(parents=True, exist_ok=True)
        test_file = storage_dir / ".doctor_test"
        test_file.write_text("ok")
        test_file.unlink()
        db_writable = True
    except Exception:
        pass
    print(f" [{'✓' if db_writable else '✗'}] Local Storage: {storage_dir} (Writable)")
    if not db_writable:
        all_good = False

    # 4. Packaged Frontend Assets Check
    frontend_dir = get_frontend_dir()
    frontend_ok = frontend_dir.exists() and (frontend_dir / "index.html").exists()
    print(f" [{'✓' if frontend_ok else '✗'}] Packaged Frontend: {frontend_dir} (Found: {frontend_ok})")
    if not frontend_ok:
        all_good = False

    # 5. PDF Rendering Check
    pdf_ok = False
    try:
        import pymupdf
        import reportlab
        pdf_ok = True
        print(f" [✓] PDF Engine: PyMuPDF {pymupdf.__version__} & ReportLab (Ready)")
    except ImportError as e:
        print(f" [✗] PDF Engine: Missing dependencies ({e})")
        all_good = False

    # 6. Isolated Sandbox Check
    sandbox_ok = True
    try:
        from devnote.app.sandbox.runner import execute_code
        res = execute_code("print('sandbox_ok')", "python", timeout=2.0)
        if res.status != "success" or "sandbox_ok" not in res.output:
            sandbox_ok = False
    except Exception:
        sandbox_ok = False
    print(f" [{'✓' if sandbox_ok else '✗'}] Local Sandbox: Isolated subprocess execution with resource limits")
    if not sandbox_ok:
        all_good = False

    # 7. Network Access Check
    lan_ip = get_lan_ip()
    print(f" [✓] Network Interface: IP {lan_ip} (Ready for iPad / local network access)")

    print("=" * 65)
    if all_good:
        print("✓ All system checks passed. DevNote is fully operational!")
    else:
        print("! One or more checks require attention. See diagnostics above.")


def cmd_version(args):
    """Prints DevNote version and build info."""
    print(f"DevNote version {CLI_VERSION} (Cross-Platform Edition)")
    print(f"OS: {platform.system()} {platform.release()} ({platform.machine()})")
    print(f"Python: {sys.version.split()[0]}")


# ----------------------------------------------------------------------
# Main Argument Parser
# ----------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        prog="devnote",
        description="DevNote — Interactive Developer Notebook & Coding Workspace CLI"
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # init
    p_init = subparsers.add_parser("init", help="Initialize workspace & database")
    p_init.add_argument("--dir", help="Custom storage directory path")
    p_init.set_defaults(func=cmd_init)

    # start
    p_start = subparsers.add_parser("start", help="Start the DevNote server")
    p_start.add_argument("--host", default="127.0.0.1", help="Host interface (0.0.0.0 for LAN/iPad)")
    p_start.add_argument("--port", type=int, default=8000, help="Port to listen on (default: 8000)")
    p_start.add_argument("--no-browser", action="store_true", help="Do not open browser automatically")
    p_start.add_argument("--token", help="Access token for network security (auto-generated for 0.0.0.0)")
    p_start.add_argument("--daemon", action="store_true", help="Run server in the background")
    p_start.add_argument("--edition", choices=["local", "hosted"], default="local", help="Distribution edition")
    p_start.add_argument("--dir", help="Custom storage directory")
    p_start.set_defaults(func=cmd_start)

    # stop
    p_stop = subparsers.add_parser("stop", help="Stop background DevNote server")
    p_stop.add_argument("--dir", help="Custom storage directory")
    p_stop.set_defaults(func=cmd_stop)

    # open
    p_open = subparsers.add_parser("open", help="Open active DevNote instance in browser")
    p_open.add_argument("--port", type=int, help="Port to open (default: 8000)")
    p_open.add_argument("--dir", help="Custom storage directory")
    p_open.set_defaults(func=cmd_open)

    # list
    p_list = subparsers.add_parser("list", help="List notebooks in workspace")
    p_list.add_argument("--archived", action="store_true", help="List archived notebooks")
    p_list.add_argument("--dir", help="Custom storage directory")
    p_list.set_defaults(func=cmd_list)

    # export
    p_export = subparsers.add_parser("export", help="Export notebook to PDF or JSON")
    p_export.add_argument("notebook_id", help="Notebook UUID to export")
    p_export.add_argument("--format", choices=["pdf", "json"], default="pdf", help="Export format (pdf or json)")
    p_export.add_argument("--output", help="Output file path")
    p_export.add_argument("--dir", help="Custom storage directory")
    p_export.set_defaults(func=cmd_export)

    # import
    p_import = subparsers.add_parser("import", help="Import PDF or JSON notebook")
    p_import.add_argument("file", help="Path to .pdf, .json, or .devnote file")
    p_import.add_argument("--target", help="Optional target notebook ID to update without duplicate")
    p_import.add_argument("--dir", help="Custom storage directory")
    p_import.set_defaults(func=cmd_import)

    # doctor
    p_doctor = subparsers.add_parser("doctor", help="Check system environment & sandbox health")
    p_doctor.add_argument("--dir", help="Custom storage directory")
    p_doctor.set_defaults(func=cmd_doctor)

    # version
    p_version = subparsers.add_parser("version", help="Show version information")
    p_version.set_defaults(func=cmd_version)

    args = parser.parse_args()
    if hasattr(args, "func"):
        args.func(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
