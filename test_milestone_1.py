import sys
from pathlib import Path

# Ensure src is in path
project_root = Path(__file__).parent
sys.path.append(str(project_root))

from src.core.models.conversion import ConversionRequest
from src.core.registry.engine_registry import EngineRegistry
from src.core.router.conversion_router import ConversionRouter
from src.engines.mock_engine import MockPdfToTxtEngine
from src.engines.image.pillow_engine import PillowImageEngine
from src.engines.pdf.pdf2docx_engine import PdfToDocxEngine
from src.engines.pdf.pdf2docx_raster_engine import PdfToDocxRasterEngine
from src.detection.pdf_analysis import PDFAnalyzer
from src.validation.fidelity_report import FidelityValidator

def run_milestone():
    print("=== LOCALCONVERT: MILESTONE 1 ===")
    
    pdf_path = Path("2309.07597v2.pdf")
    if not pdf_path.exists():
        print(f"Error: {pdf_path} not found.")
        return

    print("\n1. Running Document Analyzer...")
    analysis = PDFAnalyzer.analyze(pdf_path)
    print(f"   Pages: {analysis.pages}")
    print(f"   Estimated Columns: {analysis.estimated_columns}")
    print(f"   Complexity: {analysis.complexity_score}")

    print("\n2. Routing & Converting...")
    registry = EngineRegistry()
    registry.register(MockPdfToTxtEngine())
    registry.register(PillowImageEngine())
    registry.register(PdfToDocxEngine())
    registry.register(PdfToDocxRasterEngine())
    
    router = ConversionRouter(registry)
    
    request = ConversionRequest(
        input_path=pdf_path,
        output_format="docx",
        output_directory=Path("/tmp")
    )
    
    result = router.route_and_convert(request)
    if not result.success:
        print(f"   Conversion Failed: {result.error_message}")
        return
        
    print(f"   Conversion Succeeded via: {result.engine_used}")
    print(f"   Output saved to: {result.output_path}")

    print("\n3. Running Fidelity Validator (rendering DOCX back to PDF)...")
    report = FidelityValidator.validate(pdf_path, result.output_path)
    
    if report.original_pages == -1:
        print("   [SKIPPED] Could not render DOCX locally (MS Word / docx2pdf missing).")
        print("   Please open the generated DOCX manually to verify pagination.")
        return

    print("\n--- FIDELITY REPORT ---")
    print(f"Original Pages: {report.original_pages}")
    print(f"Rendered Pages: {report.rendered_pages}")
    print(f"Pagination Match: {'PASS' if report.pagination_match else 'FAIL'}")
    print(f"Blank Pages Detected: {report.blank_pages_detected}")
    print(f"Text Similarity: {report.text_similarity:.1f}%")
    print(f"Images Preserved: {'YES' if report.images_preserved else 'NO'}")
    print(f"OVERALL RESULT: {'✅ ACCEPTABLE' if report.overall_acceptable else '❌ UNACCEPTABLE'}")
    print("-----------------------\n")

if __name__ == "__main__":
    run_milestone()
