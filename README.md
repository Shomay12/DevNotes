<p align="center">
  <img src="assets/devnote-banner.svg" alt="DevNote Banner" width="100%" />
</p>

<p align="center">
  <a href="https://python.org"><img src="https://img.shields.io/badge/Python-3.12%2B-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python 3.12+"/></a>
  <a href="https://fastapi.tiangolo.com"><img src="https://img.shields.io/badge/FastAPI-0.110%2B-009688?style=for-the-badge&logo=fastapi&logoColor=white" alt="FastAPI"/></a>
  <a href="https://www.sqlite.org"><img src="https://img.shields.io/badge/SQLite-WAL%20Mode-003B57?style=for-the-badge&logo=sqlite&logoColor=white" alt="SQLite WAL"/></a>
  <a href="https://developer.mozilla.org/en-US/docs/Web/JavaScript"><img src="https://img.shields.io/badge/Vanilla_JS-ES6%2B-F7DF1E?style=for-the-badge&logo=javascript&logoColor=black" alt="Vanilla JS"/></a>
  <a href="#-running-automated-tests"><img src="https://img.shields.io/badge/Tests-43%20Passing%20(100%25)-10b981?style=for-the-badge&logo=pytest&logoColor=white" alt="Pytest 100% Passing"/></a>
  <a href="#license"><img src="https://img.shields.io/badge/License-MIT-blue?style=for-the-badge" alt="MIT License"/></a>
</p>

<p align="center">
  <strong>DevNote</strong> is a high-performance, developer-focused technical notebook designed for <strong>MacBook, iPad, touchscreen tablets, and desktop workstations</strong>. It seamlessly unites the executable cell workflows of <strong>Jupyter Notebook</strong>, the fluid structured editing of <strong>Notion</strong>, and the expressive tactile precision of an <strong>Apple Pencil / Stylus technical sketchbook</strong>.
</p>

---

## 📸 Interface Showcase

<p align="center">
  <img src="assets/app-demo-mockup.svg" alt="DevNote Workspace Mockup" width="100%" />
</p>

---

## ⚡ Highlights at a Glance

| Feature | Description | Architecture |
| :--- | :--- | :--- |
| **Executable Cells** | Run **Python 3** and **JavaScript** cells directly inline. | Isolated subprocess sandbox, memory limits, and timeout watchdog. |
| **Apple Pencil Dynamics** | Fluid handwriting, formulas, diagrams, and sketches. | HTML5 Canvas & Pointer Events API with native pressure curves. |
| **50% Split Search** | Search docs, concepts, error fixes, and code side-by-side. | Resizable split panel with 1-click insertion into active notebook. |
| **Strict No-Duplicates** | Persistent canonical documents with stable UUIDs. | SQLite with WAL concurrency; editing never duplicates notebooks. |
| **Lossless Round-Trip** | PDF export embeds exact state for 100% fidelity continuation. | PyMuPDF engine + embedded JSON state payload. |
| **Local Network iPad Sync** | Host on Mac/PC, write seamlessly from iPad on local Wi-Fi. | Secure token-protected local network access (`--host 0.0.0.0`). |

---

## ⚖️ Why DevNote? (Comparison Matrix)

| Feature | DevNote 🚀 | Jupyter Notebook | Notion | Obsidian |
| :--- | :---: | :---: | :---: | :---: |
| **Executable Inline Code** | ✅ Python & JS | ✅ Python/Kernels | ❌ Static text only | ❌ Plugins required |
| **Apple Pencil & Stylus Ink** | ✅ Native Pressure | ❌ Not supported | ❌ Not supported | ⚠️ Basic Excalidraw |
| **50% Split Dev Search & Ingest** | ✅ Built-in 1-Click | ❌ No | ❌ No | ❌ No |
| **Lossless Round-Trip PDF** | ✅ Embedded State | ❌ Static PDF | ❌ Static PDF | ❌ Static PDF |
| **Accidental Copy Prevention** | ✅ Canonical UUIDs | ⚠️ Duplicate `.ipynb` | ⚠️ Copy-paste drift | ⚠️ File name conflicts |
| **Zero Account / 100% Offline** | ✅ Yes | ✅ Yes | ❌ Requires cloud | ✅ Yes |
| **Terminal CLI Management** | ✅ `devnote` CLI | ⚠️ `jupyter notebook` | ❌ No | ❌ No |
| **Zero Frontend Framework Bloat** | ✅ Vanilla JS/HTML5 | ❌ Heavy React/Tornado | ❌ Heavy React/Electron | ❌ Electron |

