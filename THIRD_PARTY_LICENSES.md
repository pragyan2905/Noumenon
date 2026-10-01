# Third-Party Licenses

This document lists the third-party dependencies used by LocalConvert
and their license terms. All conversion processing is local — no files
are uploaded to remote servers.

## Python Packages

### PyMuPDF (fitz / pymupdf)
- **License**: AGPL-3.0 (free for open-source use; commercial license available from Artifex)
- **Purpose**: PDF parsing, text extraction, page rendering
- **Note**: AGPL requires derivative works to be open-source. If LocalConvert is distributed commercially, a commercial license from Artifex Software must be obtained.
- **URL**: https://pymupdf.readthedocs.io/

### python-docx
- **License**: MIT
- **Purpose**: DOCX file generation and manipulation
- **URL**: https://python-docx.readthedocs.io/

### pdf2docx
- **License**: GPL-3.0
- **Purpose**: Legacy semantic PDF→DOCX conversion (being phased out)
- **Note**: GPL-3.0 requires distribution of source code with the application.
- **URL**: https://github.com/dothinking/pdf2docx

### Pillow (PIL)
- **License**: HPND (Historical Permission Notice and Disclaimer)
- **Purpose**: Image format conversion
- **URL**: https://python-pillow.org/

### Streamlit
- **License**: Apache 2.0
- **Purpose**: Development UI prototype
- **Note**: Will be replaced by PySide6 in production.
- **URL**: https://streamlit.io/

### PySide6 (future)
- **License**: LGPL-3.0 / Commercial
- **Purpose**: Desktop application framework (planned)
- **URL**: https://doc.qt.io/qtforpython/

## Optional / Future Dependencies

### Tesseract OCR
- **License**: Apache 2.0
- **Purpose**: OCR for scanned documents
- **Note**: Tesseract is a separate binary; not bundled.
- **URL**: https://github.com/tesseract-ocr/tesseract

### FFmpeg
- **License**: LGPL-2.1+ / GPL (depending on build options)
- **Purpose**: Media file conversion
- **Note**: Not bundled; used as external tool.
- **URL**: https://ffmpeg.org/

### MinerU (optional benchmark)
- **License**: AGPL-3.0
- **Purpose**: Advanced document layout analysis (benchmark only)
- **Note**: Would require separate installation. Not bundled.

### Docling (optional benchmark)
- **License**: MIT
- **Purpose**: Structured document parsing (benchmark only)

## Key Licensing Considerations

1. **PyMuPDF (AGPL)**: Core dependency. Open-source distribution is fine.
   Commercial distribution requires a separate commercial license from Artifex.

2. **pdf2docx (GPL-3.0)**: Being phased out in favor of the custom
   reconstruction pipeline. Once fully replaced, this dependency can be removed.

3. **Privacy**: All processing is local. No data is sent externally.
   No telemetry. No analytics. Works fully offline.
