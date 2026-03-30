import fitz  # PyMuPDF
import os
import html as html_lib


def _int_color_to_rgb(color_int):
    """Convert an integer color value to an (r, g, b) tuple with values 0.0-1.0."""
    r = ((color_int >> 16) & 0xFF) / 255.0
    g = ((color_int >> 8) & 0xFF) / 255.0
    b = (color_int & 0xFF) / 255.0
    return (r, g, b)


def _is_light_color(color_int):
    """Check if a color is light/white (white text on dark header)."""
    r, g, b = _int_color_to_rgb(color_int)
    brightness = 0.299 * r + 0.587 * g + 0.114 * b
    return brightness > 0.7


def _get_bg_color_for_span(page, span_info):
    """
    Determine the fill color for redacting a span.
    - Dark text on white bg → fill white
    - Light/white text on colored header → sample corner pixels
    """
    text_color = span_info["color"]

    if not _is_light_color(text_color):
        return (1.0, 1.0, 1.0)

    try:
        rect = fitz.Rect(span_info["bbox"])
        pix = page.get_pixmap(clip=rect, dpi=72)
        w, h = pix.width, pix.height
        if w > 0 and h > 0:
            pixel = pix.pixel(0, 0)
            return (pixel[0] / 255.0, pixel[1] / 255.0, pixel[2] / 255.0)
    except Exception:
        pass

    return (0.2, 0.2, 0.2)


def process_pdf(input_path, output_path, translate_function, progress_callback=None):
    """
    Process a PDF: replace English text with Telugu while preserving layout and images.
    Uses insert_htmlbox() for proper Telugu complex script shaping (HarfBuzz).
    Groups text by lines for better translation quality.
    """
    font_path = os.path.join(os.path.dirname(os.path.dirname(__file__)),
                              "fonts", "NotoSansTelugu-Regular.ttf")

    if not os.path.exists(font_path):
        raise FileNotFoundError(f"Telugu font not found at: {font_path}")

    doc = fitz.open(input_path)
    total_pages = len(doc)

    # Prepare font archive and CSS for insert_htmlbox (proper Telugu shaping)
    font_dir = os.path.dirname(font_path)
    font_filename = os.path.basename(font_path)
    archive = fitz.Archive(font_dir)

    base_css = f"""
    @font-face {{
        font-family: "NotoTelugu";
        src: url("{font_filename}");
    }}
    * {{
        font-family: NotoTelugu, sans-serif;
        margin: 0;
        padding: 0;
        line-height: 1.1;
    }}
    """

    def report(page_num, message):
        percent = int((page_num / total_pages) * 100) if total_pages > 0 else 0
        print(f"  [{percent}%] {message}")
        if progress_callback:
            progress_callback({
                'current_page': page_num,
                'total_pages': total_pages,
                'percent': percent,
                'message': message,
            })

    report(0, f'Starting translation of {total_pages} pages...')

    for page_num in range(total_pages):
        page = doc[page_num]
        report(page_num, f'Processing page {page_num + 1} of {total_pages}...')

        # Step 1: Extract text and GROUP BY LINES
        text_dict = page.get_text("dict")
        lines_data = []

        for block in text_dict["blocks"]:
            if block["type"] != 0:
                continue

            for line in block["lines"]:
                line_spans = []
                for span in line["spans"]:
                    text = span["text"]
                    if not text.strip():
                        continue
                    line_spans.append({
                        "text": text,
                        "bbox": span["bbox"],
                        "origin": span["origin"],
                        "size": span["size"],
                        "color": span["color"],
                        "flags": span["flags"],
                    })

                if line_spans:
                    full_text = "".join(s["text"] for s in line_spans)
                    lines_data.append({
                        "full_text": full_text,
                        "spans": line_spans,
                    })

        if not lines_data:
            report(page_num + 1, f'Page {page_num + 1}: no text, skipping...')
            continue

        # Step 2: Translate all lines
        line_texts = [ld["full_text"] for ld in lines_data]
        report(page_num, f'Translating {len(line_texts)} lines on page {page_num + 1}...')
        translated_lines = translate_function(line_texts)

        # Step 3: Redact original text
        report(page_num, f'Replacing text on page {page_num + 1}...')

        for line_data in lines_data:
            for span_info in line_data["spans"]:
                rect = fitz.Rect(span_info["bbox"])
                fill = _get_bg_color_for_span(page, span_info)
                page.add_redact_annot(rect, fill=fill)

        page.apply_redactions(images=fitz.PDF_REDACT_IMAGE_NONE)

        # Step 4: Insert Telugu text using insert_htmlbox (proper shaping)
        for i, line_data in enumerate(lines_data):
            telugu_text = translated_lines[i]
            first_span = line_data["spans"][0]
            last_span = line_data["spans"][-1]
            font_size = first_span["size"] * 0.85
            text_color = _int_color_to_rgb(first_span["color"])
            r, g, b = text_color

            # Build the rect for the text box
            # Origin is baseline position; rect top = baseline - ascent
            origin_x = first_span["origin"][0]
            origin_y = first_span["origin"][1]
            ascent = font_size * 0.9
            descent = font_size * 0.35

            # Width: extend to right edge of page (with small margin)
            rect = fitz.Rect(
                origin_x,
                origin_y - ascent,
                page.rect.width - 15,
                origin_y + descent,
            )

            # CSS color
            css_r, css_g, css_b = int(r * 255), int(g * 255), int(b * 255)

            # HTML with escaped text
            safe_text = html_lib.escape(telugu_text)
            text_html = (
                f'<p style="font-size:{font_size:.1f}pt; '
                f'color:rgb({css_r},{css_g},{css_b}); '
                f'margin:0; padding:0; white-space:nowrap;">'
                f'{safe_text}</p>'
            )

            try:
                page.insert_htmlbox(rect, text_html, css=base_css, archive=archive)
            except Exception as e:
                print(f"    Error with htmlbox at {origin_x:.0f},{origin_y:.0f}: {e}")
                # Fallback to insert_text
                try:
                    page.insert_text(
                        point=(origin_x, origin_y),
                        text=telugu_text,
                        fontfile=font_path,
                        fontname="NotoTelugu",
                        fontsize=font_size,
                        color=text_color,
                    )
                except Exception:
                    pass

        report(page_num + 1, f'Page {page_num + 1} of {total_pages} complete!')

    # Save
    report(total_pages, 'Saving translated PDF...')
    doc.save(output_path, garbage=4, deflate=True)
    doc.close()
    report(total_pages, 'Translation complete!')
    print(f"  Saved translated PDF to: {output_path}")
