#!/usr/bin/env python3
"""
DevNote CLI — Cross-Platform Developer Command-Line Interface
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

# Ensure project root is in sys.path so CLI can be run from any working directory
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

# Package constants
CLI_VERSION = "1.1.0"

def resolve_config_dir() -> Path:
    """Resolves config directory, falling back gracefully if ~/.devnote is restricted."""
    home_devnote = Path.home() / ".devnote"
    try:
        home_devnote.mkdir(parents=True, exist_ok=True)
        return home_devnote
    except (PermissionError, OSError):
        local_devnote = ROOT_DIR / ".devnote"
        local_devnote.mkdir(parents=True, exist_ok=True)
        return local_devnote

DEFAULT_CONFIG_DIR = resolve_config_dir()
PID_FILE = DEFAULT_CONFIG_DIR / "devnote.pid"
CONFIG_FILE = DEFAULT_CONFIG_DIR / "config.json"


def get_lan_ip() -> str:
    """Detects local LAN IP address for local network access (e.g. iPad Safari)."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(0.5)
        # Doesn't actually establish external connection, just retrieves interface IP
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"


def get_default_storage_dir() -> Path:
    """Returns storage directory from config or fallback."""
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                cfg = json.load(f)
                if "data_dir" in cfg:
                    return Path(cfg["data_dir"]).resolve()
        except Exception:
            pass
    # Fallback to current project storage or ~/.devnote/storage
    proj_storage = Path(__file__).resolve().parent.parent / "storage"
    if proj_storage.exists():
        return proj_storage
    return DEFAULT_CONFIG_DIR / "storage"


# ----------------------------------------------------------------------
# CLI Commands
# ----------------------------------------------------------------------

def cmd_init(args):
    """Initializes DevNote storage, configuration, and database."""
    config_dir = resolve_config_dir()
    target_data_dir = Path(args.dir).resolve() if args.dir else get_default_storage_dir()
    target_data_dir.mkdir(parents=True, exist_ok=True)
    for sub in ["notebooks", "exports", "uploads"]:
        (target_data_dir / sub).mkdir(parents=True, exist_ok=True)

    config_data = {
        "version": CLI_VERSION,
        "data_dir": str(target_data_dir),
        "default_host": "127.0.0.1",
        "default_port": 8000,
        "edition": "local"
    }

    config_file = config_dir / "config.json"
    with open(config_file, "w", encoding="utf-8") as f:
        json.dump(config_data, f, indent=2)

    # Initialize database tables
    os.environ["DEVNOTE_DATA_DIR"] = str(target_data_dir)
    try:
        from backend.app.database import init_db
        init_db()
    except Exception as e:
        print(f"Warning: Database initialization notice: {e}")

    print("=" * 60)
    print(f"✨ DevNote initialized successfully!")
    print(f"   Config path:  {CONFIG_FILE}")
    print(f"   Storage path: {target_data_dir}")
    print("=" * 60)
    print("Run 'devnote start' to launch your workspace.")


def cmd_start(args):
    """Launches the DevNote application server with optional local network access."""
    host = args.host or "127.0.0.1"
    port = args.port or 8000
    edition = args.edition or "local"
    is_network = (host == "0.0.0.0" or host not in ("127.0.0.1", "localhost"))

    # Security: If listening beyond localhost, enforce an access token
    auth_token = args.token or os.environ.get("DEVNOTE_AUTH_TOKEN", "")
    if is_network and not auth_token:
        auth_token = secrets.token_urlsafe(16)

    # Setup environment variables
    env = os.environ.copy()
    env["DEVNOTE_HOST"] = host
    env["DEVNOTE_PORT"] = str(port)
    env["DEVNOTE_EDITION"] = edition
    if auth_token:
        env["DEVNOTE_AUTH_TOKEN"] = auth_token

    if args.dir:
        env["DEVNOTE_DATA_DIR"] = str(Path(args.dir).resolve())

    lan_ip = get_lan_ip()
    local_url = f"http://127.0.0.1:{port}"
    if auth_token:
        local_url += f"?token={auth_token}"
    network_url = f"http://{lan_ip}:{port}?token={auth_token}" if auth_token else f"http://{lan_ip}:{port}"

    print("=" * 65)
    print(f"🚀 DevNote {CLI_VERSION} ({edition.capitalize()} Edition)")
    print("=" * 65)
    print(f"   Local URL:    http://127.0.0.1:{port}")
    if is_network:
        print(f"   iPad / LAN:   {network_url}")
        print(f"   Access Token: {auth_token}")
        print("   🔒 Network Access Protected by Token Authentication")
    print("   Press CTRL+C to stop server")
    print("=" * 65)

    if args.daemon:
        # Run in daemon/background mode
        DEFAULT_CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        log_file = DEFAULT_CONFIG_DIR / "devnote.log"
        with open(log_file, "a") as f_out:
            proc = subprocess.Popen(
                [sys.executable, "-m", "uvicorn", "backend.app.main:app", "--host", host, "--port", str(port)],
                env=env,
                stdout=f_out,
                stderr=subprocess.STDOUT
            )
        # Record PID
        with open(PID_FILE, "w", encoding="utf-8") as f:
            json.dump({"pid": proc.pid, "host": host, "port": port, "token": auth_token}, f)
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
    try:
        import uvicorn
        uvicorn.run("backend.app.main:app", host=host, port=port, log_level="info")
    except KeyboardInterrupt:
        print("\nDevNote stopped gracefully.")


