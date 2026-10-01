"""Debug script: Extract raw PyMuPDF data from the resume to understand fragmentation."""
import fitz
import json
from pathlib import Path

pdf_path = Path("/tmp/Pragyan_Sharma_Resume .pdf")
doc = fitz.open(pdf_path)

print(f"Pages: {len(doc)}")
print(f"Page 0 size: {doc[0].rect.width} x {doc[0].rect.height}")
print()

page = doc[0]

# Method 1: get_text("dict") gives us spans with exact positions
data = page.get_text("dict")

print("=" * 60)
print("RAW SPANS (first 40)")
print("=" * 60)

span_count = 0
for block in data["blocks"]:
    if block["type"] != 0:  # text blocks only
        continue
    for line in block["lines"]:
        for span in line["spans"]:
            if span_count < 40:
                print(f"  x0={span['bbox'][0]:.1f} y0={span['bbox'][1]:.1f} "
                      f"x1={span['bbox'][2]:.1f} y1={span['bbox'][3]:.1f} "
                      f"size={span['size']:.1f} "
                      f"font={span['font']} "
                      f"flags={span['flags']} "
                      f"text='{span['text']}'")
            span_count += 1

print(f"\nTotal spans: {span_count}")

# Method 2: get_text("words") gives word-level boxes
words = page.get_text("words")
print()
print("=" * 60)
print(f"WORD OBJECTS (first 40 of {len(words)})")
print("=" * 60)
for i, w in enumerate(words[:40]):
    # w = (x0, y0, x1, y1, "word", block_no, line_no, word_no)
    print(f"  x0={w[0]:.1f} y0={w[1]:.1f} x1={w[2]:.1f} y1={w[3]:.1f} "
          f"blk={w[5]} ln={w[6]} wn={w[7]} "
          f"text='{w[4]}'")

# Method 3: get_text("rawdict") for character-level
rawdata = page.get_text("rawdict")
print()
print("=" * 60)
print("FIRST 5 LINES WITH CHARACTER DETAIL")
print("=" * 60)
line_count = 0
for block in rawdata["blocks"]:
    if block["type"] != 0:
        continue
    for line in block["lines"]:
        if line_count >= 5:
            break
        print(f"\n  LINE dir={line['dir']} bbox={[round(b,1) for b in line['bbox']]}")
        for span in line["spans"]:
            print(f"    SPAN font={span['font']} size={span['size']:.1f} "
                  f"bbox={[round(b,1) for b in span['bbox']]}")
            chars = span.get("chars", [])
            char_text = "".join(c["c"] for c in chars)
            if chars:
                print(f"      chars: '{char_text}'")
                # Show gaps between characters
                for j in range(1, min(len(chars), 20)):
                    gap = chars[j]["bbox"][0] - chars[j-1]["bbox"][2]
                    if abs(gap) > 1:
                        print(f"      GAP after '{chars[j-1]['c']}' before '{chars[j]['c']}': {gap:.1f}px")
        line_count += 1

doc.close()
