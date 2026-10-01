import time
import tempfile
import shutil
import zipfile
import tarfile
from pathlib import Path

from src.core.interfaces.engine import ConversionEngine
from src.core.models.conversion import ConversionRequest, ConversionResult

class ArchiveEngine(ConversionEngine):
    """
    Handles robust archive operations (zip, tar, gz, bz2, xz).
    Focuses on standard Python libraries to keep dependencies minimal.
    """
    
    def __init__(self):
        self.formats = {'zip', 'tar', 'gz', 'bz2', 'xz', 'tgz'}

    def can_convert(self, source_format: str, target_format: str) -> bool:
        # Archives are generally unarchived into a directory, or a directory is archived.
        # For our ConversionEngine, let's treat "target_format='extract'" as unarchiving,
        # or archive-to-archive conversion.
        if source_format in self.formats and target_format == 'extract':
            return True
        if source_format == 'dir' and target_format in self.formats:
            return True
        # Direct format conversion (e.g. zip to tar)
        if source_format in self.formats and target_format in self.formats:
            return True
        return False

    def get_quality_score(self) -> str:
        return 'A'

    def convert(self, request: ConversionRequest) -> ConversionResult:
        source_ext = request.input_path.suffix.lower().lstrip('.')
        
        # Determine source type (dir or archive)
        if request.input_path.is_dir():
            source_ext = 'dir'
            
        target_ext = request.output_format.lower().lstrip('.')
        
        start_time = time.time()
        
        try:
            if not request.input_path.exists():
                return ConversionResult(success=False, error_message=f"Input path not found: {request.input_path}")
                
            warnings = []
            
            # Directory -> Archive
            if source_ext == 'dir' and target_ext in self.formats:
                output_path = request.output_directory / f"{request.input_path.name}.{target_ext}"
                fd, temp_out_path = tempfile.mkstemp(suffix=f".{target_ext}")
                import os
                os.close(fd)
                temp_out = Path(temp_out_path)
                
                try:
                    if target_ext == 'zip':
                        with zipfile.ZipFile(temp_out, 'w', zipfile.ZIP_DEFLATED) as zf:
                            for root, _, files in os.walk(request.input_path):
                                for file in files:
                                    file_path = Path(root) / file
                                    arcname = file_path.relative_to(request.input_path)
                                    zf.write(file_path, arcname)
                    else: # tar variants
                        mode = 'w'
                        if target_ext in ('gz', 'tgz'):
                            mode = 'w:gz'
                        elif target_ext == 'bz2':
                            mode = 'w:bz2'
                        elif target_ext == 'xz':
                            mode = 'w:xz'
                            
                        with tarfile.open(temp_out, mode) as tf:
                            tf.add(request.input_path, arcname=request.input_path.name)
                            
                    # Move to final
                    shutil.move(str(temp_out), str(output_path))
                    
                except Exception as e:
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
                
            # Archive -> Extract
            elif source_ext in self.formats and target_ext == 'extract':
                output_dir = request.output_directory / request.input_path.stem
                output_dir.mkdir(parents=True, exist_ok=True)
                
                if source_ext == 'zip':
                    with zipfile.ZipFile(request.input_path, 'r') as zf:
                        zf.extractall(output_dir)
                else: # tar variants
                    with tarfile.open(request.input_path, 'r:*') as tf:
                        # Basic safety check against path traversal
                        for member in tf.getmembers():
                            if member.name.startswith('/') or '..' in member.name:
                                warnings.append(f"Skipped unsafe path in tar: {member.name}")
                            else:
                                tf.extract(member, output_dir)
                                
                return ConversionResult(
                    success=True,
                    output_path=output_dir, # Note: returning a directory
                    engine_used=self.__class__.__name__,
                    duration_seconds=time.time() - start_time,
                    warnings=warnings
                )
                
            # Archive -> Archive (Extract then compress)
            elif source_ext in self.formats and target_ext in self.formats:
                with tempfile.TemporaryDirectory() as temp_dir:
                    temp_dir_path = Path(temp_dir)
                    
                    # 1. Extract
                    if source_ext == 'zip':
                        with zipfile.ZipFile(request.input_path, 'r') as zf:
                            zf.extractall(temp_dir_path)
                    else:
                        with tarfile.open(request.input_path, 'r:*') as tf:
                            for member in tf.getmembers():
                                if not (member.name.startswith('/') or '..' in member.name):
                                    tf.extract(member, temp_dir_path)
                                    
                    # 2. Compress
                    output_path = request.output_directory / f"{request.input_path.stem}.{target_ext}"
                    fd, temp_out_path = tempfile.mkstemp(suffix=f".{target_ext}")
                    import os
                    os.close(fd)
                    temp_out = Path(temp_out_path)
                    
                    try:
                        if target_ext == 'zip':
                            with zipfile.ZipFile(temp_out, 'w', zipfile.ZIP_DEFLATED) as zf:
                                for root, _, files in os.walk(temp_dir_path):
                                    for file in files:
                                        file_path = Path(root) / file
                                        arcname = file_path.relative_to(temp_dir_path)
                                        zf.write(file_path, arcname)
                        else: # tar variants
                            mode = 'w'
                            if target_ext in ('gz', 'tgz'):
                                mode = 'w:gz'
                            elif target_ext == 'bz2':
                                mode = 'w:bz2'
                            elif target_ext == 'xz':
                                mode = 'w:xz'
                                
                            with tarfile.open(temp_out, mode) as tf:
                                # We want to add the contents of temp_dir_path directly without the temp dir name
                                for item in temp_dir_path.iterdir():
                                    tf.add(item, arcname=item.name)
                                
                        shutil.move(str(temp_out), str(output_path))
                    except Exception as e:
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
                
            else:
                 raise ValueError(f"Unsupported archive operation {source_ext} to {target_ext}")
                 
        except Exception as e:
            return ConversionResult(
                success=False,
                error_message=f"Archive operation failed: {str(e)}",
                duration_seconds=time.time() - start_time
            )
