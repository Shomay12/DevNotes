import html
import re
import httpx
from typing import List, Dict, Any, Optional
from backend.app.schemas.search import SearchResultItem
from backend.app.search.base_provider import BaseSearchProvider

CURATED_STACKOVERFLOW_SOLUTIONS: List[Dict[str, Any]] = [
    {
        "id": "so-err-py-torch-modulenotfound",
        "title": "ModuleNotFoundError: No module named 'torch' in Python / Virtual Environment",
        "category": "stackoverflow",
        "snippet": "This error occurs when PyTorch is not installed in the currently activated Python interpreter or virtual environment. Install via pip with the appropriate CUDA/CPU wheel.",
        "code": "# Fix: Activate environment and install PyTorch\npip install torch torchvision torchaudio\n\n# Or for CPU-only in lightweight environments:\npip install torch --index-url https://download.pytorch.org/whl/cpu",
        "language": "python",
        "framework": "pytorch",
        "source": "Stack Overflow",
        "url": "https://stackoverflow.com/questions/52219468/modulenotfounderror-no-module-named-torch",
        "score": 384,
        "is_answered": True,
        "tags": ["python", "pytorch", "pip", "virtualenv"]
    },
    {
        "id": "so-err-py-nonetype-subscriptable",
        "title": "TypeError: 'NoneType' object is not subscriptable in Python",
        "category": "stackoverflow",
        "snippet": "Raised when indexing an expression with [key] or [index] that returned None. Frequently happens when a function like list.sort() (which returns None) is chained, or an API call returns None.",
        "code": "# Problem:\nres = [3, 1, 2].sort()\n# val = res[0] # TypeError!\n\n# Solution:\nitems = [3, 1, 2]\nitems.sort()\nval = items[0] if items else None\nprint('Safe item:', val)",
        "language": "python",
        "framework": "python",
        "source": "Stack Overflow",
        "url": "https://stackoverflow.com/questions/13675685/typeerror-nonetype-object-is-not-subscriptable",
        "score": 752,
        "is_answered": True,
        "tags": ["python", "typeerror", "null", "indexing"]
    },
    {
        "id": "so-err-fastapi-cors",
        "title": "How to resolve CORS error 'Access-Control-Allow-Origin' in FastAPI",
        "category": "stackoverflow",
        "snippet": "Cross-Origin Resource Sharing (CORS) blocks browsers from making requests to a different domain/port. Add FastAPI's CORSMiddleware with allowed origins.",
        "code": "from fastapi import FastAPI\nfrom fastapi.middleware.cors import CORSMiddleware\n\napp = FastAPI()\n\napp.add_middleware(\n    CORSMiddleware,\n    allow_origins=['*'],\n    allow_credentials=True,\n    allow_methods=['*'],\n    allow_headers=['*'],\n)",
        "language": "python",
        "framework": "fastapi",
        "source": "Stack Overflow",
        "url": "https://stackoverflow.com/questions/65632314/how-to-solve-cors-in-fastapi",
        "score": 420,
        "is_answered": True,
        "tags": ["fastapi", "cors", "http", "api"]
    },
    {
        "id": "so-err-js-cannot-read-properties",
        "title": "TypeError: Cannot read properties of undefined (reading 'map') in JavaScript / React",
        "category": "stackoverflow",
        "snippet": "This occurs when trying to invoke .map() or access attributes on a variable before asynchronous data has finished loading, or when the initial state is undefined.",
        "code": "// Solution 1: Optional chaining with nullish fallback\nconst list = data?.items ?? [];\nconst rendered = list.map(item => item.name);\n\n// Solution 2: Default parameter in component\nfunction ListDisplay({ items = [] }) {\n    return items.map(i => i.id);\n}",
        "language": "javascript",
        "framework": "react",
        "source": "Stack Overflow",
        "url": "https://stackoverflow.com/questions/69080597/typeerror-cannot-read-properties-of-undefined-reading-map",
        "score": 612,
        "is_answered": True,
        "tags": ["javascript", "react", "typeerror", "arrays"]
    },
    {
        "id": "so-err-docker-permission-denied",
        "title": "Docker: Got permission denied while trying to connect to the Docker daemon socket",
        "category": "stackoverflow",
        "snippet": "The docker daemon binds to a Unix socket owned by root. Non-root users must be added to the 'docker' usergroup.",
        "code": "# Add user to docker group\nsudo usermod -aG docker $USER\n# Apply group membership\nnewgrp docker\n# Verify\ndocker ps",
        "language": "bash",
        "framework": "docker",
        "source": "Stack Overflow",
        "url": "https://stackoverflow.com/questions/48957195/how-to-fix-docker-got-permission-denied-issue",
        "score": 890,
        "is_answered": True,
        "tags": ["docker", "linux", "permissions", "daemon"]
    },
    {
        "id": "so-err-git-detached-head",
        "title": "How to fix a 'detached HEAD' state in Git",
        "category": "stackoverflow",
        "snippet": "A detached HEAD means you have checked out a specific commit rather than a branch tip. Any new commits will not belong to a branch unless saved.",
        "code": "# Create and switch to a new branch preserving your commits:\ngit switch -c temp-saved-work\n\n# Or discard detached commits and return to main:\ngit switch main",
        "language": "bash",
        "framework": "git",
        "source": "Stack Overflow",
        "url": "https://stackoverflow.com/questions/10228760/how-do-i-fix-a-git-detached-head",
        "score": 1150,
        "is_answered": True,
        "tags": ["git", "branch", "head", "version-control"]
    }
]