---

## 📦 Two Distribution Editions

DevNote maintains shared application logic, document schemas, and frontend code across two distinct deployment targets:

### 1. Local Developer Edition (Primary)
> **Available for macOS (Apple Silicon & Intel), Linux, and Windows.**
- 🚀 **Terminal First**: Install and launch directly via `pipx` or `pip`.
- 🔒 **100% Private & Offline**: All notebooks, code, and sketches reside entirely on your local filesystem.
- 🆓 **Zero Subscriptions & Zero Ads**: No accounts, no paywalls, no feature locks, and zero advertisements.
- ⚡ **Local Subprocess Sandbox**: Isolated execution with environment sanitization and resource caps.

### 2. Hosted iPad Web Edition
> **Optimized for iPadOS Safari, touchscreen tablets, and cloud deployments.**
- 📱 **Mobile & Tablet Optimized**: Smooth touch scrolling (`touch-action: none` prevents stylus drawing conflicts).
- ☁️ **Cloud Sandbox Ready**: Decoupled execution provider communicating with isolated cloud execution runners.
- 🤝 **Ethical Monetization**: Funded solely via non-intrusive developer sponsorships in designated sidebar footer cards. **Advertisements are never placed inside notebook documents, code blocks, or drawings**, and private content is never shared.

---

## 💻 Cross-Platform CLI Guide

<p align="center">
  <img src="assets/cli-terminal-preview.svg" alt="DevNote CLI Preview" width="100%" />
</p>

### Installation

```bash
# macOS / Linux (Recommended via pipx)
pipx install devnote
devnote init
devnote start

# Windows (Command Prompt or PowerShell)
py -m pip install devnote
devnote init
devnote start
```

### CLI Command Reference

```bash
# Initialize storage and database
devnote init [--dir <custom_storage_path>]

# Start the application server (opens browser automatically)
devnote start [--host 127.0.0.1] [--port 8000] [--daemon] [--no-browser]

# Stop background daemon server
devnote stop

# Open active workspace in default browser
devnote open [--port 8000]

# List all local notebooks in formatted table
devnote list [--archived]

# Export notebook to PDF or canonical JSON
devnote export <notebook_id> --format pdf --output ./notes.pdf
devnote export <notebook_id> --format json --output ./notes.devnote.json

# Import PDF or JSON notebook (Lossless round-trip with zero duplicates)
devnote import ./notes.devnote.json
devnote import ./exported_notes.pdf

# Run diagnostic health check
devnote doctor

# Display version & system environment
devnote version
```

---

## 📱 Local Network Access for iPad

Pair your Mac or PC notebook host with your iPad over your local Wi-Fi network:

```bash
devnote start --host 0.0.0.0 --port 8080
```

```
=================================================================
🚀 DevNote v1.1.0 (Local Edition — Cross-Platform)
=================================================================
   Local URL:    http://127.0.0.1:8080
   iPad / LAN:   http://192.168.1.50:8080?token=k9_sA7df8203...
   Access Token: k9_sA7df8203...
   🔒 Network Access Protected by Token Authentication
=================================================================
```

> [!IMPORTANT]
> **Network Security Guarantee**: Whenever DevNote listens beyond localhost (`0.0.0.0`), token authentication is automatically activated. Requests from your iPad without the access token are rejected with `401 Unauthorized`. Navigating to the generated link automatically authenticates iPad Safari.

---

## 🔄 Canonical Document & Round-Trip Workflow

DevNote eliminates "accidental copy duplication" through a canonical document state machine:

<p align="center">
  <img src="assets/roundtrip-workflow.svg" alt="Canonical Document Workflow" width="100%" />
</p>

