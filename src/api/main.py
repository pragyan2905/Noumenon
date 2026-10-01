import sys
from pathlib import Path
from typing import Optional, Dict, Any
import json
import tempfile
import shutil

# Ensure Python can find the 'src' module
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware

from src.core.models.conversion import ConversionRequest
from src.core.registry.engine_registry import EngineRegistry
from src.core.router.conversion_router import ConversionRouter

from src.engines.image.pillow_engine import PillowImageEngine
from src.engines.pdf.pymupdf_engine import PyMuPdfEngine
from src.engines.data.data_engine import DataEngine
from src.engines.text.text_engine import TextEngine
from src.engines.ocr.tesseract_engine import TesseractOcrEngine
from src.engines.media.ffmpeg_engine import FFMpegEngine
from src.engines.archive.archive_engine import ArchiveEngine

app = FastAPI(title="LocalConvert API")

# Setup CORS for the React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Since it's a local app, we can allow all origins for dev
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize the conversion backend
registry = EngineRegistry()
registry.register(PillowImageEngine())
registry.register(PyMuPdfEngine())
registry.register(DataEngine())
registry.register(TextEngine())
registry.register(TesseractOcrEngine())
registry.register(FFMpegEngine())
registry.register(ArchiveEngine())
router = ConversionRouter(registry)


@app.post("/api/convert")
async def convert_file(
    file: UploadFile = File(...),
    output_format: str = Form(...),
    options: str = Form("{}")
):
    try:
        parsed_options = json.loads(options)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid options JSON")

    # Create a temporary directory for processing this request
    with tempfile.TemporaryDirectory() as temp_dir_str:
        temp_dir = Path(temp_dir_str)
        
        # Save the uploaded file
        input_path = temp_dir / file.filename
        with open(input_path, "wb") as f:
            shutil.copyfileobj(file.file, f)
            
        request = ConversionRequest(
            input_path=input_path,
            output_format=output_format,
            output_directory=temp_dir,
            options=parsed_options
        )
        
        result = router.route_and_convert(request)
        
        if not result.success:
            raise HTTPException(status_code=400, detail=result.error_message)
            
        if result.output_path.is_dir():
            # If it's a directory (like archive extraction), zip it up
            zip_path = temp_dir / f"{result.output_path.name}_extracted"
            shutil.make_archive(str(zip_path), 'zip', result.output_path)
            final_path = temp_dir / f"{result.output_path.name}_extracted.zip"
        else:
            final_path = result.output_path
            
        # We need to copy the final file out of the temp directory 
        # so FileResponse can serve it after this function exits and cleans up temp_dir
        serve_dir = Path("/tmp/localconvert_serve")
        serve_dir.mkdir(exist_ok=True)
        serve_path = serve_dir / final_path.name
        shutil.copy2(final_path, serve_path)
        
        headers = {}
        if result.warnings:
            headers["X-Conversion-Warnings"] = json.dumps(result.warnings)
        
        return FileResponse(
            path=serve_path,
            filename=final_path.name,
            headers=headers
        )

@app.get("/api/health")
def health_check():
    return {"status": "ok"}
