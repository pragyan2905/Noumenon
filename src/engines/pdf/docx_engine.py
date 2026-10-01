import time
from pathlib import Path

from src.core.interfaces.engine import ConversionEngine
from src.core.models.conversion import ConversionRequest, ConversionResult

class DocxEngine(ConversionEngine):
    """
    Converts DOCX to PDF using mammoth (DOCX->HTML) and xhtml2pdf (HTML->PDF).
    """

    def __init__(self):
        try:
            import mammoth
            from xhtml2pdf import pisa
            self.available = True
        except ImportError:
            self.available = False

    def can_convert(self, source_format: str, target_format: str) -> bool:
        if source_format == 'docx' and target_format == 'pdf':
            return True
        return False

    def get_quality_score(self) -> str:
        return 'B'

    def convert(self, request: ConversionRequest) -> ConversionResult:
        if not self.available:
            return ConversionResult(
                success=False,
                error_message="Dependencies missing. Please run `pip install xhtml2pdf mammoth`."
            )
            
        start_time = time.time()
        
        try:
            import mammoth
            from xhtml2pdf import pisa
            
            if not request.input_path.exists():
                return ConversionResult(success=False, error_message="Input file not found.")
            
            output_path = request.output_directory / f"{request.input_path.stem}.pdf"
            
            # Step 1: DOCX -> HTML
            with open(request.input_path, "rb") as docx_file:
                result = mammoth.convert_to_html(docx_file)
                html_content = result.value
                
            # Step 2: Add some basic styling so it looks like a document
            styled_html = f"""
            <html>
                <head>
                    <style>
                        @page {{
                            size: letter portrait;
                            margin: 1in;
                        }}
                        body {{ font-family: Helvetica, sans-serif; line-height: 1.5; }}
                        img {{ zoom: 50%; max-width: 100%; }}
                        table {{ border-collapse: collapse; width: 100%; margin-bottom: 1em; }}
                        th, td {{ border: 1px solid #dddddd; padding: 8px; text-align: left; }}
                    </style>
                </head>
                <body>
                    {html_content}
                </body>
            </html>
            """
            
            # Step 3: HTML -> PDF
            with open(output_path, "wb") as pdf_out:
                pisa_status = pisa.CreatePDF(styled_html, dest=pdf_out)
                
            if pisa_status.err:
                return ConversionResult(
                    success=False,
                    error_message="Failed to generate PDF from HTML.",
                    duration_seconds=time.time() - start_time
                )
                
            return ConversionResult(
                success=True,
                output_path=output_path,
                engine_used=self.__class__.__name__,
                duration_seconds=time.time() - start_time
            )
            
        except Exception as e:
            return ConversionResult(
                success=False,
                error_message=f"DOCX to PDF conversion failed: {str(e)}",
                duration_seconds=time.time() - start_time
            )
