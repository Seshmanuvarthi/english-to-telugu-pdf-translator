# English to Telugu PDF Translator 

This is a web-based tool that translates **English PDFs into Telugu**, while preserving the layout, images, and formatting.

##  Features

-  English to Telugu translation using `googletrans`
-  Retains PDF structure and design
-  Simple browser interface (upload + download)
-  100% free — no API keys required
-  Client-ready & reusable

##  Tech Stack

- Python + Flask
- PyMuPDF (`fitz`)
- `googletrans`
- `reportlab` or `weasyprint`
- `NotoSansTelugu.ttf` for accurate Telugu font rendering

##  Getting Started

```bash
git clone https://github.com/Seshmanuvarthi/english-to-telugu-pdf-translator.git
cd english-to-telugu-pdf-translator
pip install -r requirements.txt
python app.py
