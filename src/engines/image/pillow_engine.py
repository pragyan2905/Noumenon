import time
from pathlib import Path
import tempfile
import shutil
from PIL import Image, ImageOps

from src.core.interfaces.engine import ConversionEngine
from src.core.models.conversion import ConversionRequest, ConversionResult

class PillowImageEngine(ConversionEngine):
    """
    Handles high-quality image conversions and transforms using the Python Imaging Library (Pillow).
    """
    
    # Formats that Pillow can read and write reliably
    SUPPORTED_FORMATS = {'png', 'jpg', 'jpeg', 'webp', 'bmp', 'tiff', 'gif'}

    def can_convert(self, source_format: str, target_format: str) -> bool:
        """Returns True if Pillow supports both the input and output formats."""
        return (source_format in self.SUPPORTED_FORMATS and 
                target_format in self.SUPPORTED_FORMATS)

    def get_quality_score(self) -> str:
        return 'A'

    def convert(self, request: ConversionRequest) -> ConversionResult:
        target_ext = request.output_format.lower().lstrip('.')
        if target_ext == 'jpg':
            target_ext = 'jpeg'
            
        output_path = request.output_directory / f"{request.input_path.stem}.{target_ext}"
        warnings = []
        
        start_time = time.time()
        
        try:
            # 1. Validate Input
            if not request.input_path.exists():
                return ConversionResult(success=False, error_message=f"Input file not found: {request.input_path}")
            
            with Image.open(request.input_path) as img:
                try:
                    img.verify() # Verify it's a valid image
                except Exception as e:
                    return ConversionResult(success=False, error_message=f"Corrupted or unsupported image file: {str(e)}")
            
            # Re-open after verify because verify() can leave the file in a bad state
            with Image.open(request.input_path) as img:
                # 2. Process / Transform
                options = request.options or {}
                
                # Transformations
                if options.get('resize'):
                    # resize should be a tuple (width, height)
                    width, height = options['resize']
                    img = img.resize((width, height), Image.Resampling.LANCZOS)
                
                if options.get('crop'):
                    # crop should be a tuple (left, top, right, bottom)
                    img = img.crop(options['crop'])
                    
                if options.get('rotate'):
                    # rotate should be an angle in degrees
                    img = img.rotate(options['rotate'], expand=True)
                    
                if options.get('flip') == 'horizontal':
                    img = ImageOps.mirror(img)
                elif options.get('flip') == 'vertical':
                    img = ImageOps.flip(img)
                    
                # Handle transparency issues (e.g., converting PNG with transparent background to JPEG)
                if img.mode in ('RGBA', 'P', 'LA') and target_ext in ('jpeg', 'bmp'):
                    # Create a white background to replace transparency
                    bg = Image.new('RGB', img.size, (255, 255, 255))
                    
                    if img.mode == 'P' or img.mode == 'LA':
                        img = img.convert('RGBA')
                        
                    try:
                        bg.paste(img, mask=img.split()[3]) # Use alpha channel as mask
                        img = bg
                        warnings.append("Transparency replaced with white background for compatibility.")
                    except IndexError:
                        img = img.convert('RGB')

                if img.mode != 'RGB' and target_ext in ('jpeg', 'bmp'):
                    img = img.convert('RGB')
                
                # 3. Write to temporary output first
                fd, temp_out_path = tempfile.mkstemp(suffix=f".{target_ext}")
                import os
                os.close(fd)
                temp_out = Path(temp_out_path)
                
                try:
                    save_kwargs = {}
                    if options.get('quality'):
                        save_kwargs['quality'] = options['quality']
                        if target_ext == 'jpeg':
                            save_kwargs['optimize'] = True
                    
                    img.save(temp_out, format=target_ext.upper(), **save_kwargs)
                    
                    # 4. Verify generated output
                    with Image.open(temp_out) as verify_img:
                        verify_img.verify()
                        
                    # 5. Move to final destination
                    shutil.move(str(temp_out), str(output_path))
                    
                except Exception as e:
                    # Clean up failed temp file
                    if temp_out.exists():
                        temp_out.unlink()
                    raise e
                    
            return ConversionResult(
                success=True,
                output_path=output_path,
                engine_used=self.__class__.__name__,
                duration_seconds=time.time() - start_time,
                warnings=warnings
            )
        except Exception as e:
            return ConversionResult(
                success=False,
                error_message=f"Pillow conversion failed: {str(e)}",
                duration_seconds=time.time() - start_time
            )
