import httpx
from typing import List, Dict, Any, Optional
from backend.app.schemas.search import SearchResultItem
from backend.app.search.base_provider import BaseSearchProvider

CURATED_DOCUMENTATION: List[Dict[str, Any]] = [
    # Python Core & Standard Library
    {
        "id": "doc-py-decorators",
        "title": "Python Decorators Syntax and functools.wraps",
        "category": "doc",
        "snippet": "Decorators dynamically alter the functionality of a function, method, or class without having to directly use subclasses or modify source code.",
        "code": "import functools\n\ndef bold_decorator(fn):\n    @functools.wraps(fn)\n    def wrapper(*args, **kwargs):\n        return f'<b>{fn(*args, **kwargs)}</b>'\n    return wrapper\n\n@bold_decorator\ndef greet(name):\n    return f'Hello {name}'\n\nprint(greet('Developer'))",
        "language": "python",
        "framework": "python",
        "source": "Python 3 Documentation",
        "url": "https://docs.python.org/3/glossary.html#term-decorator",
        "tags": ["python", "decorators", "functions", "metaprogramming"]
    },
    {
        "id": "doc-py-generators",
        "title": "Python Generator Expressions and Yield",
        "category": "doc",
        "snippet": "Generators provide lazy evaluation over collections. The yield statement suspends function execution and yields a value back to the caller while maintaining state.",
        "code": "def fibonacci(limit):\n    a, b = 0, 1\n    while a < limit:\n        yield a\n        a, b = b, a + b\n\nprint(list(fibonacci(50)))",
        "language": "python",
        "framework": "python",
        "source": "Python Language Reference",
        "url": "https://docs.python.org/3/reference/expressions.html#yield-expressions",
        "tags": ["python", "generators", "yield", "iteration"]
    },
    {
        "id": "doc-py-asyncio",
        "title": "Python asyncio — Asynchronous I/O and Event Loops",
        "category": "doc",
        "snippet": "asyncio is a library to write concurrent code using the async/await syntax. It powers high-performance network and web-servers, database connection libraries, and distributed queues.",
        "code": "import asyncio\n\nasync def fetch_item(item_id: int):\n    await asyncio.sleep(0.05)\n    return f'Item {item_id}'\n\nasync def main():\n    results = await asyncio.gather(*(fetch_item(i) for i in range(5)))\n    print('Fetched:', results)\n\nasyncio.run(main())",
        "language": "python",
        "framework": "python",
        "source": "Python asyncio Documentation",
        "url": "https://docs.python.org/3/library/asyncio.html",
        "tags": ["python", "async", "asyncio", "concurrency"]
    },
    {
        "id": "doc-py-contextlib",
        "title": "Python contextlib — Utilities for with-statement contexts",
        "category": "doc",
        "snippet": "Provides utilities for common tasks involving the with statement, such as @contextmanager to construct context managers without writing __enter__ and __exit__ methods.",
        "code": "from contextlib import contextmanager\n\n@contextmanager\ndef file_open(filename, mode='r'):\n    f = open(filename, mode)\n    try:\n        yield f\n    finally:\n        f.close()",
        "language": "python",
        "framework": "python",
        "source": "Python contextlib Reference",
        "url": "https://docs.python.org/3/library/contextlib.html",
        "tags": ["python", "context-managers", "with", "resources"]
    },
    {
        "id": "doc-py-typing",
        "title": "Python typing — Support for type hints and static type checkers",
        "category": "doc",
        "snippet": "Type hints provide runtime access to type annotations and empower tools like mypy, Pyright, and Pydantic for validation and editor autocompletion.",
        "code": "from typing import List, Dict, Optional, Union\n\ndef parse_headers(headers: Dict[str, Union[str, int]]) -> Optional[str]:\n    auth = headers.get('Authorization')\n    return str(auth) if auth else None",
        "language": "python",
        "framework": "python",
        "source": "Python typing Reference",
        "url": "https://docs.python.org/3/library/typing.html",
        "tags": ["python", "typing", "type-hints", "mypy"]
    },

    # FastAPI Documentation
    {
        "id": "doc-fastapi-quickstart",
        "title": "FastAPI First Steps & Routing Tutorial",
        "category": "doc",
        "snippet": "FastAPI is a modern, high-performance web framework for building APIs with Python 3.8+ based on standard Python type hints.",
        "code": "from fastapi import FastAPI\n\napp = FastAPI(title='My API')\n\n@app.get('/')\ndef read_root():\n    return {'message': 'Hello Developer', 'status': 'online'}",
        "language": "python",
        "framework": "fastapi",
        "source": "FastAPI Official Documentation",
        "url": "https://fastapi.tiangolo.com/tutorial/first-steps/",
        "tags": ["fastapi", "python", "api", "routing"]
    },
    {
        "id": "doc-fastapi-dependencies",
        "title": "FastAPI Dependency Injection System (Depends)",
        "category": "doc",
        "snippet": "FastAPI provides an extensible Dependency Injection system that simplifies authentication, database session management, and shared logic across endpoints.",
        "code": "from fastapi import Depends, FastAPI, Header, HTTPException\n\napp = FastAPI()\n\ndef verify_token(x_token: str = Header(...)):\n    if x_token != 'devnote-secret':\n        raise HTTPException(status_code=400, detail='Invalid token')\n    return x_token\n\n@app.get('/protected')\ndef read_protected(token: str = Depends(verify_token)):\n    return {'status': 'authorized'}",
        "language": "python",
        "framework": "fastapi",
        "source": "FastAPI Dependencies Guide",
        "url": "https://fastapi.tiangolo.com/tutorial/dependencies/",
        "tags": ["fastapi", "dependency-injection", "security", "auth"]
    },
    {
        "id": "doc-fastapi-pydantic-validation",
        "title": "FastAPI Request Body and Pydantic Model Validation",
        "category": "doc",
        "snippet": "Declare JSON request schemas using Pydantic models with automatic data parsing, validation, and interactive OpenAPI documentation.",
        "code": "from typing import Optional, List\nfrom pydantic import BaseModel, Field\nfrom fastapi import FastAPI\n\nclass Item(BaseModel):\n    name: str\n    price: float = Field(gt=0, description='Price must be positive')\n    tags: List[str] = []\n\napp = FastAPI()\n\n@app.post('/items')\ndef create_item(item: Item):\n    return {'item_created': item.model_dump()}",
        "language": "python",
        "framework": "fastapi",
        "source": "FastAPI Body Validation",
        "url": "https://fastapi.tiangolo.com/tutorial/body/",
        "tags": ["fastapi", "pydantic", "validation", "schemas"]
    },

    # MDN JavaScript / Web APIs
    {
        "id": "doc-mdn-promises",
        "title": "MDN: JavaScript Promises and Promise.all()",
        "category": "doc",
        "snippet": "A Promise is an object representing the eventual completion or failure of an asynchronous operation and its resulting value.",
        "code": "const p1 = Promise.resolve(3);\nconst p2 = new Promise((resolve) => setTimeout(resolve, 100, 'quick'));\n\nPromise.all([p1, p2]).then(values => {\n    console.log('Resolved all:', values);\n});",
        "language": "javascript",
        "framework": "javascript",
        "source": "MDN Web Docs",
        "url": "https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Promise",
        "tags": ["javascript", "promises", "async", "mdn"]
    },
    {
        "id": "doc-mdn-closures",
        "title": "MDN: JavaScript Closures and Lexical Scope",
        "category": "doc",
        "snippet": "A closure gives an inner function access to an outer function's scope even after the outer function has finished executing.",
        "code": "function makeAdder(x) {\n    return function(y) {\n        return x + y;\n    };\n}\n\nconst add5 = makeAdder(5);\nconsole.log(add5(10)); // 15",
        "language": "javascript",
        "framework": "javascript",
        "source": "MDN Web Docs",
        "url": "https://developer.mozilla.org/en-US/docs/Web/JavaScript/Closures",
        "tags": ["javascript", "closures", "scope", "functions"]
    },
    {
        "id": "doc-mdn-canvas",
        "title": "MDN: HTML5 Canvas API and 2D Context",
        "category": "doc",
        "snippet": "Provides an API for drawing 2D graphics using JavaScript and the <canvas> element. Ideal for data visualization, animations, and handwritten notes.",
        "code": "const canvas = document.createElement('canvas');\nconst ctx = canvas.getContext('2d');\nctx.lineWidth = 2;\nctx.strokeStyle = '#2563eb';\nctx.beginPath();\nctx.moveTo(10, 10);\nctx.lineTo(100, 100);\nctx.stroke();",
        "language": "javascript",
        "framework": "javascript",
        "source": "MDN Web Docs",
        "url": "https://developer.mozilla.org/en-US/docs/Web/API/Canvas_API",
        "tags": ["javascript", "canvas", "graphics", "pointer"]
    },
    {
        "id": "doc-mdn-pointer-events",
        "title": "MDN: Pointer Events API & Apple Pencil Stylus Pressure",
        "category": "doc",
        "snippet": "Unified input handling for mouse, touch, and stylus pen events, including e.pressure and e.pointerType.",
        "code": "window.addEventListener('pointerdown', (e) => {\n    if (e.pointerType === 'pen') {\n        console.log(`Stylus pressure: ${e.pressure}, tiltX: ${e.tiltX}`);\n    }\n});",
        "language": "javascript",
        "framework": "javascript",
        "source": "MDN Web Docs",
        "url": "https://developer.mozilla.org/en-US/docs/Web/API/Pointer_events",
        "tags": ["javascript", "pointer-events", "stylus", "touch"]
    },

    # Docker Documentation
    {
        "id": "doc-docker-compose",
        "title": "Docker Compose File Reference v3",
        "category": "doc",
        "snippet": "Docker Compose is a tool for defining and running multi-container Docker applications using a YAML configuration file.",
        "code": "version: '3.8'\nservices:\n  web:\n    build: .\n    ports:\n      - '8000:8000'\n    volumes:\n      - ./storage:/app/storage\n    restart: unless-stopped",
        "language": "yaml",
        "framework": "docker",
        "source": "Docker Documentation",
        "url": "https://docs.docker.com/compose/compose-file/",
        "tags": ["docker", "compose", "containers", "devops"]
    },
    {
        "id": "doc-docker-multistage",
        "title": "Docker Multi-stage Builds for Lean Images",
        "category": "doc",
        "snippet": "Multi-stage builds allow you to use multiple FROM statements in your Dockerfile to selectively copy artifacts from one stage to another, dramatically reducing final image size.",
        "code": "FROM python:3.12-slim AS builder\nWORKDIR /app\nCOPY requirements.txt .\nRUN pip wheel --no-cache-dir --wheel-dir /wheels -r requirements.txt\n\nFROM python:3.12-slim\nWORKDIR /app\nCOPY --from=builder /wheels /wheels\nRUN pip install --no-index --find-links=/wheels /wheels/*",
        "language": "dockerfile",
        "framework": "docker",
        "source": "Docker Documentation",
        "url": "https://docs.docker.com/build/building/multi-stage/",
        "tags": ["docker", "dockerfile", "optimization", "containers"]
    },

    # Git Documentation
    {
        "id": "doc-git-interactive-rebase",
        "title": "Git Interactive Rebase (git rebase -i)",
        "category": "doc",
        "snippet": "Interactive rebasing lets you rewrite, edit, squash, reword, and reorder commits before merging or pushing upstream.",
        "code": "# Rebase last 3 commits interactively\ngit rebase -i HEAD~3\n\n# Commands in editor:\n# pick: use commit\n# squash: meld into previous commit\n# reword: change commit message",
        "language": "bash",
        "framework": "git",
        "source": "Git SCM Reference",
        "url": "https://git-scm.com/docs/git-rebase",
        "tags": ["git", "rebase", "version-control", "commits"]
    },

    # PostgreSQL Documentation
    {
        "id": "doc-postgres-indexes",
        "title": "PostgreSQL Index Types: B-Tree, Hash, GIN, GiST",
        "category": "doc",
        "snippet": "Indexes are a common way to enhance database performance. PostgreSQL supports B-Tree (default for comparisons), GIN (for JSONB and arrays), and GiST.",
        "code": "CREATE INDEX idx_users_email ON users(email);\nCREATE INDEX idx_notebooks_tags ON notebooks USING gin(tags);\nCREATE INDEX idx_docs_fts ON documents USING gin(to_tsvector('english', content));",
        "language": "sql",
        "framework": "postgresql",
        "source": "PostgreSQL Documentation",
        "url": "https://www.postgresql.org/docs/current/indexes-types.html",
        "tags": ["postgresql", "sql", "indexes", "performance"]
    }
]

