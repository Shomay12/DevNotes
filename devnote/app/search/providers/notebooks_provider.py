import uuid
from typing import List, Dict, Any, Optional
from devnote.app.database import SessionLocal
from devnote.app.models.notebook import Notebook
from devnote.app.models.snippet import Snippet
from devnote.app.schemas.search import SearchResultItem
from devnote.app.search.base_provider import BaseSearchProvider

class NotebooksSearchProvider(BaseSearchProvider):
    id = "notebooks"
    name = "Workspace Notebooks & Snippets"
    description = "Searches inside your local notebooks, text blocks, code cells, and saved snippets"
    category = "workspace"
    is_online = False
    requires_api_key = False

    async def search(self, query: str, filters: Optional[Dict[str, Any]] = None) -> List[SearchResultItem]:
        q = query.strip().lower()
        if not q:
            return []

        results: List[SearchResultItem] = []
        db = SessionLocal()
        try:
            # 1. Search in user's notebooks
            notebooks = db.query(Notebook).filter(Notebook.is_archived == False).all()
            for nb in notebooks:
                # Check title or description
                if q in nb.title.lower() or (nb.description and q in nb.description.lower()):
                    results.append(SearchResultItem(
                        id=f"nb-{nb.id}",
                        title=f"Notebook: {nb.title}",
                        category="notebook",
                        snippet=nb.description or f"Matches notebook title '{nb.title}'",
                        source="Local Workspace Notebook",
                        url=f"#notebook-{nb.id}",
                        notebook_id=nb.id,
                        tags=nb.tags or [],
                        metadata={"tags": nb.tags}
                    ))
                    continue

                # Check inside notebook blocks
                if isinstance(nb.blocks, list):
                    for b in nb.blocks:
                        b_text = ""
                        b_type = b.get("type", "")
                        b_code = None
                        if b_type == "code":
                            b_text = b.get("code", "")
                            b_code = b.get("code", "")
                        else:
                            b_text = b.get("content", "")

                        if q in b_text.lower():
                            snip = b_text.replace("\n", " ")[:160] + "..."
                            results.append(SearchResultItem(
                                id=f"nb-block-{b.get('id', uuid.uuid4().hex)}",
                                title=f"{nb.title} › {b_type.capitalize()}",
                                category="notebook",
                                snippet=snip,
                                code=b_code,
                                language=b.get("language"),
                                source=f"Notebook: {nb.title}",
                                url=f"#notebook-{nb.id}",
                                notebook_id=nb.id,
                                block_id=b.get("id"),
                                tags=nb.tags or []
                            ))
                            break

            # 2. Search in Snippets
            snippets = db.query(Snippet).all()
            for s in snippets:
                if q in s.title.lower() or q in s.code.lower() or (s.description and q in s.description.lower()):
                    results.append(SearchResultItem(
                        id=f"snip-{s.id}",
                        title=f"Snippet: {s.title}",
                        category="snippet",
                        snippet=s.description or f"Reusable {s.language} snippet",
                        code=s.code,
                        language=s.language,
                        source="Code Snippet Library",
                        url="#snippets",
                        tags=s.tags or []
                    ))
        finally:
            db.close()

        return results
