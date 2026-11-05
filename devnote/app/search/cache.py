import time
import hashlib
from typing import Optional, Any, Dict

class SearchCache:
    """
    Lightweight, thread-safe in-memory cache for developer search queries.
    Prevents repeated expensive network requests and API rate-limit exhaustion.
    """
    def __init__(self, default_ttl_seconds: int = 300, max_entries: int = 500):
        self.default_ttl = default_ttl_seconds
        self.max_entries = max_entries
        self._store: Dict[str, Dict[str, Any]] = {}
        self.enabled = True

    @staticmethod
    def make_key(query: str, category: str = "", language: str = "", framework: str = "", provider: str = "") -> str:
        raw = f"{query.strip().lower()}|{category.lower()}|{language.lower()}|{framework.lower()}|{provider.lower()}"
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    def get(self, key: str) -> Optional[Any]:
        if not self.enabled:
            return None
        entry = self._store.get(key)
        if not entry:
            return None
        if time.time() > entry["expires_at"]:
            del self._store[key]
            return None
        return entry["data"]

    def set(self, key: str, data: Any, ttl: Optional[int] = None) -> None:
        if not self.enabled:
            return
        # Evict oldest if reaching capacity
        if len(self._store) >= self.max_entries:
            oldest_key = min(self._store.keys(), key=lambda k: self._store[k]["expires_at"])
            del self._store[oldest_key]

        expires_at = time.time() + (ttl or self.default_ttl)
        self._store[key] = {
            "data": data,
            "expires_at": expires_at
        }

    def clear(self) -> None:
        self._store.clear()