class DevDocsProvider(BaseSearchProvider):
    id = "devdocs"
    name = "DevDocs & Official Docs"
    description = "Searches official documentation from Python, MDN, FastAPI, Docker, PostgreSQL, and Git"
    category = "documentation"
    is_online = True
    requires_api_key = False

    async def search(self, query: str, filters: Optional[Dict[str, Any]] = None) -> List[SearchResultItem]:
        q = query.strip().lower()
        if not q:
            return [SearchResultItem(**item) for item in CURATED_DOCUMENTATION[:8]]

        matches: List[SearchResultItem] = []
        target_lang = (filters.get("language") or "").lower() if filters else ""
        target_fw = (filters.get("framework") or "").lower() if filters else ""

        # Search curated offline/pre-indexed entries first
        for doc in CURATED_DOCUMENTATION:
            if target_lang and doc.get("language", "").lower() != target_lang:
                continue
            if target_fw and doc.get("framework", "").lower() != target_fw:
                continue

            searchable = f"{doc['title']} {doc['snippet']} {doc.get('code', '')} {' '.join(doc.get('tags', []))}".lower()
            if q in searchable or any(term in searchable for term in q.split()):
                matches.append(SearchResultItem(**doc))

        # Try live query to DevDocs search index if network available
        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                res = await client.get(f"https://devdocs.io/docs.json")
                if res.status_code == 200:
                    docs_list = res.json()
                    # Filter relevant docs matching query
                    for item in docs_list:
                        name = item.get("name", "")
                        slug = item.get("slug", "")
                        if q in name.lower() or q in slug.lower():
                            matches.append(SearchResultItem(
                                id=f"devdocs-{slug}",
                                title=f"DevDocs: {name} Documentation",
                                category="doc",
                                snippet=f"Official API reference and developer documentation index for {name} ({item.get('release', 'latest')}).",
                                source="DevDocs.io",
                                url=f"https://devdocs.io/{slug}/",
                                tags=[slug, "devdocs"]
                            ))
                            if len(matches) >= 15:
                                break
        except Exception:
            # Network unavailable in sandbox or offline mode; curated offline docs ensure high quality results!
            pass

        return matches
