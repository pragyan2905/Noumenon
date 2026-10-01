"""
Conversion Router — Core Engine Selection

Finds the most appropriate engine for a requested conversion
and executes it.
"""
from src.core.models.conversion import ConversionRequest, ConversionResult
from src.core.registry.engine_registry import EngineRegistry

class ConversionRouter:
    """
    The main entry point for starting a conversion.
    """
    def __init__(self, registry: EngineRegistry):
        self.registry = registry

    def route_and_convert(self, request: ConversionRequest) -> ConversionResult:
        """
        Finds the best engine for the request and attempts conversion.
        If the best engine fails, it falls back to the next best engine.
        """
        source_ext = request.input_path.suffix.lower().lstrip('.')
        target_ext = request.output_format.lower().lstrip('.')

        engines = self.registry.find_engines(source_ext, target_ext)

        if not engines:
            return ConversionResult(
                success=False,
                error_message=f"No engine found capable of converting {source_ext} to {target_ext}."
            )

        # Try engines in order (best first), with fallback
        warnings = []
        for engine in engines:
            result = engine.convert(request)
            
            if result.success:
                if result.warnings:
                    warnings.extend(result.warnings)
                result.warnings = warnings
                return result
            else:
                warnings.append(
                    f"Engine {engine.__class__.__name__} failed: {result.error_message}"
                )

        return ConversionResult(
            success=False,
            warnings=warnings,
            error_message=f"All available engines failed to convert the document. Details: {', '.join(warnings)}"
        )
