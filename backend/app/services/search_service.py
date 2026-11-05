import re
import uuid
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from backend.app.models.notebook import Notebook
from backend.app.models.snippet import Snippet
from backend.app.schemas.search import SearchResultItem, SearchResponse

# Built-in developer knowledge base: concepts, error explanations, code examples, documentation
DEV_KNOWLEDGE_BASE: List[Dict[str, Any]] = [
    # Concepts - Python
    {
        "id": "concept-py-decorators",
        "title": "Python Decorators",
        "category": "concept",
        "snippet": "A decorator is a callable that takes another function as an argument, extends its behavior without modifying it, and returns the modified function.",
        "code": "import functools\nimport time\n\ndef timer(func):\n    @functools.wraps(func)\n    def wrapper(*args, **kwargs):\n        start = time.perf_counter()\n        val = func(*args, **kwargs)\n        print(f'{func.__name__} executed in {time.perf_counter() - start:.4f}s')\n        return val\n    return wrapper\n\n@timer\ndef compute():\n    return sum(i * i for i in range(100_000))\n\nprint('Result:', compute())",
        "language": "python",
        "source": "Python 3 Documentation",
        "url": "https://docs.python.org/3/glossary.html#term-decorator"
    },
    {
        "id": "concept-py-generators",
        "title": "Python Generators & 'yield'",
        "category": "concept",
        "snippet": "Generators allow you to declare a function that behaves like an iterator. They yield values lazily one by one instead of computing and storing everything in memory.",
        "code": "def count_up_to(max_val):\n    count = 1\n    while count <= max_val:\n        yield count\n        count += 1\n\nfor num in count_up_to(5):\n    print(num, end=' ')\nprint()",
        "language": "python",
        "source": "Python Language Reference",
        "url": "https://docs.python.org/3/reference/expressions.html#yield-expressions"
    },
    {
        "id": "concept-py-async",
        "title": "Python Async / Await & Asyncio",
        "category": "concept",
        "snippet": "Asynchronous programming using coroutines, event loops, and non-blocking I/O tasks.",
        "code": "import asyncio\n\nasync def fetch_data(task_id: int, delay: float):\n    print(f'Starting task {task_id}')\n    await asyncio.sleep(delay)\n    print(f'Completed task {task_id}')\n    return f'Result {task_id}'\n\nasync def main():\n    results = await asyncio.gather(\n        fetch_data(1, 0.1),\n        fetch_data(2, 0.2)\n    )\n    print('All results:', results)\n\nasyncio.run(main())",
        "language": "python",
        "source": "Asyncio Docs",
        "url": "https://docs.python.org/3/library/asyncio.html"
    },
    {
        "id": "concept-py-comprehensions",
        "title": "List & Dictionary Comprehensions",
        "category": "concept",
        "snippet": "Concise syntax to generate lists, sets, and dictionaries from existing iterables with filtering and transformations.",
        "code": "# List comprehension with filtering\nsquares = [x**2 for x in range(10) if x % 2 == 0]\nprint('Even squares:', squares)\n\n# Dict comprehension\nword_lengths = {w: len(w) for w in ['devnote', 'python', 'fastapi']}\nprint('Lengths:', word_lengths)",
        "language": "python",
        "source": "Python Tutorial",
        "url": "https://docs.python.org/3/tutorial/datastructures.html#list-comprehensions"
    },
    {
        "id": "concept-py-context-managers",
        "title": "Context Managers ('with' statement)",
        "category": "concept",
        "snippet": "Context managers guarantee resource cleanup (closing files, releasing locks, resetting state) using __enter__ and __exit__ or @contextmanager.",
        "code": "from contextlib import contextmanager\n\n@contextmanager\ndef managed_resource(name):\n    print(f'Acquiring {name}')\n    try:\n        yield f'Resource[{name}]'\n    finally:\n        print(f'Releasing {name}')\n\nwith managed_resource('DatabaseConn') as res:\n    print(f'Using {res}')",
        "language": "python",
        "source": "Python Reference",
        "url": "https://docs.python.org/3/reference/datamodel.html#context-managers"
    },

    # Concepts - JavaScript
    {
        "id": "concept-js-promises",
        "title": "JavaScript Promises & Async/Await",
        "category": "concept",
        "snippet": "Promises represent eventual completion or failure of asynchronous operations, cleanly consumed with async/await syntax.",
        "code": "const delay = (ms) => new Promise(resolve => setTimeout(resolve, ms));\n\nasync function performTasks() {\n    console.log('Task 1 starting...');\n    await delay(50);\n    console.log('Task 1 complete!');\n    return 42;\n}\n\nperformTasks().then(val => console.log('Final value:', val));",
        "language": "javascript",
        "source": "MDN Web Docs",
        "url": "https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Promise"
    },
    {
        "id": "concept-js-closures",
        "title": "JavaScript Closures & Lexical Scope",
        "category": "concept",
        "snippet": "A closure gives an inner function access to its outer function's scope even after the outer function has returned.",
        "code": "function createCounter(initial = 0) {\n    let count = initial;\n    return {\n        increment: () => ++count,\n        decrement: () => --count,\n        get: () => count\n    };\n}\n\nconst counter = createCounter(10);\nconsole.log(counter.increment()); // 11\nconsole.log(counter.increment()); // 12\nconsole.log(counter.decrement()); // 11",
        "language": "javascript",
        "source": "MDN Closures Guide",
        "url": "https://developer.mozilla.org/en-US/docs/Web/JavaScript/Closures"
    },
    {
        "id": "concept-js-destructuring",
        "title": "Destructuring & Rest/Spread Syntax",
        "category": "concept",
        "snippet": "Unpack values from arrays or properties from objects into distinct variables, or collect/spread elements.",
        "code": "const user = { name: 'Alice', role: 'Engineer', settings: { theme: 'dark' } };\nconst { name, settings: { theme } } = user;\nconsole.log(`User: ${name}, Theme: ${theme}`);\n\nconst nums = [1, 2, 3];\nconst extended = [...nums, 4, 5];\nconsole.log('Spread array:', extended);",
        "language": "javascript",
        "source": "MDN Destructuring",
        "url": "https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Operators/Destructuring_assignment"
    },

    # Error Messages & Solutions
    {
        "id": "err-py-nonetype-subscriptable",
        "title": "TypeError: 'NoneType' object is not subscriptable",
        "category": "error",
        "snippet": "Occurs when attempting to index or slice a variable with [key] or [index] that holds None instead of a dict, list, or string.",
        "code": "# Solution: Safely check or use fallback\ndef get_val(data, key):\n    if data is None:\n        return 'Default'\n    return data.get(key, 'Default')\n\nuser_data = None\nprint(get_val(user_data, 'profile')) # Safe!",
        "language": "python",
        "source": "DevNote Error Diagnostic",
        "url": "https://docs.python.org/3/library/exceptions.html#TypeError"
    },
    {
        "id": "err-py-index-error",
        "title": "IndexError: list index out of range",
        "category": "error",
        "snippet": "Raised when attempting to access an index outside the boundaries of a sequence (e.g., negative beyond -len or >= len).",
        "code": "items = [10, 20, 30]\nidx = 5\n\n# Safe access using bounds checking or exception handling\nval = items[idx] if 0 <= idx < len(items) else None\nprint('Safe access:', val)",
        "language": "python",
        "source": "Python Exceptions",
        "url": "https://docs.python.org/3/library/exceptions.html#IndexError"
    },
    {
        "id": "err-py-key-error",
        "title": "KeyError in Dictionary Access",
        "category": "error",
        "snippet": "Raised when mapping (dictionary) key is not found in the set of existing keys.",
        "code": "config = {'port': 8000}\n\n# Safe access using .get() with fallback\nhost = config.get('host', '127.0.0.1')\nport = config.get('port', 3000)\nprint(f'Server running at {host}:{port}')",
        "language": "python",
        "source": "Python Exceptions",
        "url": "https://docs.python.org/3/library/exceptions.html#KeyError"
    },
    {
        "id": "err-js-cannot-read-undefined",
        "title": "TypeError: Cannot read properties of undefined / null",
        "category": "error",
        "snippet": "Occurs when trying to access a property or method on a variable that is null or undefined.",
        "code": "const response = { status: 200, data: null };\n\n// Safe access using Optional Chaining (?.) and Nullish Coalescing (??)\nconst title = response?.data?.user?.name ?? 'Anonymous User';\nconsole.log('User title:', title);",
        "language": "javascript",
        "source": "MDN Optional Chaining",
        "url": "https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Operators/Optional_chaining"
    },
    {
        "id": "err-js-reference-error",
        "title": "ReferenceError: variable is not defined",
        "category": "error",
        "snippet": "Thrown when code refers to a variable that has not been declared, or is in the Temporal Dead Zone (TDZ).",
        "code": "// Ensure declarations precede usage\nlet initializedValue = 'Ready';\nconsole.log('Status:', initializedValue);",
        "language": "javascript",
        "source": "MDN ReferenceError",
        "url": "https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/ReferenceError"
    },

    # Code Examples
    {
        "id": "code-binary-search",
        "title": "Binary Search Algorithm (O(log n))",
        "category": "code",
        "snippet": "Efficient algorithm for finding an item in a sorted array by repeatedly dividing the search interval in half.",
        "code": "def binary_search(arr, target):\n    low, high = 0, len(arr) - 1\n    while low <= high:\n        mid = (low + high) // 2\n        if arr[mid] == target:\n            return mid\n        elif arr[mid] < target:\n            low = mid + 1\n        else:\n            high = mid - 1\n    return -1\n\nnums = [2, 5, 8, 12, 16, 23, 38, 56, 72, 91]\nprint('Found 23 at index:', binary_search(nums, 23))",
        "language": "python",
        "source": "Algorithms & Data Structures",
        "url": "https://en.wikipedia.org/wiki/Binary_search_algorithm"
    },
    {
        "id": "code-js-debounce",
        "title": "Debounce Function in JavaScript",
        "category": "code",
        "snippet": "Limits the rate at which a function can fire, ensuring it only executes after a specified quiet period.",
        "code": "function debounce(fn, delayMs = 300) {\n    let timerId;\n    return function(...args) {\n        clearTimeout(timerId);\n        timerId = setTimeout(() => fn.apply(this, args), delayMs);\n    };\n}\n\nconst logSave = debounce((txt) => console.log('Saved:', txt), 200);\nlogSave('Doc v1');\nlogSave('Doc v2'); // Only v2 will fire!",
        "language": "javascript",
        "source": "Modern JS Utilities",
        "url": "https://developer.mozilla.org/en-US/docs/Glossary/Debounce"
    },
    {
        "id": "code-py-regex",
        "title": "Regex Email & URL Parsing in Python",
        "category": "code",
        "snippet": "Using the 're' standard library for regular expressions, extraction, and validation.",
        "code": "import re\n\ntext = 'Contact support@devnote.io or admin@example.org for inquiries.'\npattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}'\nemails = re.findall(pattern, text)\nprint('Extracted emails:', emails)",
        "language": "python",
        "source": "Python re Module",
        "url": "https://docs.python.org/3/library/re.html"
    }
]

