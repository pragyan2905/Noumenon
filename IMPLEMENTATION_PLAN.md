# LocalConvert — Implementation Plan

Build the application incrementally. Do NOT implement the entire product at once.

The immediate objective is:

> **Build a reliable local PDF → DOCX conversion system with document analysis, multiple conversion strategies, pagination control, and automated fidelity validation.**

Only after this works reliably should the application expand into a general-purpose file converter.

---

# PHASE 0 — ENVIRONMENT + TECHNICAL AUDIT

Before writing application code, inspect the development environment.

Determine:

- OS
- CPU architecture
- Python version
- PySide6 availability
- LibreOffice availability
- FFmpeg availability
- Tesseract availability
- qpdf availability
- PyMuPDF availability
- pdf2docx availability
- available PDF rendering engines
- packaging/build tools

Create:

```text
scripts/
    check_environment.py
```

The script should produce something like:

```text
LocalConvert Environment

OS: macOS
Architecture: arm64
Python: 3.x

Python packages:
✓ PySide6
✓ PyMuPDF
✓ Pillow
✓ python-docx

Native tools:
✓ LibreOffice
✓ qpdf
✓ Tesseract
✓ FFmpeg

Status:
READY / MISSING DEPENDENCIES
```

Do not silently assume dependencies exist.

---

# PHASE 1 — PROJECT FOUNDATION

Create a clean modular project.

Suggested structure:

```text
localconvert/
│
├── src/
│   └── localconvert/
│       ├── core/
│       │   ├── models/
│       │   ├── registry/
│       │   ├── router/
│       │   ├── jobs/
│       │   └── errors/
│       │
│       ├── detection/
│       │   ├── file_type.py
│       │   ├── pdf_analysis.py
│       │   └── layout_analysis.py
│       │
│       ├── engines/
│       │   ├── pdf/
│       │   ├── docx/
│       │   ├── office/
│       │   ├── image/
│       │   └── ocr/
│       │
│       ├── converters/
│       │   └── pdf_to_docx/
│       │
│       ├── validation/
│       │   ├── file_validator.py
│       │   ├── text_validator.py
│       │   ├── visual_validator.py
│       │   ├── pagination_validator.py
│       │   └── fidelity_report.py
│       │
│       ├── infrastructure/
│       │   ├── filesystem.py
│       │   ├── subprocess.py
│       │   └── tempfiles.py
│       │
│       ├── cli/
│       │   └── main.py
│       │
│       └── ui/
│           ├── main_window.py
│           ├── drop_zone.py
│           ├── conversion_queue.py
│           └── results.py
│
├── tests/
├── fixtures/
├── scripts/
├── docs/
├── requirements.txt
└── README.md
```

Do not over-engineer individual classes. Maintain clear separation of responsibilities.

---

# PHASE 2 — CONVERSION CORE

Before building the GUI, create the actual conversion framework.

Implement:

```python
ConversionRequest
ConversionResult
ConversionEngine
ConversionRegistry
ConversionRouter
```

For example:

```python
class ConversionEngine:
    def can_handle(self, request, analysis):
        ...

    def convert(self, request):
        ...

    def health_check(self):
        ...
```

The GUI must never directly call `pdf2docx`, LibreOffice, PyMuPDF, etc.

The GUI talks to the conversion core.

The conversion core talks to engines.

Architecture:

```text
GUI
 ↓
Conversion Core
 ↓
Router
 ↓
Engine
```

---

# PHASE 3 — FILE DETECTION

Implement reliable input detection.

Do not trust only:

```python
Path(file).suffix
```

Use:

- extension
- MIME information where available
- magic/signature information
- structural inspection

Return:

```text
FileInfo
    format
    mime_type
    size
    valid
```

Test with:

- correctly named files
- incorrectly named files
- corrupted files
- unsupported files

---

# PHASE 4 — PDF ANALYZER

This is the most important component before attempting advanced PDF → DOCX.

Create:

```text
PDFAnalyzer
```

It should inspect:

- page count
- page dimensions
- orientation
- text blocks
- bounding boxes
- font information where available
- images
- tables where detectable
- links
- annotations
- forms
- scanned pages
- OCR layers
- rotations
- metadata
- approximate column count
- text density
- layout complexity

Produce a structured result such as:

```text
PDF Analysis

Pages: 17
Layout: 2-column
Type: born-digital
Text: present
Images: 11
Tables: 4
Links: 36
Complexity: HIGH
Scanned pages: 0
```

Do NOT try to make the analyzer perfect initially.

It only needs to classify documents well enough to route them correctly.

---

# PHASE 5 — DOCUMENT COMPLEXITY CLASSIFIER

