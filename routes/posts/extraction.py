"""
GTU-ITR R&D & IIC Portal - Post Extraction & OCR Routes
"""
import os
from flask import request, current_app, jsonify
from flask_login import login_required
from werkzeug.utils import secure_filename

from utils.decorators import principal_required
from services.ai_post_extractor import PostExtractor
from . import posts_bp, _allowed_file

_rapid_ocr_instance = None


def _get_rapid_ocr_engine():
    """Lazily initialize and cache the RapidOCR engine."""
    global _rapid_ocr_instance
    if _rapid_ocr_instance is None:
        try:
            os.environ.setdefault('ORT_LOG_LEVEL', '3')
            from rapidocr_onnxruntime import RapidOCR
            with _suppress_c_stderr():
                _rapid_ocr_instance = RapidOCR()
        except Exception as e:
            import logging
            logging.getLogger(__name__).warning("Could not initialize RapidOCR: %s", e)
            _rapid_ocr_instance = False
    return _rapid_ocr_instance if _rapid_ocr_instance is not False else None


def _suppress_c_stderr():
    """Context manager to silence low-level C/C++ runtime stderr (e.g. ONNX thread warnings)."""
    import contextlib
    @contextlib.contextmanager
    def _suppressor():
        import os, sys
        try:
            stderr_fd = sys.stderr.fileno()
            saved_stderr = os.dup(stderr_fd)
            devnull = os.open(os.devnull, os.O_WRONLY)
            os.dup2(devnull, stderr_fd)
            os.close(devnull)
            try:
                yield
            finally:
                os.dup2(saved_stderr, stderr_fd)
                os.close(saved_stderr)
        except Exception:
            yield
    return _suppressor()


def _ocr_image(image):
    """Run OCR on a PIL Image and return extracted text.
    Uses RapidOCR (pure ONNX engine, high accuracy) as primary,
    with fallback to pytesseract if installed.
    """
    import logging
    logger = logging.getLogger(__name__)

    # 1. Primary: RapidOCR
    try:
        engine = _get_rapid_ocr_engine()
        if engine is not None:
            import numpy as np
            rgb_image = image.convert('RGB')
            img_np = np.array(rgb_image)
            with _suppress_c_stderr():
                result, _ = engine(img_np)
            if result:
                lines = [line[1] for line in result if line and len(line) > 1 and line[1]]
                extracted = '\n'.join(lines).strip()
                if extracted:
                    return extracted
    except Exception as e:
        logger.warning("RapidOCR extraction failed: %s", e)

    # 2. Fallback: pytesseract
    try:
        import pytesseract
        text = pytesseract.image_to_string(image, lang='eng').strip()
        if text:
            return text
    except Exception as e:
        logger.debug("pytesseract unavailable or failed: %s", e)

    return ''