class SearchService:
    @staticmethod
    def search_all(
        db: Session,
        query: str,
        category: Optional[str] = "all"
    ) -> SearchResponse:
        """
        Unified developer search workspace:
        Searches concepts, documentation, error diagnostics, code examples,
        and user's existing notebooks.
        """
        q = query.strip().lower()
        if not q:
            # Return popular concepts as suggestions
            items = [SearchResultItem(**item) for item in DEV_KNOWLEDGE_BASE[:8]]
            return SearchResponse(query="", total_results=len(items), results=items)

        results: List[SearchResultItem] = []

        # 1. Search in curated Knowledge Base (concepts, docs, errors, code)
        if category in ("all", "concept", "doc", "error", "code", "web"):
            for item in DEV_KNOWLEDGE_BASE:
                if category != "all" and item.get("category") != category:
                    continue

                text_to_search = f"{item['title']} {item['snippet']} {item.get('code', '')}".lower()
                if q in text_to_search:
                    results.append(SearchResultItem(**item))

        # 2. Search in user's existing notebooks
        if category in ("all", "notebook"):
            notebooks = db.query(Notebook).filter(Notebook.is_archived == False).all()
            for nb in notebooks:
                # Check title or description
                if q in nb.title.lower() or (nb.description and q in nb.description.lower()):
                    results.append(SearchResultItem(
                        id=f"nb-{nb.id}",
                        title=f"Notebook: {nb.title}",
                        category="notebook",
                        snippet=nb.description or f"Matches notebook title '{nb.title}'",
                        source=f"Created {nb.created_at.strftime('%Y-%m-%d') if nb.created_at else ''}",
                        notebook_id=nb.id,
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
                                notebook_id=nb.id,
                                block_id=b.get("id")
                            ))
                            break  # one block per notebook is enough for overview

        # 3. Search Snippets
        if category in ("all", "code", "snippet"):
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
                        source="Code Snippet Library"
                    ))

        return SearchResponse(
            query=query,
            total_results=len(results),
            results=results
        )

    @staticmethod
    def search_web(query: str, category: Optional[str] = "all") -> SearchResponse:
        """
        External developer web search query, querying live developer resources
        or instant answers with safe fallback.
        """
        q = query.strip()
        matched = []
        for item in DEV_KNOWLEDGE_BASE:
            if q.lower() in item['title'].lower() or q.lower() in item['snippet'].lower():
                matched.append(SearchResultItem(**item))

        # Add external web search link item
        matched.append(SearchResultItem(
            id=f"web-external-{uuid.uuid4().hex[:6]}",
            title=f"Search online docs for '{q}'",
            category="web",
            snippet=f"Explore official documentation, GitHub repositories, and StackOverflow answers for {q}.",
            source="Developer Web Engine",
            url=f"https://devdocs.io/#q={q.replace(' ', '+')}"
        ))

        return SearchResponse(
            query=query,
            total_results=len(matched),
            results=matched
        )
