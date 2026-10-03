import time
import tempfile
import shutil
from pathlib import Path
import fitz # PyMuPDF

from src.core.interfaces.engine import ConversionEngine
from src.core.models.conversion import ConversionRequest, ConversionResult

class PyMuPdfEngine(ConversionEngine):
    """
    Handles reliable core PDF operations using PyMuPDF:
    - Image -> PDF
    - PDF -> Image (rasterization)
    - PDF Merge, Split, Reorder, Rotate, Metadata
    """
    
    IMAGE_FORMATS = {'png', 'jpg', 'jpeg', 'webp', 'tiff', 'bmp'}
    
    def can_convert(self, source_format: str, target_format: str) -> bool:
        if source_format == 'pdf' and target_format in self.IMAGE_FORMATS:
            return True
        if source_format in self.IMAGE_FORMATS and target_format == 'pdf':
            return True
        # Future: pdf to pdf (merge, optimize, etc.)
        if source_format == 'pdf' and target_format == 'pdf':
            return True
        return False

    def get_quality_score(self) -> str:
        return 'A'

    def convert(self, request: ConversionRequest) -> ConversionResult:
        source_ext = request.input_path.suffix.lower().lstrip('.')
        target_ext = request.output_format.lower().lstrip('.')
        
        start_time = time.time()
        
        try:
            # 1. Validate Input
            if not request.input_path.exists():
                return ConversionResult(success=False, error_message=f"Input file not found: {request.input_path}")
            
            # Temporary output path
            fd, temp_out_path = tempfile.mkstemp(suffix=f".{target_ext}")
            import os
            os.close(fd)
            temp_out = Path(temp_out_path)
            
            output_path = request.output_directory / f"{request.input_path.stem}.{target_ext}"
            warnings = []

            try:
                # PDF to Image
                if source_ext == 'pdf' and target_ext in self.IMAGE_FORMATS:
                    # For simplicity, convert the first page, or use options to specify page
                    try:
                        doc = fitz.open(request.input_path)
                        options = request.options or {}
                        
                        # Handle decryption if password provided
                        if doc.needs_pass:
                            pwd = options.get('password', '')
                            if not doc.authenticate(pwd):
                                raise ValueError("PDF is encrypted. Invalid or missing password.")
                    except Exception as e:
                        raise ValueError(f"Failed to open PDF: {str(e)}")
                    
                    if doc.page_count == 0:
                        raise ValueError("PDF has no pages.")
                        
                    options = request.options or {}
                    page_num = options.get('page', 0)
                    
                    if page_num >= doc.page_count or page_num < 0:
                        raise ValueError(f"Invalid page number {page_num} for PDF with {doc.page_count} pages.")
                    
                    page = doc.load_page(page_num)
                    
                    # DPI options
                    zoom = options.get('zoom', 2.0) # default 144 DPI roughly
                    mat = fitz.Matrix(zoom, zoom)
                    pix = page.get_pixmap(matrix=mat)
                    
                    if target_ext == 'jpg':
                        target_ext = 'jpeg'
                        
                    pix.save(temp_out)
                    doc.close()
                    
                    # Verify generated image
                    from PIL import Image
                    with Image.open(temp_out) as verify_img:
                        verify_img.verify()

                # Image to PDF
                elif source_ext in self.IMAGE_FORMATS and target_ext == 'pdf':
                    doc = fitz.open()
                    
                    # Open image to get dimensions
                    try:
                        img_doc = fitz.open(request.input_path)
                    except Exception as e:
                         raise ValueError(f"Failed to open Image: {str(e)}")
                         
                    rect = img_doc[0].rect
                    pdfbytes = img_doc.convert_to_pdf()
                    img_doc.close()
                    
                    img_pdf = fitz.open("pdf", pdfbytes)
                    doc.insert_pdf(img_pdf)
                    
                    options = request.options or {}
                    
                    # Metadata
                    if options.get('metadata'):
                        doc.set_metadata(options['metadata'])
                        
                    doc.save(temp_out)
                    doc.close()
                    
                    # Verify output PDF
                    try:
                        verify_doc = fitz.open(temp_out)
                        if verify_doc.page_count == 0:
                            raise ValueError("Output PDF is empty.")
                        verify_doc.close()
                    except Exception as e:
                        raise ValueError(f"Generated PDF verification failed: {str(e)}")

                # PDF to PDF (Transformations, Optimize, Extract, Password, Merge, Watermark)
                elif source_ext == 'pdf' and target_ext == 'pdf':
                    options = request.options or {}
                    action = options.get('action')
                    
                    if action == 'merge' and getattr(request, 'input_paths', None):
                        doc = fitz.open()
                        for p in request.input_paths:
                            try:
                                src_doc = fitz.open(p)
                                doc.insert_pdf(src_doc)
                                src_doc.close()
                            except Exception as e:
                                warnings.append(f"Failed to merge {p.name}: {str(e)}")
                    else:
                        try:
                            doc = fitz.open(request.input_path)
                            if doc.needs_pass:
                                pwd = options.get('password', '')
                                if not doc.authenticate(pwd):
                                    raise ValueError("PDF is encrypted. Invalid or missing password.")
                        except Exception as e:
                            raise ValueError(f"Failed to open PDF: {str(e)}")
                            
                        # Handle page extraction
                        if 'page' in options and options['page'] != '':
                            try:
                                # 1-indexed to 0-indexed
                                page_num = int(options['page']) - 1
                                if page_num < 0 or page_num >= doc.page_count:
                                    raise ValueError(f"Page number out of bounds.")
                                
                                new_doc = fitz.open()
                                new_doc.insert_pdf(doc, from_page=page_num, to_page=page_num)
                                doc.close()
                                doc = new_doc
                            except ValueError as ve:
                                 raise ValueError(f"Invalid page extraction: {str(ve)}")
                    
                    if options.get('metadata'):
                        doc.set_metadata(options['metadata'])
                        
                    # Rotate all pages if specified
                    if options.get('rotate'):
                        try:
                            rot = int(options['rotate'])
                            for page in doc:
                                page.set_rotation(rot)
                        except Exception:
                            pass
                            
                    # Watermarking
                    if options.get('watermark'):
                        wm_text = options['watermark']
                        for page in doc:
                            # Insert diagonally across page
                            rect = page.rect
                            p1 = fitz.Point(rect.width * 0.1, rect.height * 0.9)
                            page.insert_text(p1, wm_text, fontsize=48, color=(0.8, 0.8, 0.8), rotate=45, fill_opacity=0.5)
                            
                    # Encryption and Compression options
                    save_kwargs = {
                        "garbage": 4, # Max garbage collection
                        "deflate": True,
                        "clean": True
                    }
                    
                    if options.get('compress_level') == 'high':
                        # More aggressive optimization flags
                        save_kwargs["deflate"] = True
                        save_kwargs["deflate_images"] = True
                        save_kwargs["deflate_fonts"] = True
                        save_kwargs["garbage"] = 4
                    
                    encrypt_pwd = options.get('encrypt_password')
                    if encrypt_pwd:
                        save_kwargs["encryption"] = fitz.PDF_ENCRYPT_AES_256
                        save_kwargs["owner_pw"] = encrypt_pwd
                        save_kwargs["user_pw"] = encrypt_pwd
                        
                    # Save with optimization and/or encryption
                    doc.save(temp_out, **save_kwargs)
                    doc.close()
                    
                    # Verify output PDF
                    try:
                        verify_doc = fitz.open(temp_out)
                        verify_doc.close()
                    except Exception as e:
                        raise ValueError(f"Generated PDF verification failed: {str(e)}")

                else:
                    raise ValueError(f"Unsupported conversion {source_ext} to {target_ext}")

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
                error_message=f"PyMuPDF conversion failed: {str(e)}",
                duration_seconds=time.time() - start_time
            )