```mermaid
flowchart LR
    A["📓 SQLite Database<br/>(WAL Atomic Transactions)"] -->|"Debounced Autosave"| B["Document Workspace<br/>(Stable UUID)"]
    B -->|"Export"| C["PDF Snapshot<br/>(+ Embedded State)"]
    C -->|"Upload / AirDrop"| D["Host / iPad Web"]
    D -->|"Reconstruct"| A
```

1. **Persistent Document Model**: Each notebook has a permanent UUID stored in SQLite. Editing or reopening restores the exact state.
2. **Debounced Autosave**: Changes save automatically after 800ms with a real-time status indicator (`Saving...` → `All changes saved`).
3. **Lossless PDF Embedding**: When exporting to PDF, DevNote embeds the canonical `devnote_state.json` payload directly into the PDF.
4. **Re-import Continuation**: Uploading the exported PDF reconstructs 100% of the blocks, execution outputs, and handwriting strokes without creating duplicate notebook records.

---

## 🎨 Interactive User Guide

### 1. Rich Block Writing & Slash Menu (`/`)
DevNote is structured around independent, draggable blocks. Press `/` anywhere to summon the insertion palette:

- `/code` or `/python`: Insert executable Python 3 block.
- `/javascript` or `/js`: Insert executable JavaScript block.
- `/heading` (H1, H2, H3): Insert structured section headers.
- `/drawing`: Insert Apple Pencil & stylus canvas.
- `/checklist`: Insert interactive todo checkboxes.
- `/math`: Insert mathematical LaTeX formulas.
- `/table`: Insert data table grid.

### 2. Isolated Code Execution
Write standard Python or JavaScript code and click **▶ Run** or press <kbd>Cmd</kbd> + <kbd>Enter</kbd>:

```python
# Executable Python block inside your notes
import math

def calculate_trajectory(v0, angle_deg):
    theta = math.radians(angle_deg)
    time_of_flight = (2 * v0 * math.sin(theta)) / 9.81
    max_height = (v0**2 * (math.sin(theta)**2)) / (2 * 9.81)
    return time_of_flight, max_height

tof, hmax = calculate_trajectory(25, 45)
print(f"Time of Flight: {tof:.2f}s | Max Height: {hmax:.2f}m")
```

- **Output Panel**: Captures standard output (`stdout`) and execution duration in milliseconds.
- **Error Panel**: Captures tracebacks (`stderr`) in a dedicated red error box.
- **Stop Button**: Halts long-running loops or timeouts immediately.

### 3. DevSearch Lite — Integrated Side-by-Side Developer Research Workspace
Click **Search** in the sidebar or press <kbd>Cmd</kbd> + <kbd>K</kbd> to activate the side-by-side research workspace:
- **Default Search Provider: SearXNG Meta-Search**:
  - Replaces Google Search with privacy-first metasearch aggregation across DuckDuckGo, Brave, Startpage, Wikipedia, arXiv, and developer documentation.
  - **No Paid APIs or Google Credentials Required**: Fully functional out of the box with zero third-party API keys and zero page scraping.
  - **Configurable Endpoint**: Set via `SEARXNG_URL` environment variable or dynamically inside DevSearch Settings (default: `http://localhost:8080`).
  - **Docker Compose for Local Development**: Spin up an isolated, self-hosted SearXNG instance with one command:
    ```bash
    # Start self-hosted SearXNG with pre-configured JSON API
    docker compose up -d searxng
    ```
- **Supported Search Categories**:
  - `General Web`: Wide web search across general engines.
  - `IT & Dev`: Targeted developer documentation, GitHub code, Stack Overflow, and engineering sources.
  - `Science`: Academic papers, research journals, arXiv, and scientific reference materials.
- **Integrated Research Browser (Sandboxed Iframe + Safe Fallback)**:
  - **Side-by-Side Study**: Study documentation and technical articles directly alongside your active notebook without leaving the application or losing context.
  - **Browser Navigation Toolbar**: Full navigation controls featuring `← Results`, `← Back`, `→ Forward`, `↻ Reload`, URL bar navigation, `📋 Copy URL`, `🔖 Bookmark`, and `↗ Open in New Tab`.
  - **Safe X-Frame-Options & CSP Fallback**: Sites that restrict iframe embedding automatically surface an inline reader card with title, summary, code examples, and 1-click external tab access, respecting security boundaries.
  - **Reader / Frame Toggle**: Switch between live embedded web frame and distilled technical summary mode with a single click.