Classify PDFs:

```text
SIMPLE
STRUCTURED
COMPLEX
SCANNED
```

Possible signals:

- number of columns
- number of text blocks
- density of positioned text
- number of fonts
- images
- tables
- unusual coordinates
- overlapping elements
- OCR-only content

For example:

```text
Simple:
single-column
mostly flowing text

Structured:
headings + tables + images

Complex:
two-column academic layout
many positioned objects
complex figures/tables

Scanned:
little/no text layer
```

Do not use this classification as an artificial limitation.

It should determine the **strategy**, not simply reject complex documents.

---

# PHASE 6 — BASELINE PDF → DOCX ENGINE

Implement a baseline engine first.

Use a mature existing solution where appropriate, such as `pdf2docx`, to establish a baseline.

This engine is NOT the final solution.

Record:

- conversion time
- success/failure
- output page count
- extracted text
- visual similarity
- blank pages
- structural issues

The purpose of this stage is benchmarking.

Create:

```text
BaselineEngine
```

Do not bury its implementation throughout the project.

---

# PHASE 7 — FIX PAGINATION FIRST

The current system has a major pagination failure.

Our 17-page academic test produces unwanted blank/mostly blank pages and incorrect content flow.

Investigate generated DOCX structure for:

- explicit page breaks
- section breaks
- `pageBreakBefore`
- `keepNext`
- `keepLines`
- empty paragraphs
- fixed-height tables
- non-splittable rows
- incorrect page dimensions
- incorrect margins
- excessive paragraph spacing
- incorrect DOCX column configuration
- page-sized layout containers

Build a diagnostic script:

```text
scripts/
    inspect_docx_layout.py
```

It should report:

```text
DOCX Layout Diagnostics

Sections: 18
Page breaks: 17
Section breaks: 17
Empty paragraphs: 132
Fixed-height containers: 4
Two-column sections: 0

Potential problems:
HIGH — excessive section/page breaks
HIGH — document does not use native two-column structure
```

Fix the actual causes rather than adding hacks such as deleting every second page afterward.

---

# PHASE 8 — LAYOUT-AWARE PDF → DOCX ENGINE

Now implement the real conversion strategy.

The engine should use positional PDF information.

Pipeline:

```text
PDF
 ↓
extract positioned text blocks
 ↓
detect columns
 ↓
sort blocks into reading order
 ↓
group blocks into paragraphs
 ↓
identify headings
 ↓
identify figures/images
 ↓
identify tables
 ↓
reconstruct DOCX
```

For two-column documents:

```text
Page
 ├── Header
 ├── Column 1
 │    ├── paragraph
 │    ├── paragraph
 │    └── figure
 └── Column 2
      ├── paragraph
      ├── paragraph
      └── table
```

Use actual DOCX structural features wherever possible.

Avoid representing an entire PDF page as a giant image or page-sized container.

---

# PHASE 9 — READING ORDER

Build a separate reading-order component.

Do not assume the raw order returned by PDF extraction represents reading order.

Implement heuristics based on:

- x/y coordinates
- column boundaries
- block position
- font information
- block proximity
- heading detection
- image locations
- page boundaries

Test specifically on:

- one-column documents
- two-column documents
- sidebars
- footnotes
- captions
- references

The system should be modular so the reading-order algorithm can be improved later.

---

# PHASE 10 — FIGURES + IMAGES

Implement extraction and placement of images.

Preserve where possible:

- original image
- resolution
- aspect ratio
- location
- approximate size

Do not unnecessarily rasterize the entire page.

A figure should become an image/appropriate object in the DOCX where possible.

Test:

- inline images
- figures with captions
- full-width figures
- multiple images
- images spanning columns

---

# PHASE 11 — TABLE HANDLING

Implement basic table detection and reconstruction.

Initially focus on:

- rectangular tables
- rows/columns
- cell text
- basic formatting

Do not promise perfect reconstruction for arbitrary graphical tables.

For unsupported/complex tables:

- preserve visually where possible
- report the limitation

The validator must detect whether a table was lost.

---

# PHASE 12 — SCANNED PDF PIPELINE

Implement a separate scanned-document strategy.

Pipeline:

```text
PDF
 ↓
detect image-only pages
 ↓
OCR
 ↓
text layer / document reconstruction
 ↓
DOCX
```

Use OCR tooling locally.

Do not send documents to external APIs.

Maintain two distinct paths:

```text
Born-digital PDF
        ↓
layout/text reconstruction

Scanned PDF
        ↓
OCR + reconstruction
```

---

# PHASE 13 — FIDELITY VALIDATION

