from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from devnote.app.schemas.search import SearchResultItem

class BaseSearchProvider(ABC):
    """
    Abstract base class for all DevSearch providers.
    Each provider standardizes results into SearchResultItem.
    """
    id: str = "base"
    name: str = "Base Provider"
    description: str = "Base Search Provider"
    category: str = "general"
    is_online: bool = True
    requires_api_key: bool = False

    @abstractmethod
    async def search(self, query: str, filters: Optional[Dict[str, Any]] = None) -> List[SearchResultItem]:
        """Execute search and return normalized results list."""
        raise NotImplementedError

    async def is_available(self) -> bool:
        """Check if provider is operational and credentials are valid."""
        return True

    def get_info(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "category": self.category,
            "is_online": self.is_online,
            "requires_api_key": self.requires_api_key,
        }