def _extract_text_from_file(filepath):
    """Extract text from uploaded file.

    Supports:
    - **Images** (JPG/PNG/BMP/TIFF/WEBP): RapidOCR & Tesseract fallback
    - **PDF**: Text extraction with pdfplumber; if scanned or minimal text,
      falls back to OCR on rendered pages via pypdfium2
    - **DOCX/DOC**: Extracts paragraphs + table cells + headers/footers
    - **TXT**: Plain read
    """
    import logging
    logger = logging.getLogger(__name__)

    ext = filepath.rsplit('.', 1)[1].lower()
    text = ''

    # ── Images: OCR ─────────────────────────────────────────────────
    if ext in ('png', 'jpg', 'jpeg', 'bmp', 'tiff', 'webp'):
        try:
            from PIL import Image
            img = Image.open(filepath)
            text = _ocr_image(img)
            logger.info("OCR extracted %d chars from image.", len(text))
        except Exception as e:
            logger.warning("OCR failed for image: %s", e)
            text = ''

    # ── PDF: text first, OCR fallback for scanned pages ─────────────
    elif ext == 'pdf':
        try:
            import pdfplumber
            page_count = 0
            with pdfplumber.open(filepath) as pdf:
                page_count = len(pdf.pages)
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + '\n'
                    # Also extract text from tables
                    for table in (page.extract_tables() or []):
                        for row in table:
                            cells = [c.strip() for c in row if c and c.strip()]
                            if cells:
                                text += ' | '.join(cells) + '\n'

            logger.info("pdfplumber extracted %d chars from %d pages.", len(text.strip()), page_count)
        except Exception as e:
            logger.warning("pdfplumber extraction failed: %s", e)
            page_count = 0

        # If text extraction got very little content (or was scanned PDF),
        # fall back to OCR on rendered page images
        if len(text.strip()) < 50:
            logger.info("PDF text too short (%d chars), trying OCR fallback on rendered pages...", len(text.strip()))
            try:
                import pypdfium2 as pdfium

                ocr_text = ''
                pdf_doc = pdfium.PdfDocument(filepath)
                num_pages = len(pdf_doc)
                for i in range(min(num_pages, 10)):  # OCR up to 10 pages
                    page = pdf_doc[i]
                    bitmap = page.render(scale=300 / 72)
                    pil_image = bitmap.to_pil()
                    page_ocr = _ocr_image(pil_image)
                    if page_ocr:
                        ocr_text += page_ocr + '\n'
                    bitmap.close()
                pdf_doc.close()

                if len(ocr_text.strip()) > len(text.strip()):
                    text = ocr_text
                    logger.info("PDF OCR fallback extracted %d chars.", len(text.strip()))
            except Exception as ocr_e:
                logger.warning("PDF OCR fallback failed: %s", ocr_e)

    # ── Word documents: paragraphs + tables + headers ────────────────
    elif ext in ('docx', 'doc'):
        try:
            import docx
            doc = docx.Document(filepath)
            parts = []

            # 1. Headers (often contain title / letterhead info)
            for section in doc.sections:
                header = section.header
                if header and not header.is_linked_to_previous:
                    for p in header.paragraphs:
                        if p.text.strip():
                            parts.append(p.text.strip())

            # 2. All paragraphs (main body)
            for p in doc.paragraphs:
                if p.text.strip():
                    parts.append(p.text.strip())

            # 3. All tables (dates, venues, details often live here)
            for table in doc.tables:
                for row in table.rows:
                    cells = [cell.text.strip() for cell in row.cells if cell.text.strip()]
                    if cells:
                        parts.append(' | '.join(cells))

            # 4. Footers (contact info, registration links)
            for section in doc.sections:
                footer = section.footer
                if footer and not footer.is_linked_to_previous:
                    for p in footer.paragraphs:
                        if p.text.strip():
                            parts.append(p.text.strip())

            text = '\n'.join(parts)
            logger.info("DOCX extracted %d chars from %d parts.", len(text), len(parts))
        except Exception as e:
            logger.warning("DOCX extraction failed: %s", e)
            text = '[DOCX text extraction failed]'

    # ── Plain text ───────────────────────────────────────────────────
    elif ext == 'txt':
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                text = f.read()
        except Exception:
            text = '[TXT read failed]'

    return _clean_extracted_text(text)


