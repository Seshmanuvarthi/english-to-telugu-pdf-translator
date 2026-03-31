# English to Telugu PDF Translator 

A privacy-preserving, fully offline web-based tool that translates **English PDFs into Telugu** while preserving the original layout, images, background colors, and document formatting.

## Features

- **100% Offline AI Translation:** Uses Meta's **NLLB-200** (No Language Left Behind) sequence-to-sequence NLP model for highly accurate, offline text translation. No data is sent to external APIs (e.g., Google Translate).
- **Layout & Structure Preservation:** Uses intelligent bounding box and background color sampling to perfectly redact original English text without creating ugly black boxes, retaining all images and document flow.
- **Flawless Telugu Rendering:** Utilizes PyMuPDF's HarfBuzz complex script shaping to correctly render Telugu conjunct consonants (Vottulu) and vowel modifiers.
- **Hardware Accelerated:** Automatically batches NLP input tensors and offloads inference to Apple Silicon GPUs (Metal Performance Shaders - `mps`) for rapid generation.
- **Real-Time Streaming Interface:** An intuitive browser interface featuring Server-Sent Events (SSE) to track translation progress line-by-line without freezing the browser.

## Tech Stack

- **Backend:** Python + Flask
- **PDF Manipulation:** PyMuPDF (`fitz`)
- **NLP Engine:** Hugging Face `transformers`, PyTorch (Meta NLLB-200 Distilled 600M)
- **Typography:** `NotoSansTelugu-Regular.ttf`

## Getting Started

### Prerequisites
- Python 3.8+
- Mac with Apple Silicon (M1/M2/M3) recommended for optimal translation speed.

```bash
git clone https://github.com/Seshmanuvarthi/english-to-telugu-pdf-translator.git
cd english-to-telugu-pdf-translator
pip install -r requirements.txt
```

### Running the App

```bash
python3 app.py
```

1. The first time you run this, it will download the ~2.4GB Meta NLLB NLP model automatically to your local machine.
2. Open `http://127.0.0.1:5001` in your web browser.
3. Upload an English PDF and click translate.
4. Watch the real-time progress bar process your document.
5. Download your perfectly translated Telugu PDF!