This phase is mandatory.

After generating the DOCX:

```text
DOCX
 ↓
render locally to PDF
 ↓
compare with source PDF
```

Build:

```text
FidelityValidator
```

Checks:

### File

- output exists
- output opens

### Pagination

- source pages
- output pages
- blank pages
- suspicious pages

### Text

- character count
- word count
- important terms
- similarity
- missing content

### Visual

- page rendering
- perceptual similarity
- layout regions

### Structural

- images
- links
- metadata
- fonts where practical

Output:

```text
Conversion Fidelity Report

Pages:
17 → 18

Blank pages:
1

Text similarity:
97.4%

Images:
10 / 11

Visual similarity:
HIGH

Pagination:
FAIL

Overall:
NOT ACCEPTABLE
```

---

# PHASE 14 — BLANK PAGE DETECTOR

Implement a dedicated detector.

For each rendered page calculate:

- text amount
- number of images
- occupied area
- foreground pixel ratio

Flag suspicious pages.

Example:

```text
Page 7

Text: 0 characters
Images: 0
Occupied area: 0.4%

→ SUSPICIOUS BLANK PAGE
```

Do not automatically delete suspicious pages.

First identify why they exist.

---

# PHASE 15 — REGRESSION TEST CORPUS

Create:

```text
fixtures/
    pdf/
        simple/
        two_column/
        scanned/
        tables/
        figures/
        multilingual/
        difficult/
```

Use the current 17-page academic paper as a permanent regression test.

Record expected properties:

```text
17 pages
two-column layout
text layer present
figures present
tables present
references present
```

Add additional real-world documents over time.

Every code change affecting conversion must run against this corpus.

---

# PHASE 16 — MULTI-ENGINE ROUTING

Once the baseline and layout-aware engines exist, implement routing.

Example:

```text
PDF
 ↓
Analyzer
 ↓
Simple
 → baseline/simple engine

Structured
 → layout-aware engine

Complex
 → layout-aware engine
 → fallback strategy if required

Scanned
 → OCR engine
```

Routing should consider:

- expected fidelity
- engine availability
- file characteristics
- speed
- historical success rate

Do not pick an engine arbitrarily.

---

# PHASE 17 — FALLBACK SYSTEM

Implement controlled fallback.

Example:

```text
Engine A
 ↓
conversion
 ↓
validation
 ↓
FAIL
 ↓
Engine B
 ↓
validation
 ↓
PASS
 ↓
return
```

If all strategies fail:

```text
Conversion could not achieve reliable editable output.

Reason:
Complex two-column layout could not be reconstructed
within the configured fidelity threshold.

Recommended:
Maximum visual-fidelity mode.
```

Never silently return corrupted output.

---

# PHASE 18 — USER MODES

Add:

```text
PDF → DOCX

[ Editable ]
[ Layout Preserved ]
[ Maximum Visual Fidelity ]
```

### Editable

Prioritize semantic/editable structure.

### Layout Preserved

Prioritize appearance while maintaining real editable content where feasible.

### Maximum Visual Fidelity

Allow hybrid/rasterized elements where necessary.

Clearly communicate reduced editability.

---

# PHASE 19 — CLI

Before the full GUI, make the conversion system usable through CLI.

Example:

```bash
localconvert input.pdf --to docx
```

and:

```bash
localconvert input.pdf --to docx --mode editable
```

and:

```bash
localconvert input.pdf --to docx --mode layout
```

and:

```bash
localconvert input.pdf --analyze
```

and:

```bash
localconvert input.pdf --validate output.docx
```

CLI and GUI must use the same conversion core.

---

# PHASE 20 — DESKTOP GUI

Only after the conversion core is reliable, build the PySide6 interface.

Main screen:

```text
LOCALCONVERT

Private • Local • Offline

┌─────────────────────────────┐
│                             │
│       Drop files here       │
│                             │
│        or Browse            │
│                             │
└─────────────────────────────┘
```

Then:

```text
report.pdf

Convert to:
[ DOCX ]

Mode:
[ Layout Preserved ]

[ Convert ]
```

For complex PDFs show:

```text
Detected:
Complex 2-column document

Recommended mode:
Layout Preserved

Potential limitations:
Some elements may require manual adjustment.
```

---

# PHASE 21 — JOB SYSTEM

Implement background conversion workers.

Requirements:

- no UI blocking
- queue
- progress
- cancellation
- retry
- bounded concurrency
- error state
- completion state

Example:

```text
Queued
  ↓
Analyzing
  ↓
Converting
  ↓
Validating
  ↓
Completed
```

---

# PHASE 22 — PRIVACY

