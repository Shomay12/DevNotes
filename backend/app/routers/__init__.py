from backend.app.routers.notebooks import router as notebooks_router
from backend.app.routers.execution import router as execution_router
from backend.app.routers.pdf import router as pdf_router
from backend.app.routers.search import router as search_router
from backend.app.routers.snippets import router as snippets_router

__all__ = [
    "notebooks_router",
    "execution_router",
    "pdf_router",
    "search_router",
    "snippets_router",
]
