import time
import tempfile
import shutil
import subprocess
from pathlib import Path

from src.core.interfaces.engine import ConversionEngine
from src.core.models.conversion import ConversionRequest, ConversionResult

class FFMpegEngine(ConversionEngine):
    """
    Handles audio/video conversions using FFmpeg.
    Requires ffmpeg to be installed on the system.
    """
    
    AUDIO_FORMATS = {'mp3', 'wav', 'aac', 'flac', 'ogg', 'm4a'}
    VIDEO_FORMATS = {'mp4', 'mkv', 'avi', 'mov', 'webm'}
    ALL_FORMATS = AUDIO_FORMATS.union(VIDEO_FORMATS)

    def __init__(self):
        try:
            subprocess.run(["ffmpeg", "-version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
            self.available = True
        except (subprocess.CalledProcessError, FileNotFoundError):
            self.available = False

    def can_convert(self, source_format: str, target_format: str) -> bool:
        if not self.available:
            return False
        # Can extract audio from video, convert audio->audio, video->video
        if source_format in self.ALL_FORMATS and target_format in self.ALL_FORMATS:
            return True
        return False

    def get_quality_score(self) -> str:
        return 'A'

    def convert(self, request: ConversionRequest) -> ConversionResult:
        source_ext = request.input_path.suffix.lower().lstrip('.')
        target_ext = request.output_format.lower().lstrip('.')
        
        start_time = time.time()
        
        try:
            if not request.input_path.exists():
                return ConversionResult(success=False, error_message=f"Input file not found: {request.input_path}")
            
            fd, temp_out_path = tempfile.mkstemp(suffix=f".{target_ext}")
            import os
            os.close(fd)
            # Remove because ffmpeg creates it, but we needed a guaranteed unique path
            os.unlink(temp_out_path)
            temp_out = Path(temp_out_path)
            
            try:
                cmd = ["ffmpeg", "-y", "-i", str(request.input_path)]
                
                options = request.options or {}
                
                # If target is audio and source is video, extract audio
                if target_ext in self.AUDIO_FORMATS and source_ext in self.VIDEO_FORMATS:
                    cmd.extend(["-vn", "-c:a", "libmp3lame" if target_ext == 'mp3' else "copy"])
                
                cmd.append(str(temp_out))
                
                result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                
                if result.returncode != 0:
                    raise RuntimeError(f"FFmpeg failed: {result.stderr}")
                
                if not temp_out.exists():
                    raise RuntimeError("FFmpeg did not produce the expected output file.")
                
                # Verify output file isn't empty
                if temp_out.stat().st_size == 0:
                    raise ValueError("Generated media file is unexpectedly empty.")
                    
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
                error_message=f"Media conversion failed: {str(e)}",
                duration_seconds=time.time() - start_time
            )
