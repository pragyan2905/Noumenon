import time
import tempfile
import shutil
import subprocess
from pathlib import Path

from src.core.interfaces.engine import ConversionEngine
from src.core.models.conversion import ConversionRequest, ConversionResult

class TesseractOcrEngine(ConversionEngine):
    """
    Handles OCR and Searchable PDF generation using Tesseract.
    Requires tesseract to be installed on the system.
    """
    
    IMAGE_FORMATS = {'png', 'jpg', 'jpeg', 'webp', 'tiff', 'bmp'}

    def __init__(self):
        # Check if tesseract is available
        try:
            subprocess.run(["tesseract", "--version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
            self.available = True
        except (subprocess.CalledProcessError, FileNotFoundError):
            self.available = False

    def can_convert(self, source_format: str, target_format: str) -> bool:
        if not self.available:
            return False
        # Image to Text (OCR)
        if source_format in self.IMAGE_FORMATS and target_format == 'txt':
            return True
        # Image to Searchable PDF
        if source_format in self.IMAGE_FORMATS and target_format == 'pdf':
            return True
        # PDF to Searchable PDF (Not directly supported by just tesseract, requires splitting/merging, keeping simple for now)
        return False

    def get_quality_score(self) -> str:
        # A bit lower than PyMuPdf for image->pdf so it doesn't default to OCR unless requested
        return 'B'

    def convert(self, request: ConversionRequest) -> ConversionResult:
        source_ext = request.input_path.suffix.lower().lstrip('.')
        target_ext = request.output_format.lower().lstrip('.')
        
        start_time = time.time()
        
        try:
            if not request.input_path.exists():
                return ConversionResult(success=False, error_message=f"Input file not found: {request.input_path}")
            
            # Tesseract writes to an output file without extension and appends .txt or .pdf automatically
            fd, temp_out_base_path = tempfile.mkstemp()
            import os
            os.close(fd)
            # Remove the empty file because tesseract wants to create it
            os.unlink(temp_out_base_path)
            
            temp_out = Path(f"{temp_out_base_path}.{target_ext}")
            
            try:
                lang = request.options.get('lang', 'eng') if request.options else 'eng'
                
                cmd = ["tesseract", str(request.input_path), temp_out_base_path, "-l", lang]
                if target_ext == 'pdf':
                    cmd.append("pdf")
                else:
                    cmd.append("txt")
                    
                result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                
                if result.returncode != 0:
                    raise RuntimeError(f"Tesseract failed: {result.stderr}")
                
                if not temp_out.exists():
                    raise RuntimeError("Tesseract did not produce the expected output file.")
                
                # Verify output file isn't empty
                if temp_out.stat().st_size == 0:
                    raise ValueError("Generated OCR output is empty.")
                    
                output_path = request.output_directory / f"{request.input_path.stem}.{target_ext}"
                shutil.move(str(temp_out), str(output_path))
                
            except Exception as e:
                if temp_out.exists():
                    temp_out.unlink()
                raise e
                
            return ConversionResult(
                success=True,
                output_path=output_path,
                engine_used=self.__class__.__name__,
                duration_seconds=time.time() - start_time
            )
            
        except Exception as e:
            return ConversionResult(
                success=False,
                error_message=f"OCR conversion failed: {str(e)}",
                duration_seconds=time.time() - start_time
            )
