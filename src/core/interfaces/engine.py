from abc import ABC, abstractmethod
from src.core.models.conversion import ConversionRequest, ConversionResult

class ConversionEngine(ABC):
    """
    Abstract base class that all specialized conversion engines must inherit from.
    This guarantees that the router can interact with any engine uniformly.
    """

    @abstractmethod
    def can_convert(self, source_format: str, target_format: str) -> bool:
        """
        Returns True if this engine knows how to convert the source format 
        into the target format.
        """
        pass

    @abstractmethod
    def convert(self, request: ConversionRequest) -> ConversionResult:
        """
        Performs the actual conversion based on the request and returns a Result.
        """
        pass

    @abstractmethod
    def get_quality_score(self) -> str:
        """
        Returns a quality tier (e.g., 'A' for standard, 'B' for fallback).
        """
        pass