- **Study & Evidence Capture Dock**:
  - Docked directly beneath the research browser to capture quotes, technical notes, and code snippets while reading.
  - **+ Insert Evidence**: Formats clean markdown blockquotes with exact quote, source title, clickable source URL, retrieval date, and personal explanations into the active notebook.
  - **Strict No-Overwrite Guarantee**: All insertions append cleanly as new blocks, never modifying or destroying existing notebook content.
  - **+ Ref / + Code / + Insert All**: Flexible 1-click ingestion for citations, executable code cells, or combined reference blocks.
- **Multi-Provider Search Architecture**:
  - **SearXNG Meta-Search (Default)**: Aggregated technical, IT, and science search.
  - **Official Documentation**: Searches Python 3, MDN Web Docs, FastAPI, Docker, PostgreSQL, Git, Flutter, and DevDocs.
  - **Stack Overflow**: Real-time programming discussions, debugging error fixes, and accepted answers via official Stack Exchange API.
  - **GitHub Search**: Open-source repositories, stars, licenses, and implementations via GitHub REST API.
  - **Local Offline Documentation (SQLite FTS5)**: Full-text search across downloaded doc indexes completely offline with zero internet access.
  - **Workspace Notebooks**: Search across your own notes, blocks, and code snippets.
- **Deterministic Query Classification & Intelligent Routing**:
  - Automatically identifies query intent (**Error Troubleshooting**, **Documentation / Concept**, **Code Implementation**, **API Reference**, **Technical Research**).
  - Detects programming language (**Python, JavaScript, Rust, Go, Java, C++, SQL, Dart**) and framework (**FastAPI, Django, React, Node.js, Docker, Git, PyTorch**).
  - Routes queries to the highest-scoring providers and applies multi-dimensional BM25 + intent ranking.
- **Dynamic Filters & Offline Resilience**:
  - Category tabs: `All Sources`, `IT & Dev`, `Science`, `General Web`, `Official Docs`, `Code Examples`, `Stack Overflow`, `GitHub`, `Offline (FTS5)`, `Notebooks`.
  - Filter by Language and Framework.
  - Live **● Online / ● Offline** status indicator with seamless fallback to local SQLite FTS5 documentation and saved bookmarks.
- **Draggable Divider & Responsive Layout Persistence**:
  - Drag the vertical split divider (`touch-action: none` with Pointer Events support) to customize split ratio (50%/50% default).
  - Remembers panel width and layout state across sessions in `localStorage`.
  - Header actions to reset split (50%), toggle full-screen (100%), or collapse panel (<kbd>Cmd</kbd> + <kbd>K</kbd>).

### 4. Apple Pencil & Stylus Handwriting
Integrated canvas block powered by the HTML5 Canvas & Pointer Events API:
- **Pressure Dynamics**: Reads `e.pressure` to produce variable-width, natural ink strokes.
- **Tools**: Pressure Pen, Semi-Transparent Highlighter, Pixel Eraser, Undo/Redo, and Clear.
- **Color Palette**: Pitch Black, Royal Blue, Ruby Red, Emerald Green, Amber Orange, Purple.
- **iPad Palm Rejection**: Styled with `touch-action: none` so Apple Pencil gestures do not trigger unwanted page scrolling.

---

## ⌨️ Keyboard Shortcuts Reference

| Shortcut | macOS | Windows / Linux | Action |
| :--- | :--- | :--- | :--- |
| **Save Document** | <kbd>Cmd</kbd> + <kbd>S</kbd> | <kbd>Ctrl</kbd> + <kbd>S</kbd> | Save document immediately to SQLite. |
| **Search Workspace** | <kbd>Cmd</kbd> + <kbd>K</kbd> | <kbd>Ctrl</kbd> + <kbd>K</kbd> | Open or collapse Developer Search panel. |
| **Execute Block** | <kbd>Cmd</kbd> + <kbd>Enter</kbd> | <kbd>Ctrl</kbd> + <kbd>Enter</kbd> | Run the active code block. |
| **Component Menu** | <kbd>/</kbd> | <kbd>/</kbd> | Open block insertion slash command menu. |
| **Smart Indent** | <kbd>Tab</kbd> | <kbd>Tab</kbd> | Insert 4 spaces in code editor without losing focus. |
| **Undo / Redo** | <kbd>Cmd</kbd> + <kbd>Z</kbd> / <kbd>Shift</kbd> | <kbd>Ctrl</kbd> + <kbd>Z</kbd> / <kbd>Shift</kbd> | Undo or redo text and canvas strokes. |

