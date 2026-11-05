import re
import datetime
from typing import List, Dict, Any, Optional
from sqlalchemy import text
from devnote.app.database import engine, SessionLocal
from devnote.app.models.doc_index import DocIndex
from devnote.app.schemas.search import SearchResultItem
from devnote.app.search.base_provider import BaseSearchProvider

BUNDLED_DOC_PACKS = [
    {
        "id": "python-core",
        "name": "Python 3 Standard Library & Reference",
        "version": "3.12+",
        "description": "Core language syntax, decorators, generators, asyncio, built-ins, and data structures.",
        "category": "language",
        "status": "downloaded",
        "entries": [
            {
                "title": "Python Decorators Syntax & functools.wraps",
                "category": "doc",
                "language": "python",
                "url": "https://docs.python.org/3/glossary.html#term-decorator",
                "content": "A decorator is a callable that returns a callable. Decorators are applied with @decorator syntax to wrap functions or methods.",
                "code": "import functools\n\ndef my_decorator(fn):\n    @functools.wraps(fn)\n    def wrapper(*args, **kwargs):\n        print('Before call')\n        result = fn(*args, **kwargs)\n        print('After call')\n        return result\n    return wrapper\n\n@my_decorator\ndef greet(name):\n    return f'Hello, {name}'\n\nprint(greet('Developer'))"
            },
            {
                "title": "Python Generators and Yield Expressions",
                "category": "doc",
                "language": "python",
                "url": "https://docs.python.org/3/reference/expressions.html#yield-expressions",
                "content": "Generators allow you to declare a function that behaves like an iterator. They yield values lazily one by one.",
                "code": "def count_up_to(max_val):\n    count = 1\n    while count <= max_val:\n        yield count\n        count += 1\n\nfor num in count_up_to(5):\n    print(num, end=' ')\nprint()"
            },
            {
                "title": "Python Asyncio Event Loop & Coroutines",
                "category": "doc",
                "language": "python",
                "url": "https://docs.python.org/3/library/asyncio.html",
                "content": "asyncio is a library to write concurrent code using the async/await syntax. Ideal for asynchronous networking and IO tasks.",
                "code": "import asyncio\n\nasync def fetch_data(task_id: int):\n    await asyncio.sleep(0.05)\n    return f'Result {task_id}'\n\nasync def main():\n    results = await asyncio.gather(*(fetch_data(i) for i in range(3)))\n    print('Gathered:', results)\n\nasyncio.run(main())"
            },
            {
                "title": "Python List & Dict Comprehensions",
                "category": "doc",
                "language": "python",
                "url": "https://docs.python.org/3/tutorial/datastructures.html#list-comprehensions",
                "content": "List comprehensions provide a concise way to create lists from existing iterables with optional filtering.",
                "code": "even_squares = [x**2 for x in range(10) if x % 2 == 0]\nprint('Even squares:', even_squares)\n\nlength_map = {word: len(word) for word in ['python', 'devnote', 'fastapi']}\nprint('Lengths:', length_map)"
            },
            {
                "title": "Python Context Managers & with-statement",
                "category": "doc",
                "language": "python",
                "url": "https://docs.python.org/3/library/contextlib.html",
                "content": "Context managers guarantee deterministic resource cleanup (closing files, releasing locks) using __enter__ and __exit__.",
                "code": "from contextlib import contextmanager\n\n@contextmanager\ndef open_resource(name):\n    print(f'Opening {name}')\n    try:\n        yield f'Resource({name})'\n    finally:\n        print(f'Closing {name}')\n\nwith open_resource('Database') as res:\n    print('Using', res)"
            }
        ]
    },
    {
        "id": "fastapi-docs",
        "name": "FastAPI & Pydantic Documentation",
        "version": "0.110+",
        "description": "FastAPI framework, APIRouter, dependency injection, and Pydantic validation.",
        "category": "framework",
        "status": "downloaded",
        "entries": [
            {
                "title": "FastAPI APIRouter and Route Organization",
                "category": "doc",
                "language": "python",
                "url": "https://fastapi.tiangolo.com/tutorial/bigger-applications/",
                "content": "APIRouter allows organizing FastAPI routes into separate modules, setting common prefixes, tags, and dependencies.",
                "code": "from fastapi import APIRouter\n\nrouter = APIRouter(prefix='/api/v1/items', tags=['items'])\n\n@router.get('/')\ndef get_items():\n    return [{'id': 1, 'name': 'Item 1'}]"
            },
            {
                "title": "FastAPI Dependency Injection (Depends)",
                "category": "doc",
                "language": "python",
                "url": "https://fastapi.tiangolo.com/tutorial/dependencies/",
                "content": "FastAPI's dependency injection system simplifies sharing database connections, security checks, and configuration.",
                "code": "from fastapi import Depends, FastAPI\n\napp = FastAPI()\n\ndef get_db_session():\n    db = {'connection': 'active'}\n    try:\n        yield db\n    finally:\n        pass\n\n@app.get('/users')\ndef list_users(db: dict = Depends(get_db_session)):\n    return {'db_status': db['connection']}"
            },
            {
                "title": "Pydantic BaseModel & Field Validation",
                "category": "doc",
                "language": "python",
                "url": "https://docs.pydantic.dev/latest/concepts/models/",
                "content": "Pydantic defines data schemas with automatic type casting, constraints, and JSON serialization.",
                "code": "from pydantic import BaseModel, Field\n\nclass UserProfile(BaseModel):\n    username: str = Field(min_length=3, max_length=50)\n    email: str\n    is_active: bool = True\n\nuser = UserProfile(username='alice', email='alice@devnote.io')\nprint(user.model_dump())"
            }
        ]
    },
    {
        "id": "javascript-web",
        "name": "MDN JavaScript & Web APIs",
        "version": "ES2023",
        "description": "Modern JavaScript, Promises, Canvas API, Pointer Events, and DOM manipulation.",
        "category": "language",
        "status": "downloaded",
        "entries": [
            {
                "title": "JavaScript Promises & Async/Await",
                "category": "doc",
                "language": "javascript",
                "url": "https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Promise",
                "content": "Promises represent asynchronous values that will be resolved or rejected in the future.",
                "code": "const delay = (ms) => new Promise(resolve => setTimeout(resolve, ms));\n\nasync function run() {\n    console.log('Start');\n    await delay(100);\n    console.log('Finished 100ms later');\n}\nrun();"
            },
            {
                "title": "HTML5 Canvas API for Graphics & Handwriting",
                "category": "doc",
                "language": "javascript",
                "url": "https://developer.mozilla.org/en-US/docs/Web/API/Canvas_API",
                "content": "HTML5 Canvas provides a 2D rendering surface for drawing paths, lines, and capturing stylus signatures.",
                "code": "const canvas = document.createElement('canvas');\nconst ctx = canvas.getContext('2d');\nctx.strokeStyle = '#2563eb';\nctx.lineWidth = 3;\nctx.beginPath();\nctx.moveTo(10, 10);\nctx.lineTo(200, 200);\nctx.stroke();"
            },
            {
                "title": "Pointer Events API for Touch & Apple Pencil Stylus",
                "category": "doc",
                "language": "javascript",
                "url": "https://developer.mozilla.org/en-US/docs/Web/API/Pointer_events",
                "content": "Pointer Events unifies mouse, pen, and touch inputs, providing pressure and tilt attributes.",
                "code": "element.addEventListener('pointerdown', (e) => {\n    const isStylus = e.pointerType === 'pen';\n    const pressure = e.pressure; // 0.0 to 1.0\n    console.log(`Input type: ${e.pointerType}, Pressure: ${pressure}`);\n});"
            }
        ]
    },
    {
        "id": "docker-cli",
        "name": "Docker & Container CLI Reference",
        "version": "24+",
        "description": "Docker container commands, Dockerfile syntax, and compose multi-container setups.",
        "category": "tool",
        "status": "downloaded",
        "entries": [
            {
                "title": "Dockerfile Multi-stage Build Pattern",
                "category": "doc",
                "language": "dockerfile",
                "url": "https://docs.docker.com/build/building/multi-stage/",
                "content": "Multi-stage builds reduce final image size by separating build dependencies from the runtime image.",
                "code": "FROM python:3.12-slim AS builder\nWORKDIR /app\nCOPY requirements.txt .\nRUN pip wheel --no-cache-dir -r requirements.txt\n\nFROM python:3.12-slim\nCOPY --from=builder /wheels /wheels\nRUN pip install /wheels/*"
            },
            {
                "title": "Docker Compose Services & Volumes",
                "category": "doc",
                "language": "yaml",
                "url": "https://docs.docker.com/compose/",
                "content": "Docker Compose orchestrates multi-container applications with isolated networks and shared volumes.",
                "code": "version: '3.8'\nservices:\n  devnote:\n    build: .\n    ports:\n      - '8000:8000'\n    volumes:\n      - ./storage:/app/storage\n    restart: unless-stopped"
            }
        ]
    },
    {
        "id": "git-reference",
        "name": "Git Version Control Guide",
        "version": "2.40+",
        "description": "Git branching, rebasing, stashing, and conflict resolution workflows.",
        "category": "tool",
        "status": "downloaded",
        "entries": [
            {
                "title": "Git Interactive Rebase (git rebase -i)",
                "category": "doc",
                "language": "bash",
                "url": "https://git-scm.com/docs/git-rebase",
                "content": "Interactive rebasing lets you clean up commit history, squash WIP commits, and reword messages before pushing.",
                "code": "# Rebase the last 3 commits\ngit rebase -i HEAD~3\n# Use 'squash' to combine commits, 'reword' to modify messages"
            },
            {
                "title": "Git Stash for Temporary Work In Progress",
                "category": "doc",
                "language": "bash",
                "url": "https://git-scm.com/docs/git-stash",
                "content": "Stashing saves dirty working directory changes without creating a permanent commit.",
                "code": "git stash save 'WIP: search panel changes'\n# Switch branches or pull upstream changes\ngit pull --rebase\n# Restore stashed changes\ngit stash pop"
            }
        ]
    }
]

