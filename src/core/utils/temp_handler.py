import tempfile
import shutil
from pathlib import Path
from contextlib import contextmanager

@contextmanager
def safe_temp_output(target_ext: str, final_output_path: Path):
    """
    Context manager that safely provisions a temporary file,
    yields it, and if no exception occurs, moves it to the final destination.
    If an exception occurs, it cleans up the temporary file.
    
    Usage:
        with safe_temp_output(target_ext, final_output_path) as temp_out:
            # write to temp_out
            verify(temp_out)
    """
    fd, temp_out_path = tempfile.mkstemp(suffix=f".{target_ext}")
    import os
    os.close(fd)
    temp_out = Path(temp_out_path)
    
    try:
        yield temp_out
        
        # Verify it has size
        if temp_out.exists() and temp_out.stat().st_size == 0:
            raise ValueError("Generated output file is unexpectedly empty.")
            
        shutil.move(str(temp_out), str(final_output_path))
    except Exception as e:
        if temp_out.exists():
            temp_out.unlink()
        raise e
