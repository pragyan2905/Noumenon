# Noumenon

**Private file conversion. Everything stays on your device.**

Noumenon is a privacy-first, local-only, high-quality file conversion utility for macOS, Windows, and Linux. 
The long-term goal is to create a local desktop alternative to cloud services such as iLovePDF, Smallpdf, and CloudConvert, with a critical distinction: User files must never need to be uploaded to a remote third-party server.

## Core Capabilities

- Image Processing: Scale, crop, rotate, adjust DPI, convert to grayscale, and dynamically strip EXIF metadata for privacy. Supports PNG, JPG, WebP, TIFF, GIF, BMP.
- Document Manipulation: Extract PDF pages, rotate pages, unlock encrypted PDFs, and apply new encryption passwords natively without quality loss. Supports PDF, DOCX, TXT, MD, HTML.
- Data Conversion: Parse and convert complex datasets across CSV, JSON, YAML, XML, TOML, TSV, Excel (XLSX), and Parquet.
- Media Encoding: Transcode video and audio formats natively via FFmpeg. Supports MP4, MP3, WAV, MKV, AVI, MOV, AAC, FLAC.
- Archive Utilities: Pack and extract archives natively (ZIP, TAR, GZ, BZ2).

## Architecture

Noumenon operates as a decoupled architecture:
1. Frontend: A React/Vite modular dashboard designed for high performance and an elegant user experience.
2. Backend: A FastAPI engine serving as the core router, instantly analyzing uploaded blobs and routing them to specialized conversion engines (Pillow, PyMuPDF, Pandas, FFmpeg).

## Deployment

Noumenon is designed to be easily deployed to modern cloud infrastructure (such as Render, Fly.io, or AWS) using Docker. The deployment process utilizes a multi-stage Dockerfile that natively compiles the React frontend and packages it with the Python backend into a single unified container.

1. Clone the repository.
2. Push to your cloud provider using Docker runtime.
3. The server will natively install system dependencies and compile the static assets automatically.

## Development

See PLAN.md and ARCHITECTURE.md for details on the development process and roadmap.