class LocalDocsProvider(BaseSearchProvider):
    id = "local_docs"
    name = "Local Offline Documentation"
    description = "Searches downloaded documentation indexes locally using SQLite FTS5 (Zero Internet Required)"
    category = "documentation"
    is_online = False
    requires_api_key = False

    @classmethod
    def seed_bundled_indexes_if_needed(cls):
        """Seed SQLite with bundled doc packs and FTS5 entries on first launch."""
        db = SessionLocal()
        try:
            # Check if doc_indexes has any records
            existing_count = db.query(DocIndex).count()
            if existing_count == 0:
                with engine.connect() as conn:
                    for pack in BUNDLED_DOC_PACKS:
                        # 1. Add to DocIndex table
                        doc_idx = DocIndex(
                            id=pack["id"],
                            name=pack["name"],
                            version=pack["version"],
                            description=pack["description"],
                            category=pack["category"],
                            status=pack["status"],
                            entry_count=len(pack["entries"]),
                            size_bytes=len(str(pack["entries"])),
                            downloaded_at=datetime.datetime.utcnow(),
                            url=f"local://{pack['id']}"
                        )
                        db.add(doc_idx)

                        # 2. Add to doc_entries_fts virtual table
                        for e in pack["entries"]:
                            conn.execute(
                                text("""
                                    INSERT INTO doc_entries_fts(index_id, title, category, language, url, content, code)
                                    VALUES (:idx_id, :title, :cat, :lang, :url, :content, :code)
                                """),
                                {
                                    "idx_id": pack["id"],
                                    "title": e["title"],
                                    "cat": e["category"],
                                    "lang": e["language"],
                                    "url": e["url"],
                                    "content": e["content"],
                                    "code": e["code"]
                                }
                            )
                    conn.commit()
                db.commit()
        except Exception as e:
            print(f"Notice: local docs seed: {e}")
            db.rollback()
        finally:
            db.close()

    async def search(self, query: str, filters: Optional[Dict[str, Any]] = None) -> List[SearchResultItem]:
        q = query.strip()
        if not q:
            q = "python"  # default term to show entries

        # Sanitize query for FTS5 (remove special characters that break SQLite FTS syntax)
        clean_terms = re.findall(r"[a-zA-Z0-9_\-]+", q)
        if not clean_terms:
            return []

        # Construct FTS5 match query (e.g. 'decorator*' OR 'python*')
        fts_query = " OR ".join(f'"{t}"*' for t in clean_terms[:5])

        results: List[SearchResultItem] = []
        try:
            with engine.connect() as conn:
                # Query FTS5 matching doc_entries_fts
                sql = text("""
                    SELECT index_id, title, category, language, url, content, code, bm25(doc_entries_fts) as rank
                    FROM doc_entries_fts
                    WHERE doc_entries_fts MATCH :fts_query
                    ORDER BY rank ASC
                    LIMIT 15
                """)
                rows = conn.execute(sql, {"fts_query": fts_query}).fetchall()

                for row in rows:
                    idx_id, title, category, language, url, content, code, rank = row
                    results.append(SearchResultItem(
                        id=f"local-{idx_id}-{abs(hash(title)) % 100000}",
                        title=title,
                        category="offline",
                        snippet=content,
                        code=code,
                        language=language,
                        source=f"Offline Doc: {idx_id.replace('-', ' ').title()}",
                        url=url,
                        tags=["offline", idx_id, language]
                    ))
        except Exception as e:
            # Fallback to in-memory search across bundled packs if FTS error
            q_lower = q.lower()
            for pack in BUNDLED_DOC_PACKS:
                for e in pack["entries"]:
                    if q_lower in e["title"].lower() or q_lower in e["content"].lower():
                        results.append(SearchResultItem(
                            id=f"local-mem-{abs(hash(e['title'])) % 100000}",
                            title=e["title"],
                            category="offline",
                            snippet=e["content"],
                            code=e["code"],
                            language=e["language"],
                            source=f"Offline Doc: {pack['name']}",
                            url=e["url"],
                            tags=["offline", pack["id"], e["language"]]
                        ))

        return results