---

## 🏛️ System Architecture

```
devnote/
├── assets/                      # Animated SVGs, diagrams, and hero graphics
│   ├── devnote-banner.svg
│   ├── app-demo-mockup.svg
│   ├── roundtrip-workflow.svg
│   └── cli-terminal-preview.svg
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI app, static mounts & auth middleware
│   │   ├── config.py            # Environment, edition & network settings
│   │   ├── database.py          # SQLite engine & WAL mode listener
│   │   ├── models/              # SQLite ORM models (Notebook, Snippet, ExecutionRecord)
│   │   ├── schemas/             # Pydantic validation schemas
│   │   ├── routers/             # API routes (notebooks, execution, pdf, search, snippets)
│   │   ├── services/
│   │   │   ├── storage_provider.py    # Decoupled Storage (LocalStorage vs HostedStorage)
│   │   │   ├── execution_provider.py  # Decoupled Execution (LocalSandbox vs CloudSandbox)
│   │   │   ├── notebook_service.py
│   │   │   ├── pdf_service.py
│   │   │   └── search_service.py
│   │   └── sandbox/             # Subprocess runner, resource limits & timeouts
│   ├── cli.py                   # Cross-Platform CLI entry point
│   ├── tests/                   # Pytest test suite (100% passing)
│   └── requirements.txt
├── frontend/                    # Pure HTML5 / CSS3 / Vanilla JavaScript UI
│   ├── index.html
│   ├── css/
│   │   ├── main.css
│   │   ├── sidebar.css
│   │   ├── editor.css
│   │   └── responsive.css
│   └── js/
│       ├── api.js
│       ├── app.js
│       ├── editor.js
│       ├── code-blocks.js
│       ├── handwriting.js
│       ├── search.js
│       └── pdf.js
├── storage/                     # SQLite database & exported PDF files
├── pyproject.toml               # Python package configuration
├── Dockerfile                   # Production container definition
└── docker-compose.yml           # Multi-platform orchestration
```

---

## 🐳 Docker & Container Deployment

Deploy DevNote in a single command using Docker and Docker Compose:

```bash
# Build and run with isolated persistent volumes
docker compose up -d

# Check running container logs
docker compose logs -f

# Stop container gracefully
docker compose down
```

The container automatically mounts `./storage` to persist your notebooks, SQLite database, uploads, and PDF exports across container restarts.

---

## 🧪 Running Automated Tests

DevNote and DevSearch include a complete test suite covering notebooks, code execution, sandbox timeouts, PDF round-trips, search query classification, ranking, SQLite FTS5 offline docs, snippet library, and the full end-to-end 18-step user acceptance workflow:

```bash
# Run complete test suite (38 tests)
source venv/bin/activate
PYTHONPATH=. pytest backend/tests -v
```

