import os
import httpx
from typing import List, Dict, Any, Optional
from devnote.app.schemas.search import SearchResultItem
from devnote.app.search.base_provider import BaseSearchProvider

CURATED_GITHUB_REPOSITORIES: List[Dict[str, Any]] = [
    {
        "id": "gh-fastapi",
        "title": "tiangolo/fastapi",
        "category": "github",
        "snippet": "FastAPI framework, high performance, easy to learn, fast to code, ready for production. Built with Starlette and Pydantic.",
        "code": "from fastapi import FastAPI\napp = FastAPI()\n\n@app.get('/health')\ndef health():\n    return {'status': 'healthy'}",
        "language": "python",
        "framework": "fastapi",
        "source": "GitHub",
        "url": "https://github.com/tiangolo/fastapi",
        "stars": 75000,
        "date": "2024",
        "tags": ["python", "fastapi", "api", "pydantic", "async"]
    },
    {
        "id": "gh-python-algorithms",
        "title": "TheAlgorithms/Python",
        "category": "github",
        "snippet": "All Algorithms implemented in Python — Education resource for data structures, sorting, graphs, dynamic programming, and search algorithms.",
        "code": "def quick_sort(arr):\n    if len(arr) <= 1:\n        return arr\n    pivot = arr[len(arr) // 2]\n    left = [x for x in arr if x < pivot]\n    middle = [x for x in arr if x == pivot]\n    right = [x for x in arr if x > pivot]\n    return quick_sort(left) + middle + quick_sort(right)\n\nprint(quick_sort([3, 6, 8, 10, 1, 2, 1]))",
        "language": "python",
        "framework": "python",
        "source": "GitHub",
        "url": "https://github.com/TheAlgorithms/Python",
        "stars": 182000,
        "date": "2024",
        "tags": ["python", "algorithms", "data-structures", "sorting"]
    },
    {
        "id": "gh-javascript-algorithms",
        "title": "trekhleb/javascript-algorithms",
        "category": "github",
        "snippet": "Algorithms and data structures implemented in JavaScript with explanations and links to further readings.",
        "code": "function binarySearch(sortedArray, seekElement) {\n    let startIndex = 0;\n    let endIndex = sortedArray.length - 1;\n    while (startIndex <= endIndex) {\n        const middleIndex = startIndex + Math.floor((endIndex - startIndex) / 2);\n        if (sortedArray[middleIndex] === seekElement) return middleIndex;\n        if (sortedArray[middleIndex] < seekElement) startIndex = middleIndex + 1;\n        else endIndex = middleIndex - 1;\n    }\n    return -1;\n}\n\nconsole.log(binarySearch([1, 3, 5, 7, 9], 7));",
        "language": "javascript",
        "framework": "javascript",
        "source": "GitHub",
        "url": "https://github.com/trekhleb/javascript-algorithms",
        "stars": 185000,
        "date": "2024",
        "tags": ["javascript", "algorithms", "data-structures"]
    },
    {
        "id": "gh-pytorch",
        "title": "pytorch/pytorch",
        "category": "github",
        "snippet": "Tensors and Dynamic neural networks in Python with strong GPU acceleration. Deep learning framework for research and production.",
        "code": "import torch\nx = torch.rand(5, 3)\nprint('PyTorch Tensor:\\n', x)",
        "language": "python",
        "framework": "pytorch",
        "source": "GitHub",
        "url": "https://github.com/pytorch/pytorch",
        "stars": 85000,
        "date": "2024",
        "tags": ["pytorch", "machine-learning", "ai", "deep-learning"]
    },
    {
        "id": "gh-flutter",
        "title": "flutter/flutter",
        "category": "github",
        "snippet": "Flutter makes it easy and fast to build beautiful apps for mobile and beyond. Cross-platform UI toolkit developed by Google.",
        "code": "import 'package:flutter/material.dart';\nvoid main() => runApp(const MaterialApp(home: Scaffold(body: Center(child: Text('Hello Flutter')))));",
        "language": "dart",
        "framework": "flutter",
        "source": "GitHub",
        "url": "https://github.com/flutter/flutter",
        "stars": 165000,
        "date": "2024",
        "tags": ["dart", "flutter", "mobile", "cross-platform"]
    }
]

class GitHubProvider(BaseSearchProvider):
    id = "github"
    name = "GitHub"
    description = "Searches open-source repositories, implementations, code samples, and releases"
    category = "code"
    is_online = True
    requires_api_key = False

    async def search(self, query: str, filters: Optional[Dict[str, Any]] = None) -> List[SearchResultItem]:
        q = query.strip()
        if not q:
            return [SearchResultItem(**item) for item in CURATED_GITHUB_REPOSITORIES[:5]]

        results: List[SearchResultItem] = []
        target_lang = (filters.get("language") or "").lower() if filters else ""

        # 1. Search curated high-quality repositories & code snippets
        for repo in CURATED_GITHUB_REPOSITORIES:
            if target_lang and repo.get("language", "").lower() != target_lang:
                continue
            text = f"{repo['title']} {repo['snippet']} {' '.join(repo.get('tags', []))}".lower()
            if any(term in text for term in q.lower().split()):
                results.append(SearchResultItem(**repo))

        # 2. Query official GitHub API
        try:
            gh_token = os.environ.get("GITHUB_TOKEN", "").strip()
            headers = {
                "Accept": "application/vnd.github.v3+json",
                "User-Agent": "DevNote-DevSearch/1.1 (Developer Technical Notebook)"
            }
            if gh_token:
                headers["Authorization"] = f"token {gh_token}"

            search_query = q
            if target_lang:
                search_query += f" language:{target_lang}"

            async with httpx.AsyncClient(timeout=4.0) as client:
                res = await client.get(
                    "https://api.github.com/search/repositories",
                    params={"q": search_query, "sort": "stars", "order": "desc", "per_page": 8},
                    headers=headers
                )

                if res.status_code == 200:
                    data = res.json()
                    items = data.get("items", [])
                    for repo in items:
                        full_name = repo.get("full_name", "")
                        desc = repo.get("description") or "No description provided."
                        lang = repo.get("language")
                        stars = repo.get("stargazers_count", 0)
                        html_url = repo.get("html_url", "")
                        updated_at = repo.get("updated_at", "")[:10]
                        topics = repo.get("topics", [])

                        results.append(SearchResultItem(
                            id=f"gh-{repo.get('id', full_name)}",
                            title=full_name,
                            category="github",
                            snippet=desc,
                            language=lang.lower() if lang else None,
                            source="GitHub",
                            url=html_url,
                            stars=stars,
                            date=updated_at,
                            tags=topics,
                            metadata={"forks": repo.get("forks_count", 0), "license": repo.get("license", {}).get("name") if repo.get("license") else None}
                        ))
        except Exception:
            # Fallback offline or sandbox mode: curated results already populated
            pass

        return results