class StackOverflowProvider(BaseSearchProvider):
    id = "stackoverflow"
    name = "Stack Overflow"
    description = "Searches developer questions, error fixes, and debugging discussions via Stack Exchange API"
    category = "q_and_a"
    is_online = True
    requires_api_key = False

    async def search(self, query: str, filters: Optional[Dict[str, Any]] = None) -> List[SearchResultItem]:
        q = query.strip()
        if not q:
            return [SearchResultItem(**item) for item in CURATED_STACKOVERFLOW_SOLUTIONS[:6]]

        results: List[SearchResultItem] = []
        target_lang = (filters.get("language") or "").lower() if filters else ""

        # 1. First, search curated solutions for exact error fixes
        for item in CURATED_STACKOVERFLOW_SOLUTIONS:
            if target_lang and item.get("language", "").lower() != target_lang:
                continue
            text = f"{item['title']} {item['snippet']} {' '.join(item.get('tags', []))}".lower()
            if any(term in text for term in q.lower().split()):
                results.append(SearchResultItem(**item))

        # 2. Query official Stack Exchange API 2.3
        try:
            params = {
                "order": "desc",
                "sort": "relevance",
                "site": "stackoverflow",
                "pagesize": 8,
                "q": q
            }
            if target_lang:
                params["tagged"] = target_lang

            async with httpx.AsyncClient(timeout=4.0) as client:
                res = await client.get(
                    "https://api.stackexchange.com/2.3/search/advanced",
                    params=params,
                    headers={"User-Agent": "DevNote-DevSearch/1.1 (Developer Technical Notebook)"}
                )

                if res.status_code == 200:
                    data = res.json()
                    items = data.get("items", [])
                    for q_item in items:
                        title = html.unescape(q_item.get("title", ""))
                        tags = q_item.get("tags", [])
                        score = q_item.get("score", 0)
                        is_answered = q_item.get("is_answered", False)
                        link = q_item.get("link", "")
                        q_id = q_item.get("question_id", "")

                        # Construct clean snippet
                        snippet = f"Stack Overflow discussion with {score} votes ({'Accepted answer' if is_answered else 'Unaccepted'}). Tags: {', '.join(tags[:4])}"

                        results.append(SearchResultItem(
                            id=f"so-{q_id}",
                            title=title,
                            category="stackoverflow",
                            snippet=snippet,
                            source="Stack Overflow",
                            url=link,
                            score=score,
                            is_answered=is_answered,
                            tags=tags,
                            metadata={"view_count": q_item.get("view_count", 0)}
                        ))
        except Exception:
            # Fallback offline or sandbox mode: curated results already populated
            pass

        return results
