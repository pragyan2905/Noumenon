import sys
from pathlib import Path
import streamlit as st

project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

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

@st.cache_resource
def setup_backend():
    registry = EngineRegistry()
    registry.register(PillowImageEngine())
    registry.register(PyMuPdfEngine())
    registry.register(DataEngine())
    registry.register(TextEngine())
    registry.register(TesseractOcrEngine())
    registry.register(FFMpegEngine())
    registry.register(ArchiveEngine())
    # Register more engines here as we build them (PDF, OCR, etc.)
    router = ConversionRouter(registry)
    return router

router = setup_backend()

st.set_page_config(page_title="LocalConvert Core", page_icon="🗂️")

st.title("LocalConvert 🗂️")
st.subheader("Private file conversion. Core reliable features only.")

st.markdown("---")

uploaded_file = st.file_uploader("Drop your file here", type=['pdf', 'png', 'jpg', 'jpeg', 'webp', 'tiff', 'bmp', 'gif', 'csv', 'tsv', 'json', 'yaml', 'toml', 'xml', 'txt', 'md', 'html', 'mp3', 'wav', 'mp4', 'avi', 'mkv', 'zip', 'tar', 'gz'])

if uploaded_file is not None:
    input_ext = uploaded_file.name.split('.')[-1].lower()
    
    st.write(f"**Selected File:** `{uploaded_file.name}`")
    
    # Comprehensive output format selection
    output_format = st.selectbox("Convert to:", [
        "png", "jpg", "webp", "pdf", 
        "csv", "json", "yaml", "xml", "toml",
        "txt", "md", "html",
        "mp3", "wav", "mp4",
        "zip", "extract"
    ])
    
    if st.button("Convert"):
        temp_input = Path("/tmp") / uploaded_file.name
        with open(temp_input, "wb") as f:
            f.write(uploaded_file.getbuffer())
            
        request = ConversionRequest(
            input_path=temp_input,
            output_format=output_format,
            output_directory=Path("/tmp")
        )
        
        with st.spinner(f"Converting {input_ext.upper()} to {output_format.upper()}..."):
            result = router.route_and_convert(request)
            
        if result.success:
            st.success(f"✅ Conversion Succeeded!")
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Engine", result.engine_used)
            with col2:
                if result.duration_seconds is not None:
                    st.metric("Duration", f"{result.duration_seconds:.2f}s")
            
            if result.warnings:
                for w in result.warnings:
                    st.warning(w)
            
            with open(result.output_path, "rb") as file_data:
                st.download_button(
                    label=f"⬇️ Download {result.output_path.name}",
                    data=file_data,
                    file_name=result.output_path.name,
                    mime="application/octet-stream"
                )
        else:
            st.error(f"❌ Conversion Failed!")
            st.error(f"Error: {result.error_message}")
            if result.warnings:
                for w in result.warnings:
                    st.warning(w)

st.markdown("---")
st.caption("*LocalConvert — All processing happens locally on your device. Your files are never uploaded.*")
