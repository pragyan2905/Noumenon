import time
import tempfile
import shutil
import subprocess
import os
from pathlib import Path

from src.core.interfaces.engine import ConversionEngine
from src.core.models.conversion import ConversionRequest, ConversionResult

class FFMpegEngine(ConversionEngine):
    """
    Handles audio/video conversions using FFmpeg (provided by imageio_ffmpeg).
    """
    
    AUDIO_FORMATS = {'mp3', 'wav', 'aac', 'flac', 'ogg', 'm4a'}
    VIDEO_FORMATS = {'mp4', 'mkv', 'avi', 'mov', 'webm'}
    IMAGE_FORMATS = {'gif'}
    ALL_FORMATS = AUDIO_FORMATS.union(VIDEO_FORMATS).union(IMAGE_FORMATS)

    def __init__(self):
        try:
            import imageio_ffmpeg
            self.ffmpeg_path = imageio_ffmpeg.get_ffmpeg_exe()
            self.available = True
        except ImportError:
            self.ffmpeg_path = "ffmpeg"
            try:
                subprocess.run([self.ffmpeg_path, "-version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
                self.available = True
            except (subprocess.CalledProcessError, FileNotFoundError):
                self.available = False

    def can_convert(self, source_format: str, target_format: str) -> bool:
        if source_format in self.VIDEO_FORMATS or source_format in self.AUDIO_FORMATS:
            if target_format in self.ALL_FORMATS:
                return True
        return False

    def get_quality_score(self) -> str:
        return 'A'

    def convert(self, request: ConversionRequest) -> ConversionResult:
        if not self.available:
            return ConversionResult(
                success=False,
                error_message="FFmpeg is not installed or imageio-ffmpeg is missing."
            )
            
        target_ext = request.output_format.lower().lstrip('.')
        warnings = []
        start_time = time.time()
        
        try:
            paths = getattr(request, 'input_paths', None)
            if not paths:
                paths = [request.input_path]
                
            is_batch = len(paths) > 1
            if is_batch:
                output_path = request.output_directory / "batch_media"
                output_path.mkdir(exist_ok=True)
            else:
                output_path = request.output_directory / f"{request.input_path.stem}.{target_ext}"
                
            for input_p in paths:
                if not input_p.exists():
                    warnings.append(f"Input file not found: {input_p.name}")
                    continue
                    
                source_ext = input_p.suffix.lower().lstrip('.')
                
                fd, temp_out_path = tempfile.mkstemp(suffix=f".{target_ext}")
                os.close(fd)
                os.unlink(temp_out_path)
                temp_out = Path(temp_out_path)
                
                try:
                    cmd = [self.ffmpeg_path, "-y"]
                    options = request.options or {}
                    
                    # Trimming (must be before -i for fast seeking)
                    if options.get('trim_start'):
                        cmd.extend(["-ss", str(options['trim_start'])])
                    
                    cmd.extend(["-i", str(input_p)])
                    
                    if options.get('trim_end'):
                        cmd.extend(["-to", str(options['trim_end'])])
                        
                    # Extract Audio
                    if target_ext in self.AUDIO_FORMATS and source_ext in self.VIDEO_FORMATS:
                        if target_ext == 'mp3':
                            cmd.extend(["-vn", "-c:a", "libmp3lame"])
                            if options.get('compress_level') == 'high':
                                cmd.extend(["-b:a", "64k"])
                            else:
                                cmd.extend(["-b:a", "192k"])
                        else:
                            cmd.extend(["-vn"])
                            
                    # GIF Conversion
                    elif target_ext == 'gif':
                        cmd.extend(["-vf", "fps=10,scale=320:-1:flags=lanczos,split[s0][s1];[s0]palettegen[p];[s1][p]paletteuse"])
                        
                    # Video Compression
                    elif target_ext in self.VIDEO_FORMATS:
                        if options.get('compress_level') == 'high':
                            cmd.extend(["-vcodec", "libx264", "-crf", "35", "-preset", "veryfast", "-b:a", "96k"])
                        else:
                            cmd.extend(["-vcodec", "libx264", "-crf", "23", "-preset", "medium"])
                            
                    cmd.append(str(temp_out))
                    
                    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                    
                    if result.returncode != 0:
                        raise RuntimeError(f"FFmpeg failed: {result.stderr}")
                    
                    if not temp_out.exists() or temp_out.stat().st_size == 0:
                        raise RuntimeError("Generated media file is unexpectedly empty or failed.")
                        
                    if is_batch:
                        final_item_path = output_path / f"{input_p.stem}.{target_ext}"
                    else:
                        final_item_path = output_path
                        
                    shutil.move(str(temp_out), str(final_item_path))
                    
                except Exception as e:
                    if temp_out.exists():
                        temp_out.unlink()
                    warnings.append(f"Failed to process {input_p.name}: {str(e)}")
                    
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
                error_message=f"Media conversion failed: {str(e)}",
                duration_seconds=time.time() - start_time
            )
