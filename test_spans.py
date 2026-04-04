import fitz
import sys

def test(pdf_path):
    doc = fitz.open(pdf_path)
    page = doc[0]
    text_dict = page.get_text("dict")
    
    for block in text_dict["blocks"]:
        if block["type"] != 0: continue
        for line in block["lines"]:
            spans = line["spans"]
            print("Spans:", [s["text"] for s in spans])

if len(sys.argv) > 1:
    test(sys.argv[1])
else:
    print("No PDF provided")
