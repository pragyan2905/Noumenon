from dataclasses import dataclass, field
from typing import Optional, Dict, Any
from pathlib import Path

@dataclass
class ConversionRequest:
    """Represents a request to convert a file from one format to another."""
    input_path: Path
    output_format: str
    output_directory: Path
    options: Dict[str, Any] = field(default_factory=dict)

@dataclass
class ConversionResult:
    """Represents the outcome of a conversion attempt."""
    success: bool
    output_path: Optional[Path] = None
    engine_used: Optional[str] = None
    duration_seconds: float = 0.0
    warnings: list[str] = field(default_factory=list)
    fidelity_score: Optional[float] = None
    error_message: Optional[str] = None
