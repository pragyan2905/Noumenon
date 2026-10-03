import time
from pathlib import Path
import tempfile
import shutil
from PIL import Image, ImageOps, ImageFile

# Tell Pillow to tolerate slightly corrupted/truncated image files
ImageFile.LOAD_TRUNCATED_IMAGES = True
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
                
                # Background Removal
                if options.get('remove_background'):
                    try:
                        from rembg import remove, new_session
                        # Use u2net for standard, u2netp for lightweight
                        session = new_session('u2net')
                        img = remove(img, session=session)
                        warnings.append("Background successfully removed using AI.")
                    except ImportError:
                        warnings.append("rembg library not installed. Background removal skipped.")
                    except Exception as e:
                        warnings.append(f"Background removal failed: {str(e)}")
                
                # Transformations
                if options.get('scale') and options['scale'] != 100:
                    scale_factor = float(options['scale']) / 100.0
                    new_width = int(img.width * scale_factor)
                    new_height = int(img.height * scale_factor)
                    img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                elif options.get('width') or options.get('height'):
                    new_w = int(options.get('width') or img.width)
                    new_h = int(options.get('height') or img.height)
                    img = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
                elif options.get('resize'):
                    # legacy tuple support
                    width, height = options['resize']
                    img = img.resize((width, height), Image.Resampling.LANCZOS)
                
                if options.get('crop'):
                    img = img.crop(options['crop'])
                    
                if options.get('rotate'):
                    img = img.rotate(int(options['rotate']), expand=True)
                    
                if options.get('flip') == 'horizontal':
                    img = ImageOps.mirror(img)
                elif options.get('flip') == 'vertical':
                    img = ImageOps.flip(img)

                # Color Enhancements
                if options.get('auto_contrast'):
                    if img.mode not in ('L', 'RGB'):
                        img_converted = img.convert('RGB')
                        img_converted = ImageOps.autocontrast(img_converted)
                        img = img_converted
                    else:
                        img = ImageOps.autocontrast(img)

                from PIL import ImageEnhance, ImageFilter
                
                if options.get('brightness') and options['brightness'] != 100:
                    enhancer = ImageEnhance.Brightness(img)
                    img = enhancer.enhance(float(options['brightness']) / 100.0)
                    
                if options.get('contrast') and options['contrast'] != 100:
                    enhancer = ImageEnhance.Contrast(img)
                    img = enhancer.enhance(float(options['contrast']) / 100.0)
                    
                if options.get('sharpness') and options['sharpness'] != 100:
                    enhancer = ImageEnhance.Sharpness(img)
                    img = enhancer.enhance(float(options['sharpness']) / 100.0)
                    
                # Noise Reduction (Filters)
                if options.get('noise_reduction') == 'median':
                    img = img.filter(ImageFilter.MedianFilter(size=3))
                elif options.get('noise_reduction') == 'gaussian':
                    img = img.filter(ImageFilter.GaussianBlur(radius=2))
                    
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
                    
                # Grayscale conversion
                if options.get('grayscale'):
                    img = img.convert('L')
                    # Convert back to RGB if saving to jpeg and it complains, but PIL handles 'L' to JPEG fine.
                
                # 3. Write to temporary output first
                fd, temp_out_path = tempfile.mkstemp(suffix=f".{target_ext}")
                import os
                os.close(fd)
                temp_out = Path(temp_out_path)
                
                try:
                    save_kwargs = {}
                    if options.get('quality'):
                        save_kwargs['quality'] = int(options['quality'])
                        if target_ext == 'jpeg':
                            save_kwargs['optimize'] = True
                            
                    # Aggressive Compression Feature
                    if options.get('compress_level') == 'high':
                        if target_ext in ('jpeg', 'jpg', 'webp'):
                            save_kwargs['quality'] = min(int(options.get('quality', 60)), 60)
                            save_kwargs['optimize'] = True
                            if target_ext in ('jpeg', 'jpg'):
                                save_kwargs['progressive'] = True
                        elif target_ext == 'png':
                            save_kwargs['optimize'] = True
                            # Quantize PNGs to 256 colors for massive file size reduction
                            if img.mode != 'P':
                                img = img.convert('P', palette=Image.ADAPTIVE, colors=256)
                            
                    if options.get('dpi'):
                        val = int(options['dpi'])
                        save_kwargs['dpi'] = (val, val)
                        
                    # EXIF Metadata removal
                    if not options.get('remove_metadata', False) and 'exif' in img.info:
                        save_kwargs['exif'] = img.info['exif']
                    
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
