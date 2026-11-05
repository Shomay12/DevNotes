import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from devnote.app.config import (
    BASE_DIR,
    FRONTEND_DIR,
    STORAGE_DIR,
    EXPORTS_DIR,
    UPLOADS_DIR,
    DEVNOTE_EDITION,
    DEVNOTE_VERSION,
    DEVNOTE_AUTH_TOKEN,
    DEVNOTE_HOST,
    DEVNOTE_PORT
)
from devnote.app.database import engine, Base, SessionLocal
from devnote.app.models.notebook import Notebook
from devnote.app.models.snippet import Snippet
from devnote.app.services.notebook_service import NotebookService, get_default_blocks
from devnote.app.routers import (
    notebooks_router,
    execution_router,
    pdf_router,
    pdf_compat_router,
    search_router,
    snippets_router,
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize DB schema
    Base.metadata.create_all(bind=engine)

    # Seed initial data if empty
    db = SessionLocal()
    try:
        notebook_count = db.query(Notebook).count()
        if notebook_count == 0:
            welcome_notebook = Notebook(
                id="default-welcome-notebook",
                title="Getting Started with DevNote",
                description="Your personal interactive developer notebook & code workspace.",
                tags=["getting-started", "python", "quickstart"],
                blocks=get_default_blocks(),
                is_pinned=True,
                is_archived=False,
                version=1
            )
            db.add(welcome_notebook)

        snippet_count = db.query(Snippet).count()
        if snippet_count == 0:
            sample_snippets = [
                Snippet(
                    title="Python QuickSort Algorithm",
                    language="python",
                    code="def quicksort(arr):\n    if len(arr) <= 1:\n        return arr\n    pivot = arr[len(arr) // 2]\n    left = [x for x in arr if x < pivot]\n    middle = [x for x in arr if x == pivot]\n    right = [x for x in arr if x > pivot]\n    return quicksort(left) + middle + quicksort(right)\n\nprint(quicksort([3, 6, 8, 10, 1, 2, 1]))",
                    description="Recursive implementation of quicksort in Python",
                    tags=["algorithms", "sorting"]
                ),
                Snippet(
                    title="Async Fetch JSON in JS",
                    language="javascript",
                    code="async function fetchJSON(url) {\n    const res = await fetch(url);\n    if (!res.ok) throw new Error(`HTTP ${res.status}`);\n    return await res.json();\n}\n\nconsole.log('fetchJSON helper ready');",
                    description="Clean async helper to fetch and parse JSON",
                    tags=["web", "fetch", "async"]
                ),
                Snippet(
                    title="FastAPI Route Template",
                    language="python",
                    code="from fastapi import APIRouter, HTTPException\n\nrouter = APIRouter(prefix='/api/items')\n\n@router.get('/{item_id}')\ndef get_item(item_id: int):\n    return {'item_id': item_id, 'status': 'active'}",
                    description="Standard APIRouter template for microservices",
                    tags=["fastapi", "backend"]
                )
            ]
            db.add_all(sample_snippets)

        db.commit()
    except Exception as e:
        print(f"Startup seed error: {e}")
        db.rollback()
    finally:
        db.close()

    yield

app = FastAPI(
    title="DevNote API",
    description="Interactive Developer Notebook & Coding Workspace",
    version="1.0.0",
    lifespan=lifespan
)

# Enable CORS for local cross-origin if needed
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Network Security Authentication Middleware
@app.middleware("http")
async def network_security_auth_middleware(request: Request, call_next):
    # Only enforce when DEVNOTE_AUTH_TOKEN is configured
    token = DEVNOTE_AUTH_TOKEN
    if token and request.url.path.startswith("/api/"):
        # Allow public endpoints
        if request.url.path in ("/api/health", "/api/config"):
            return await call_next(request)

        # Check Authorization header (Bearer <token>) or ?token= query parameter
        auth_header = request.headers.get("Authorization", "")
        query_token = request.query_params.get("token", "")

        is_valid = False
        if auth_header.startswith("Bearer "):
            bearer = auth_header.split("Bearer ", 1)[1].strip()
            if bearer == token:
                is_valid = True
        elif query_token == token:
            is_valid = True

        if not is_valid:
            return JSONResponse(
                status_code=401,
                content={"detail": "Unauthorized: Invalid or missing DevNote access token."}
            )

    return await call_next(request)

# Include API Routers
app.include_router(notebooks_router)
app.include_router(execution_router)
app.include_router(pdf_router)
app.include_router(pdf_compat_router)
app.include_router(search_router)
app.include_router(snippets_router)

# Mount static frontend directories
css_dir = FRONTEND_DIR / "css"
js_dir = FRONTEND_DIR / "js"
assets_dir = FRONTEND_DIR / "assets"
if not assets_dir.exists():
    assets_dir = BASE_DIR / "assets"

if css_dir.exists():
    app.mount("/css", StaticFiles(directory=str(css_dir)), name="css")
if js_dir.exists():
    app.mount("/js", StaticFiles(directory=str(js_dir)), name="js")
if assets_dir.exists():
    app.mount("/assets", StaticFiles(directory=str(assets_dir)), name="assets")

# Mount storage exports for direct preview downloads if needed
app.mount("/storage/exports", StaticFiles(directory=str(EXPORTS_DIR)), name="exports")

@app.get("/api/health")
def health_check():
    return {"status": "ok", "app": "DevNote", "version": DEVNOTE_VERSION, "edition": DEVNOTE_EDITION}

@app.get("/api/config")
def get_app_config():
    return {
        "version": DEVNOTE_VERSION,
        "edition": DEVNOTE_EDITION,
        "auth_required": bool(DEVNOTE_AUTH_TOKEN),
        "host": DEVNOTE_HOST,
        "port": DEVNOTE_PORT
    }

# Root index route
@app.get("/")
def serve_index():
    index_file = FRONTEND_DIR / "index.html"
    if index_file.exists():
        return FileResponse(index_file)
    return JSONResponse({"message": "DevNote Backend API running. Frontend index.html not yet built."})