```
============================= test session starts ==============================
backend/tests/test_cli_and_distribution.py::test_api_config_endpoint PASSED [  2%]
backend/tests/test_cli_and_distribution.py::test_json_export_and_import_endpoints PASSED [  5%]
backend/tests/test_cli_and_distribution.py::test_storage_provider_abstraction PASSED [  7%]
backend/tests/test_cli_and_distribution.py::test_execution_provider_abstraction PASSED [ 10%]
backend/tests/test_cli_and_distribution.py::test_network_security_middleware PASSED [ 13%]
backend/tests/test_cli_and_distribution.py::test_cli_execution_commands PASSED [ 15%]
backend/tests/test_devsearch.py::test_query_classifier_concept PASSED    [ 18%]
backend/tests/test_devsearch.py::test_query_classifier_error PASSED      [ 21%]
backend/tests/test_devsearch.py::test_query_classifier_code_implementation PASSED [ 23%]
backend/tests/test_devsearch.py::test_query_classifier_javascript PASSED [ 26%]
backend/tests/test_devsearch.py::test_result_deduplicator PASSED         [ 28%]
backend/tests/test_devsearch.py::test_ranking_engine_error_boost PASSED  [ 31%]
backend/tests/test_devsearch.py::test_search_cache PASSED                [ 34%]
backend/tests/test_devsearch.py::test_api_unified_search_post PASSED     [ 36%]
backend/tests/test_devsearch.py::test_api_search_providers_list PASSED   [ 39%]
backend/tests/test_devsearch.py::test_api_search_history_lifecycle PASSED [ 42%]
backend/tests/test_devsearch.py::test_api_offline_docs_search PASSED     [ 44%]
backend/tests/test_devsearch.py::test_api_doc_indexes_management PASSED  [ 47%]
backend/tests/test_devsearch.py::test_api_saved_resources_crud PASSED    [ 50%]
backend/tests/test_devsearch.py::test_api_search_settings PASSED         [ 52%]
backend/tests/test_devsearch_e2e.py::test_devsearch_full_acceptance_workflow PASSED [ 55%]
backend/tests/test_e2e_workflow.py::test_full_devnote_acceptance_workflow PASSED [ 57%]
backend/tests/test_execution.py::test_execute_python_success PASSED      [ 60%]
backend/tests/test_execution.py::test_execute_javascript_success PASSED  [ 63%]
backend/tests/test_execution.py::test_execute_python_error PASSED        [ 65%]
backend/tests/test_execution.py::test_execute_timeout PASSED             [ 68%]
backend/tests/test_execution.py::test_execute_updates_notebook_block PASSED [ 71%]
backend/tests/test_notebooks.py::test_health PASSED                      [ 73%]
backend/tests/test_notebooks.py::test_create_and_get_notebook PASSED     [ 76%]
backend/tests/test_notebooks.py::test_autosave_content PASSED            [ 78%]
backend/tests/test_notebooks.py::test_update_notebook_metadata PASSED    [ 81%]
backend/tests/test_notebooks.py::test_delete_notebook PASSED             [ 83%]
backend/tests/test_pdf.py::test_pdf_export_and_roundtrip_import PASSED   [ 86%]
backend/tests/test_search.py::test_search_concepts PASSED                [ 89%]
backend/tests/test_search.py::test_search_error_messages PASSED          [ 92%]
backend/tests/test_search.py::test_search_notebooks_content PASSED       [ 94%]
backend/tests/test_search.py::test_web_search_endpoint PASSED            [ 97%]
backend/tests/test_snippets.py::test_snippet_crud PASSED                 [100%]
======================= 38 passed in 8.17s ========================
```

---

## 🛠️ Diagnostics & Troubleshooting FAQ

### 1. Run Environment Diagnostics
If you experience any issues with local interpreters or execution compilers, run:
```bash
devnote doctor
```
This inspects your Python version, Node.js installation, SQLite permissions, PDF font engines, and active network interfaces.

### 2. Port Already in Use (`Errno 48: Address already in use`)
If port 8000 is occupied by another application, launch DevNote on an alternative port:
```bash
devnote start --port 8080
```

### 3. iPad Pairing Fails with `401 Unauthorized`
When DevNote listens on all interfaces (`--host 0.0.0.0`), token security is enforced automatically.
- Check the terminal output from `devnote start` for your unique access token.
- Navigate to the generated LAN URL (`http://<YOUR_IP>:<PORT>?token=<TOKEN>`) on iPad Safari.
- Alternatively, include the header `Authorization: Bearer <TOKEN>` in your requests.

### 4. JavaScript Execution Requires Node.js
Python 3 execution works out of the box using your active Python binary. For executing JavaScript cells, ensure Node.js is installed on your host system:
```bash
# macOS
brew install node

# Ubuntu / Debian
sudo apt-get install -y nodejs
```

---

## 📄 License

DevNote is distributed under the **MIT License**. Free for personal, educational, and commercial use.
# DevNotes
