"""Core repository interface."""
from abc import ABC, abstractmethod
from typing import List, Optional, Any
from src.grid.asset import Asset
from src.grid.meter import Meter

class AssetRepository(ABC):
    """Abstract interface for asset storage."""
    
    @abstractmethod
    def get_asset(self, asset_id: str) -> Optional[Asset]:
        pass

    @abstractmethod
    def save_asset(self, asset: Asset) -> None:
        pass
        
    @abstractmethod
    def get_all_edges(self) -> List[Any]:
        """Returns all edges for graph construction."""
        pass
