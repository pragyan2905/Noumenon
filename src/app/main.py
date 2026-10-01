import sys
from pathlib import Path

# Ensure Python can find the 'src' module
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

from src.core.models.conversion import ConversionRequest
from src.core.registry.engine_registry import EngineRegistry
from src.core.router.conversion_router import ConversionRouter
from src.engines.mock_engine import MockPdfToTxtEngine

def main():
    print("--- Starting LocalConvert Pipeline Test ---")
    
    # 1. Setup the Registry
    registry = EngineRegistry()
    
    # 2. Register our available engines
    registry.register(MockPdfToTxtEngine())
    
    # 3. Setup the Router
    router = ConversionRouter(registry)
    
    # 4. Create a Request (pretend the user dragged in a file)
    request = ConversionRequest(
        input_path=Path("sample_document.pdf"),
        output_format="txt",
        output_directory=Path("/tmp/output")
    )
    
    print(f"\nRouter received request: {request.input_path.name} -> {request.output_format}")
    
    # 5. Route and Convert!
    result = router.route_and_convert(request)
    
    # 6. View the Result
    if result.success:
        print("\n✅ Success!")
        print(f"Engine Used: {result.engine_used}")
        print(f"Output File: {result.output_path}")
    else:
        print("\n❌ Failed!")
        print(f"Error: {result.error_message}")

if __name__ == "__main__":
    main()