def _clean_extracted_text(raw_text):
    """Clean up extracted text from PDF/OCR to fix common artifacts.

    Fixes:
    1. Triple-letter OCR artifacts from bold/decorative fonts
       (e.g. BBBhhhaaarrraaatttiiiyyyaaa → Bharatiya)
    2. Duplicate paragraphs / content blocks from multi-page extraction
    3. Excessive whitespace and empty lines
    """
    import re

    if not raw_text or raw_text.startswith('['):
        return raw_text.strip()

    lines = raw_text.split('\n')
    cleaned_lines = []

    for line in lines:
        stripped = line.strip()
        if not stripped:
            cleaned_lines.append('')
            continue

        # ── Fix 1: Triple-letter OCR artifact ──────────────────────
        # Detect lines like "BBBhhhaaarrraaatttiiiyyyaaa GGGyyyaaannn"
        triple_groups = re.findall(r'(.)\1{2}', stripped)

        if triple_groups:
            # Calculate what % of non-space chars are triple-repeated
            non_space = stripped.replace(' ', '')
            triple_char_count = sum(
                len(m.group(0)) for m in re.finditer(r'(.)\1{2,}', stripped)
            )
            ratio = triple_char_count / max(len(non_space), 1)

            # If more than 30% of non-space chars are in triple groups
            # AND there are at least 2 triple groups, it's an artifact
            if ratio > 0.3 and len(triple_groups) >= 2:
                fixed = re.sub(r'(.)\1{2}', r'\1', stripped)
                cleaned_lines.append(fixed)
                continue
            # Short lines that are entirely triple chars (e.g. "sssttt")
            elif ratio > 0.8 and len(stripped) <= 10:
                fixed = re.sub(r'(.)\1{2}', r'\1', stripped)
                cleaned_lines.append(fixed)
                continue

        cleaned_lines.append(stripped)

    # ── Fix 1b: Re-join broken title lines ─────────────────────────
    # Merge consecutive short lines that form a title
    # e.g. "Bharatiya Gyan Parampara: Scientific" + "Technical Development in"
    # → "Bharatiya Gyan Parampara: Scientific Technical Development in"
    merged_lines = []
    i = 0
    while i < len(cleaned_lines):
        current = cleaned_lines[i]
        # If this line ends without punctuation and next line looks like continuation
        if (current and not current.endswith(('.', ',', ':', ';', '!', '?', '—', '-'))
            and i + 1 < len(cleaned_lines)
            and cleaned_lines[i + 1]
            and not cleaned_lines[i + 1][0].isupper()
            and len(current) < 60):
            # Merge with next line
            merged_lines.append(current + ' ' + cleaned_lines[i + 1])
            i += 2
        else:
            merged_lines.append(current)
            i += 1

    # ── Fix 2: Remove duplicate lines/blocks ───────────────────────
    # Use a sliding window approach: track seen lines, skip exact repeats
    text = '\n'.join(merged_lines)

    # Split into logical blocks (separated by blank lines)
    blocks = re.split(r'\n\s*\n', text)

    seen_blocks = set()
    unique_blocks = []

    for block in blocks:
        block = block.strip()
        if not block:
            continue

        # Normalize for comparison
        key = re.sub(r'\s+', ' ', block.lower()).strip()

        # Skip if too similar to something we've seen
        if key in seen_blocks:
            continue

        # Skip if this block's content is substantially contained in an earlier block
        is_dup = False
        for seen_key in seen_blocks:
            # Check if >80% of this block's words appear in an existing block
            if len(key) > 40 and len(seen_key) > 40:
                if key in seen_key or seen_key in key:
                    is_dup = True
                    break
                # Check overlap of words
                key_words = set(key.split())
                seen_words = set(seen_key.split())
                if len(key_words) > 5:
                    overlap = len(key_words & seen_words) / len(key_words)
                    if overlap > 0.8:
                        is_dup = True
                        break
        if is_dup:
            continue

        seen_blocks.add(key)
        unique_blocks.append(block)

    # ── Fix 3: Final cleanup ───────────────────────────────────────
    result = '\n\n'.join(unique_blocks)
    result = re.sub(r'\n{3,}', '\n\n', result)

    return result.strip()


@posts_bp.route('/extract', methods=['POST'])
@login_required
@principal_required
def extract():
    """AJAX endpoint to auto-extract post details from pasted text or uploaded file.
    Supports OCR for flier images (JPG/PNG), text extraction from PDFs/DOCX,
    and saves the uploaded file as a post attachment."""
    raw_text = request.form.get('pasted_text', '').strip()
    use_ai = request.form.get('use_ai') == 'true'
    saved_attachment = None
    file_text = ''
    
    # If a file was uploaded: save as attachment + extract text from it
    if 'post_file' in request.files and request.files['post_file'].filename:
        file = request.files['post_file']
        if _allowed_file(file.filename):
            import uuid
            clean_name = secure_filename(file.filename)
            filename = f"{uuid.uuid4().hex[:8]}_{clean_name}"
            upload_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'posts')
            os.makedirs(upload_dir, exist_ok=True)
            filepath = os.path.join(upload_dir, filename)
            file.save(filepath)
            saved_attachment = f'posts/{filename}'
            
            # Extract text from the uploaded file (OCR for images, text for PDFs)
            file_text = _extract_text_from_file(filepath)

    # Combine: pasted text takes priority, file text is fallback
    combined_text = raw_text or file_text
            
    if not combined_text:
        if saved_attachment:
            return jsonify({
                'success': True,
                'extracted': {
                    'activity_heading': '',
                    'source': 'COMPANY',
                    'summary': '',
                    'start_date': None,
                    'end_date': None,
                    'department': None,
                    'full_content': ''
                },
                'saved_attachment': saved_attachment,
                'message': 'File attached but no text could be extracted from it.'
            })
        return jsonify({'error': 'No text or file was provided.'}), 400
        
    # Extract structured details using heuristic service
    extracted = PostExtractor.extract(combined_text, use_ai=use_ai)
    
    result = {
        'success': True,
        'extracted': extracted
    }
    if saved_attachment:
        result['saved_attachment'] = saved_attachment
    if file_text and not raw_text:
        result['ocr_used'] = True
    
    return jsonify(result)