Verify the architecture is completely local.

Test with network disabled.

Conversion should continue to work.

Ensure:

- no file uploads
- no cloud APIs
- no telemetry
- no remote OCR
- no remote conversion
- no document contents in logs

Add:

```text
docs/PRIVACY.md
```

and explain exactly what the application does locally.

---

# PHASE 23 — PACKAGING

Once the application is stable:

## macOS

Build:

```text
LocalConvert-macOS-arm64.dmg
```

and later:

```text
LocalConvert-macOS-x64.dmg
```

## Windows

Build:

```text
LocalConvert-Windows-x64.exe
```

Bundle required runtime/dependencies as appropriate.

User should not need Python installed.

Test on clean machines.

---

# PHASE 24 — EXPAND BEYOND PDF

Only after PDF → DOCX is reliable should the project expand.

Next:

### PDF

- merge
- split
- rotate
- compress
- OCR
- images
- metadata

### Office

- DOCX → PDF
- PPTX → PDF
- XLSX → PDF

### Images

- PNG
- JPG
- WEBP
- TIFF

### Data

- JSON
- YAML
- CSV
- XML

### Media

- FFmpeg-based conversions

Each category gets its own specialized engine.

Do not introduce all of these simultaneously.

---

# PHASE 25 — QUALITY DASHBOARD

Create a developer-facing benchmark command:

```bash
localconvert benchmark
```

Output:

```text
LocalConvert Conversion Benchmark

Test corpus: 42 files

PDF → DOCX

Success rate:          90.5%
Pagination failures:   2
Blank-page failures:   1
Text fidelity:         98.1%
Visual fidelity:       95.7%
Average conversion:    3.8s
Average memory:        420 MB

Worst cases:
1. complex_two_column.pdf
2. scanned_invoice.pdf
3. academic_tables.pdf
```

Do not fabricate or hand-tune metrics.

Every value must come from the actual test run.

---

# PHASE 26 — PACKAGING + DEPENDENCY AUDIT

Before release:

Check every dependency for:

- license
- redistribution rights
- version
- security
- platform availability

Create:

```text
THIRD_PARTY_LICENSES.md
```

and package required license notices.

---

# PHASE 27 — FINAL PRODUCT HARDENING

Before calling the application production-ready:

Test:

- huge files
- malformed PDFs
- corrupted DOCX
- missing native dependencies
- permission errors
- Unicode filenames
- long paths
- cancelled conversions
- disk-full conditions
- concurrent conversions
- offline operation
- repeated conversions
- application restart during conversion

Check that temporary files are cleaned up.

Check that the original file is never modified unintentionally.

---

# DEVELOPMENT RULES

Follow these rules throughout the project.

### Rule 1

**Do not add more formats when existing formats are unreliable.**

### Rule 2

**Do not hide failures.**

### Rule 3

**Do not judge conversion quality only by whether the output opens.**

### Rule 4

**Do not make rasterization the default solution.**

### Rule 5

**Do not tie the GUI directly to conversion libraries.**

### Rule 6

**Do not rely on a single library for every format.**

### Rule 7

**Do not use cloud APIs for the core conversion path.**

### Rule 8

**Every important conversion gets an automated regression test.**

### Rule 9

**A conversion can fail honestly. A corrupted document must never be reported as successful.**

### Rule 10

**Quality and fidelity take priority over the number of supported formats.**

---

# IMMEDIATE EXECUTION ORDER

Do not jump ahead.

Implement in exactly this order:

```text
1. Environment audit
        ↓
2. Project foundation
        ↓
3. Conversion core
        ↓
4. File detection
        ↓
5. PDF analyzer
        ↓
6. Baseline PDF → DOCX
        ↓
7. Diagnose/fix pagination
        ↓
8. Layout-aware PDF → DOCX
        ↓
9. Reading-order reconstruction
        ↓
10. Figures/images
        ↓
11. Tables
        ↓
12. OCR path
        ↓
13. Fidelity validator
        ↓
14. Blank-page detector
        ↓
15. Regression corpus
        ↓
16. Multi-engine router
        ↓
17. Fallback system
        ↓
18. User conversion modes
        ↓
19. CLI
        ↓
20. PySide6 GUI
        ↓
21. Job system
        ↓
22. Privacy verification
        ↓
23. macOS/Windows packaging
        ↓
24. Expand supported formats
```

## FIRST MILESTONE

Do NOT attempt to build the entire application immediately.

The first milestone is:

> **Take the provided 17-page academic PDF, convert it to DOCX, render that DOCX back to PDF, and produce an automated fidelity report showing pagination, blank pages, text preservation, and visual differences.**
