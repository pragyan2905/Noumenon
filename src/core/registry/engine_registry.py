from typing import List
from src.core.interfaces.engine import ConversionEngine

class EngineRegistry:
    """
    Holds a list of all available conversion engines in the system.
    """
    def __init__(self):
        self._engines: List[ConversionEngine] = []

    def register(self, engine: ConversionEngine):
        """Register a new engine."""
        self._engines.append(engine)

    def find_engines(self, source_format: str, target_format: str) -> List[ConversionEngine]:
        """
        Returns a list of engines capable of this conversion, 
        sorted by their quality score (A is best).
        """
        capable_engines = [
            engine for engine in self._engines 
            if engine.can_convert(source_format, target_format)
        ]
        
        # Sort engines so that 'A' tier comes before 'B' tier, etc.
        capable_engines.sort(key=lambda e: e.get_quality_score())
        return capable_engines
