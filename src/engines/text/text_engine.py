import time
import tempfile
import shutil
from pathlib import Path

try:
    import markdown
    HAS_MARKDOWN = True
except ImportError:
    HAS_MARKDOWN = False

try:
    from bs4 import BeautifulSoup
    HAS_BS4 = True
except ImportError:
    HAS_BS4 = False

from src.core.interfaces.engine import ConversionEngine
from src.core.models.conversion import ConversionRequest, ConversionResult

class TextEngine(ConversionEngine):
    """
    Handles robust text conversions: txt, md, html.
    """
    
    def __init__(self):
        self.formats = {'txt', 'md', 'html'}

    def can_convert(self, source_format: str, target_format: str) -> bool:
        return source_format in self.formats and target_format in self.formats

    def get_quality_score(self) -> str:
        return 'A'

    def convert(self, request: ConversionRequest) -> ConversionResult:
        source_ext = request.input_path.suffix.lower().lstrip('.')
        target_ext = request.output_format.lower().lstrip('.')
        
        start_time = time.time()
        
        try:
            if not request.input_path.exists():
                return ConversionResult(success=False, error_message=f"Input file not found: {request.input_path}")
            
            # Read input
            try:
                with open(request.input_path, 'r', encoding='utf-8') as f:
                    text_content = f.read()
            except Exception as e:
                return ConversionResult(success=False, error_message=f"Failed to read {source_ext.upper()}: {str(e)}")
            
            # Convert
            output_content = text_content
            
            if source_ext == 'md' and target_ext == 'html':
                if HAS_MARKDOWN:
                    output_content = markdown.markdown(text_content, extensions=['tables', 'fenced_code'])
                else:
                    return ConversionResult(success=False, error_message="Markdown library not installed for md->html conversion.")
            
            elif source_ext == 'html' and target_ext == 'md':
                # Basic conversion, ideally we'd use html2text or markdownify, but keeping dependencies light
                if HAS_BS4:
                    soup = BeautifulSoup(text_content, 'html.parser')
                    # Very rudimentary extraction
                    output_content = soup.get_text(separator='\n\n')
                else:
                    # Fallback to dumb tags stripping
                    import re
                    output_content = re.sub(r'<[^>]+>', '', text_content)
                    
            elif source_ext == 'html' and target_ext == 'txt':
                if HAS_BS4:
                    soup = BeautifulSoup(text_content, 'html.parser')
                    output_content = soup.get_text(separator='\n')
                else:
                    import re
                    output_content = re.sub(r'<[^>]+>', '', text_content)
                    
            elif source_ext == 'txt' and target_ext == 'html':
                # Escape and wrap in pre
                import html
                escaped = html.escape(text_content)
                output_content = f"<html><body><pre>{escaped}</pre></body></html>"
                
            # Write temp output
            fd, temp_out_path = tempfile.mkstemp(suffix=f".{target_ext}")
            import os
            os.close(fd)
            temp_out = Path(temp_out_path)
            
            try:
                with open(temp_out, 'w', encoding='utf-8') as f:
                    f.write(output_content)
                
                # Verify generated output by checking size
                if temp_out.stat().st_size == 0 and len(output_content) > 0:
                    raise ValueError("Generated output file is unexpectedly empty.")
                
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
                error_message=f"Text conversion failed: {str(e)}",
                duration_seconds=time.time() - start_time
            )