def cmd_stop(args):
    """Stops background DevNote daemon process."""
    if not PID_FILE.exists():
        print("No running DevNote background process found.")
        return

    try:
        with open(PID_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            pid = data.get("pid")

        if pid:
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
        if PID_FILE.exists():
            PID_FILE.unlink()


def cmd_open(args):
    """Opens active DevNote instance in default browser."""
    port = args.port or 8000
    token = ""
    if PID_FILE.exists():
        try:
            with open(PID_FILE, "r") as f:
                d = json.load(f)
                port = d.get("port", port)
                token = d.get("token", "")
        except Exception:
            pass

    target = f"http://127.0.0.1:{port}"
    if token:
        target += f"?token={token}"
    print(f"Opening {target} in browser...")
    webbrowser.open(target)


def cmd_list(args):
    """Lists notebooks in SQLite database directly from CLI."""
    try:
        from backend.app.database import SessionLocal
        from backend.app.models.notebook import Notebook
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
    notebook_id = args.notebook_id
    fmt = (args.format or "pdf").lower()

    try:
        from backend.app.database import SessionLocal
        from backend.app.models.notebook import Notebook
        db = SessionLocal()
        nb = db.query(Notebook).filter(Notebook.id == notebook_id).first()
        if not nb:
            print(f"Error: Notebook '{notebook_id}' not found.")
            db.close()
            return

        if fmt == "json":
            from backend.app.services.storage_provider import get_storage_provider
            storage = get_storage_provider()
            json_bytes = storage.export_notebook_json(nb.to_dict())
            out_path = Path(args.output) if args.output else Path(f"{nb.title[:30]}_{nb.id[:8]}.devnote.json")
            with open(out_path, "wb") as f:
                f.write(json_bytes)
            print(f"✓ Exported JSON notebook to: {out_path.resolve()} ({len(json_bytes)} bytes)")
        else:
            from backend.app.services.pdf_service import PDFService
            res = PDFService.export_notebook_to_pdf(db, notebook_id)
            print(f"✓ Exported PDF notebook ({res['page_count']} pages): {res['filename']}")
            print(f"  File: {nb.pdf_export_path}")

        db.close()
    except Exception as e:
        print(f"Export error: {e}")


def cmd_import(args):
    """Imports a PDF or JSON notebook directly into canonical database without duplicates."""
    file_path = Path(args.file)
    if not file_path.exists():
        print(f"Error: File '{file_path}' does not exist.")
        return

    content = file_path.read_bytes()
    filename = file_path.name.lower()

    try:
        from backend.app.database import SessionLocal
        db = SessionLocal()

        if filename.endswith(".json") or filename.endswith(".devnote"):
            from backend.app.services.storage_provider import get_storage_provider
            from backend.app.models.notebook import Notebook
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
            from backend.app.services.pdf_service import PDFService
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

    # 1. Python Check
    py_ver = sys.version.split()[0]
    py_ok = sys.version_info >= (3, 12)
    print(f" [{'✓' if py_ok else '✗'}] Python Runtime: {py_ver} (>= 3.12 required)")
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
    storage_dir = get_default_storage_dir()
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

    # 4. PDF Rendering Check
    pdf_ok = False
    try:
        import pymupdf
        import reportlab
        pdf_ok = True
        print(f" [✓] PDF Engine: PyMuPDF {pymupdf.__version__} & ReportLab (Ready)")
    except ImportError as e:
        print(f" [✗] PDF Engine: Missing dependencies ({e})")
        all_good = False

    # 5. Isolated Sandbox Check
    sandbox_ok = True
    try:
        from backend.app.sandbox.runner import execute_code
        res = execute_code("print('sandbox_ok')", "python", timeout=2.0)
        if res.status != "success" or "sandbox_ok" not in res.output:
            sandbox_ok = False
    except Exception:
        sandbox_ok = False
    print(f" [{'✓' if sandbox_ok else '✗'}] Local Sandbox: Isolated subprocess execution with resource limits")
    if not sandbox_ok:
        all_good = False

    # 6. Network Access Check
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
    p_stop.set_defaults(func=cmd_stop)

    # open
    p_open = subparsers.add_parser("open", help="Open active DevNote instance in browser")
    p_open.add_argument("--port", type=int, help="Port to open (default: 8000)")
    p_open.set_defaults(func=cmd_open)

    # list
    p_list = subparsers.add_parser("list", help="List notebooks in workspace")
    p_list.add_argument("--archived", action="store_true", help="List archived notebooks")
    p_list.set_defaults(func=cmd_list)

    # export
    p_export = subparsers.add_parser("export", help="Export notebook to PDF or JSON")
    p_export.add_argument("notebook_id", help="Notebook UUID to export")
    p_export.add_argument("--format", choices=["pdf", "json"], default="pdf", help="Export format (pdf or json)")
    p_export.add_argument("--output", help="Output file path")
    p_export.set_defaults(func=cmd_export)

    # import
    p_import = subparsers.add_parser("import", help="Import PDF or JSON notebook")
    p_import.add_argument("file", help="Path to .pdf, .json, or .devnote file")
    p_import.add_argument("--target", help="Optional target notebook ID to update without duplicate")
    p_import.set_defaults(func=cmd_import)

    # doctor
    p_doctor = subparsers.add_parser("doctor", help="Check system environment & sandbox health")
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
