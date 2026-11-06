from devnote.app.routers.notebooks import router as notebooks_router
from devnote.app.routers.execution import router as execution_router
from devnote.app.routers.pdf import router as pdf_router, pdf_compat_router
from devnote.app.routers.search import router as search_router
from devnote.app.routers.snippets import router as snippets_router
from devnote.app.routers.news import router as news_router
from devnote.app.routers.llm import router as llm_router

__all__ = [
    "notebooks_router",
    "execution_router",
    "pdf_router",
    "pdf_compat_router",
    "search_router",
    "snippets_router",
    "news_router",
    "llm_router",
]
