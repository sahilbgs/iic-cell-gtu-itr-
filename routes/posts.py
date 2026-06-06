"""
GTU-ITR R&D & IIC Portal - Principal Post Routes
Blueprint: posts  |  Prefix: /posts
"""
import os
from datetime import datetime
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, jsonify, abort
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename

from extensions import db
from models.principal_post import PrincipalPost, POST_SOURCES, POST_STATUSES
from models.department import Department
from models.activity_report import ActivityReport
from services.report_generator import ReportGenerator
from utils.decorators import principal_required, role_required
from services.ai_post_extractor import PostExtractor


posts_bp = Blueprint('posts', __name__, url_prefix='/posts')

ALLOWED_UPLOAD_EXT = {'pdf', 'docx', 'doc', 'txt', 'png', 'jpg', 'jpeg'}


def _allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_UPLOAD_EXT


@posts_bp.route('/')
@login_required
def index():
    """List all shared principal posts for general view (excluding completed ones with reports)."""
    PrincipalPost.check_and_update_expired()
    # Filter out completed and expired posts
    posts = PrincipalPost.query.join(
        ActivityReport, PrincipalPost.id == ActivityReport.post_id, isouter=True
    ).filter(
        PrincipalPost.progress_status != 'EXPIRED',
        db.or_(
            PrincipalPost.progress_status != 'COMPLETED',
            ActivityReport.id == None,
            ActivityReport.status != 'SUBMITTED'
        )
    ).order_by(PrincipalPost.created_at.desc()).all()
    return render_template('posts/index.html', posts=posts)



@posts_bp.route('/<int:post_id>/view')
@login_required
def view_post(post_id):
    """View full details and attachment of a post on a dedicated page."""
    post = PrincipalPost.query.get_or_404(post_id)
    return render_template('posts/view.html', post=post)


@posts_bp.route('/manage')
@login_required
@principal_required
def manage():
    """Management dashboard for the Principal to CRUD posts."""
    PrincipalPost.check_and_update_expired()
    posts = PrincipalPost.query.order_by(PrincipalPost.created_at.desc()).all()
    return render_template('posts/manage.html', posts=posts)


@posts_bp.route('/approved-activities')
@login_required
@principal_required
def approved_activities():
    """Principal's view of all approved activities with progress reports."""
    PrincipalPost.check_and_update_expired()
    approved_posts = PrincipalPost.query.join(
        ActivityReport, PrincipalPost.id == ActivityReport.post_id, isouter=True
    ).filter(
        PrincipalPost.approval_status == 'APPROVED',
        PrincipalPost.progress_status != 'EXPIRED',
        db.or_(
            PrincipalPost.progress_status != 'COMPLETED',
            ActivityReport.id == None,
            ActivityReport.status != 'SUBMITTED'
        )
    ).order_by(PrincipalPost.created_at.desc()).all()

    # Group by department (a post can appear in multiple departments)
    dept_groups = {}
    for post in approved_posts:
        if post.departments:
            for dept in post.departments:
                if dept.name not in dept_groups:
                    dept_groups[dept.name] = []
                dept_groups[dept.name].append(post)
        else:
            dept_name = 'Unassigned'
            if dept_name not in dept_groups:
                dept_groups[dept_name] = []
            dept_groups[dept_name].append(post)

    # Stats
    total_approved = len(approved_posts)
    completed_count = sum(1 for p in approved_posts if p.progress_status == 'COMPLETED')
    in_progress_count = sum(1 for p in approved_posts if p.progress_status == 'IN_PROGRESS')
    not_started_count = sum(1 for p in approved_posts if p.progress_status == 'NOT_STARTED')

    return render_template('posts/approved_activities.html',
                           approved_posts=approved_posts,
                           dept_groups=dept_groups,
                           total_approved=total_approved,
                           completed_count=completed_count,
                           in_progress_count=in_progress_count,
                           not_started_count=not_started_count)


def _ocr_image(image):
    """Run Tesseract OCR on a PIL Image and return extracted text."""
    import pytesseract
    return pytesseract.image_to_string(image, lang='eng')


def _extract_text_from_file(filepath):
    """Extract text from uploaded file.

    Supports:
    - **Images** (JPG/PNG/BMP/TIFF): OCR with Tesseract
    - **PDF**: Text extraction with pdfplumber; if the result is too
      short (scanned/image PDF), falls back to OCR via pypdfium2
    - **DOCX/DOC**: Extracts paragraphs + table cells + headers/footers
    - **TXT**: Plain read
    """
    import logging
    logger = logging.getLogger(__name__)

    ext = filepath.rsplit('.', 1)[1].lower()
    text = ''

    # ── Images: OCR with Tesseract ──────────────────────────────────
    if ext in ('png', 'jpg', 'jpeg', 'bmp', 'tiff', 'webp'):
        try:
            from PIL import Image
            img = Image.open(filepath)
            text = _ocr_image(img)
            logger.info("OCR extracted %d chars from image.", len(text))
        except ImportError:
            text = '[OCR unavailable – install pytesseract and Pillow]'
        except Exception as e:
            logger.warning("OCR failed for image: %s", e)
            text = f'[OCR failed: {e}]'

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

            # If text extraction got very little content, the PDF is likely
            # scanned/image-based — fall back to OCR on each page
            if len(text.strip()) < 50 and page_count > 0:
                logger.info("PDF text too short (%d chars), trying OCR fallback...", len(text.strip()))
                try:
                    import pypdfium2 as pdfium
                    from PIL import Image as PILImage

                    ocr_text = ''
                    pdf_doc = pdfium.PdfDocument(filepath)
                    for i in range(min(len(pdf_doc), 5)):  # OCR max 5 pages
                        page = pdf_doc[i]
                        # Render page as image at 300 DPI for good OCR quality
                        bitmap = page.render(scale=300/72)
                        pil_image = bitmap.to_pil()
                        page_ocr = _ocr_image(pil_image)
                        if page_ocr:
                            ocr_text += page_ocr + '\n'
                    pdf_doc.close()

                    if len(ocr_text.strip()) > len(text.strip()):
                        text = ocr_text
                        logger.info("PDF OCR fallback extracted %d chars.", len(text.strip()))
                except ImportError:
                    logger.warning("pypdfium2 not available for PDF OCR fallback.")
                except Exception as ocr_e:
                    logger.warning("PDF OCR fallback failed: %s", ocr_e)

        except Exception as e:
            logger.warning("PDF extraction failed: %s", e)
            text = '[PDF text extraction failed]'

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
        if (current and not current.endswith(('.', ',', ':', ';', '!', '?', ''))
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
            filename = secure_filename(file.filename)
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


@posts_bp.route('/create', methods=['GET', 'POST'])
@login_required
@principal_required
def create():
    """Create a new shared principal post."""
    departments = Department.query.order_by(Department.name).all()
    
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        source = request.form.get('source', 'COMPANY')
        summary = request.form.get('summary', '').strip()
        full_content = request.form.get('full_content', '').strip()
        progress_status = request.form.get('progress_status', 'NOT_STARTED')
        department_id = request.form.get('department_id', type=int)
        
        # Validation
        if not title or not summary or not full_content:
            flash('Activity heading, summary, and full content are required.', 'danger')
            return render_template('posts/form.html', post=None, departments=departments,
                                   sources=POST_SOURCES, statuses=POST_STATUSES)
            
        # Parse Dates
        start_date = None
        start_date_str = request.form.get('start_date', '').strip()
        if start_date_str:
            try:
                start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            except ValueError:
                pass
                
        end_date = None
        end_date_str = request.form.get('end_date', '').strip()
        if end_date_str:
            try:
                end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
            except ValueError:
                pass

        if start_date and end_date and end_date < start_date:
            flash('End Date / Deadline cannot be earlier than Start Date.', 'danger')
            return render_template('posts/form.html', post=None, departments=departments,
                                   sources=POST_SOURCES, statuses=POST_STATUSES)

        post = PrincipalPost(
            title=title,
            source=source,
            summary=summary,
            full_content=full_content,
            progress_status=progress_status,
            department_id=department_id or None,
            created_by=current_user.id,
            start_date=start_date,
            end_date=end_date
        )

        # Handle file attachment
        if 'attachment' in request.files and request.files['attachment'].filename:
            file = request.files['attachment']
            if _allowed_file(file.filename):
                filename = secure_filename(file.filename)
                upload_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'posts')
                os.makedirs(upload_dir, exist_ok=True)
                filepath = os.path.join(upload_dir, filename)
                file.save(filepath)
                post.attachment_path = f'posts/{filename}'
            else:
                flash('Unsupported attachment file format.', 'warning')
        elif request.form.get('pre_attachment_path', '').strip():
            # Use the file that was pre-saved during AI extraction
            post.attachment_path = request.form.get('pre_attachment_path').strip()

        db.session.add(post)
        db.session.commit()
        flash('Shared Activity Post created successfully!', 'success')
        return redirect(url_for('posts.manage'))

    return render_template('posts/form.html', post=None, departments=departments,
                           sources=POST_SOURCES, statuses=POST_STATUSES)


@posts_bp.route('/<int:post_id>/edit', methods=['GET', 'POST'])
@login_required
@principal_required
def edit(post_id):
    """Edit an existing shared principal post."""
    post = PrincipalPost.query.get_or_404(post_id)
    if post.progress_status == 'COMPLETED':
        flash('Completed activities cannot be edited.', 'danger')
        return redirect(url_for('posts.manage'))
        
    departments = Department.query.order_by(Department.name).all()
    
    if request.method == 'POST':
        post.title = request.form.get('title', '').strip()
        post.source = request.form.get('source', 'COMPANY')
        post.summary = request.form.get('summary', '').strip()
        post.full_content = request.form.get('full_content', '').strip()
        post.progress_status = request.form.get('progress_status', 'NOT_STARTED')
        post.department_id = request.form.get('department_id', type=int) or None
        
        # Validation
        if not post.title or not post.summary or not post.full_content:
            flash('Activity heading, summary, and full content are required.', 'danger')
            return render_template('posts/form.html', post=post, departments=departments,
                                   sources=POST_SOURCES, statuses=POST_STATUSES)
        
        # Parse Dates
        start_date = None
        start_date_str = request.form.get('start_date', '').strip()
        if start_date_str:
            try:
                start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            except ValueError:
                pass
                
        end_date = None
        end_date_str = request.form.get('end_date', '').strip()
        if end_date_str:
            try:
                end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
            except ValueError:
                pass

        if start_date and end_date and end_date < start_date:
            flash('End Date / Deadline cannot be earlier than Start Date.', 'danger')
            return render_template('posts/form.html', post=post, departments=departments,
                                   sources=POST_SOURCES, statuses=POST_STATUSES)

        post.start_date = start_date
        post.end_date = end_date

        # Handle file attachment replacement
        if 'attachment' in request.files and request.files['attachment'].filename:
            file = request.files['attachment']
            if _allowed_file(file.filename):
                filename = secure_filename(file.filename)
                upload_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'posts')
                os.makedirs(upload_dir, exist_ok=True)
                filepath = os.path.join(upload_dir, filename)
                file.save(filepath)
                post.attachment_path = f'posts/{filename}'
            else:
                flash('Unsupported attachment file format.', 'warning')
        elif request.form.get('pre_attachment_path', '').strip():
            # Use the file that was pre-saved during AI extraction
            post.attachment_path = request.form.get('pre_attachment_path').strip()

        db.session.commit()
        flash('Shared Activity Post updated successfully!', 'success')
        return redirect(url_for('posts.manage'))

    return render_template('posts/form.html', post=post, departments=departments,
                           sources=POST_SOURCES, statuses=POST_STATUSES)


@posts_bp.route('/<int:post_id>/delete', methods=['POST'])
@login_required
@principal_required
def delete(post_id):
    """Delete a shared principal post."""
    post = PrincipalPost.query.get_or_404(post_id)
    if post.progress_status == 'COMPLETED':
        flash('Completed activities cannot be deleted.', 'danger')
        return redirect(url_for('posts.manage'))
        
    db.session.delete(post)
    db.session.commit()
    flash('Shared Activity Post deleted successfully.', 'success')
    return redirect(url_for('posts.manage'))


@posts_bp.route('/<int:post_id>/approve', methods=['POST'])
@login_required
@role_required('CHAIRPERSON')
def approve(post_id):
    """Chairperson approves a post and allocates it to a department."""
    post = PrincipalPost.query.get_or_404(post_id)
    department_ids = request.form.getlist('department_ids', type=int)

    if not department_ids:
        flash('Please select at least one department to allocate this activity to.', 'warning')
        return redirect(url_for('dashboard.index'))

    post.approval_status = 'APPROVED'
    post.approved_by = current_user.id
    post.approval_date = datetime.utcnow()
    post.approval_note = request.form.get('approval_note', '').strip() or None

    # Update many-to-many relationship
    depts = Department.query.filter(Department.id.in_(department_ids)).all()
    post.departments = depts

    # Maintain backward compatibility with department_id for legacy routes
    post.department_id = department_ids[0]

    db.session.commit()
    dept_names = ", ".join([d.name for d in depts])
    flash(f'Activity approved and allocated to {dept_names}!', 'success')
    return redirect(url_for('dashboard.index'))


@posts_bp.route('/<int:post_id>/reject', methods=['POST'])
@login_required
@role_required('CHAIRPERSON')
def reject(post_id):
    """Chairperson rejects a post."""
    post = PrincipalPost.query.get_or_404(post_id)
    post.approval_status = 'REJECTED'
    post.approved_by = current_user.id
    post.approval_date = datetime.utcnow()
    post.rejection_reason = request.form.get('rejection_reason', '').strip() or None

    db.session.commit()
    flash('Activity has been rejected.', 'info')
    return redirect(url_for('dashboard.index'))


@posts_bp.route('/uploads/<path:filename>')
@login_required
def download_file(filename):
    """Serve files from the uploads directory securely."""
    from flask import send_from_directory
    as_attachment = request.args.get('download') == '1'
    return send_from_directory(current_app.config['UPLOAD_FOLDER'], filename, as_attachment=as_attachment)


@posts_bp.route('/<int:post_id>/assign-faculty', methods=['POST'])
@login_required
@role_required('DEPT_COORDINATOR')
def assign_faculty(post_id):
    """Department Coordinator assigns a faculty lead to an approved post."""
    post = PrincipalPost.query.get_or_404(post_id)
    
    # Check if this post is allocated to the coordinator's department
    if current_user.department_id not in [d.id for d in post.departments]:
        abort(403)
        
    faculty_id = request.form.get('faculty_id', type=int)
    if not faculty_id:
        flash('Please select a valid faculty member.', 'warning')
        return redirect(url_for('dashboard.index'))
        
    # Verify the faculty belongs to coordinator's department
    from models.user import User
    faculty = User.query.filter_by(id=faculty_id, role='FACULTY', department_id=current_user.department_id).first()
    if not faculty:
        flash('Selected faculty is not in your department.', 'danger')
        return redirect(url_for('dashboard.index'))
        
    post.assigned_faculty_id = faculty_id
    db.session.commit()
    flash(f'Faculty Lead {faculty.full_name} assigned successfully!', 'success')
    return redirect(url_for('dashboard.index'))


@posts_bp.route('/<int:post_id>/update-progress', methods=['POST'])
@login_required
def update_progress(post_id):
    """Coordinator or assigned Faculty Lead updates post progress status."""
    post = PrincipalPost.query.get_or_404(post_id)
    
    # Authorization check
    is_coord = current_user.role == 'DEPT_COORDINATOR' and current_user.department_id in [d.id for d in post.departments]
    is_assigned = current_user.id == post.assigned_faculty_id
    
    if not (is_coord or is_assigned):
        abort(403)
        
    progress_status = request.form.get('progress_status')
    if progress_status not in [key for key, _ in POST_STATUSES]:
        flash('Invalid progress status.', 'danger')
        return redirect(url_for('dashboard.index'))
        
    post.progress_status = progress_status
    db.session.commit()
    flash(f'Activity progress updated to {post.status_label}!', 'success')
    return redirect(url_for('dashboard.index'))


@posts_bp.route('/<int:post_id>/form-builder', methods=['GET', 'POST'])
@login_required
@role_required('DEPT_COORDINATOR')
def form_builder(post_id):
    """Coordinator accesses and configures the student registration form builder."""
    post = PrincipalPost.query.get_or_404(post_id)
    
    # Check if this post is allocated to coordinator's department
    if current_user.department_id not in [d.id for d in post.departments]:
        abort(403)
        
    import json
    
    # Default fields that are always included in student registration
    default_fields = [
        {"id": "student_name", "label": "Full Name", "type": "text", "required": True, "is_default": True},
        {"id": "enrollment_no", "label": "Enrollment Number", "type": "text", "required": True, "is_default": True},
        {"id": "email", "label": "Email Address", "type": "email", "required": True, "is_default": True},
        {"id": "phone", "label": "Phone Number", "type": "tel", "required": False, "is_default": True},
        {"id": "semester", "label": "Current Semester", "type": "text", "required": False, "is_default": True},
        {"id": "department", "label": "Department", "type": "select", "options": ["Computer Engineering", "Information Technology", "Mechanical Engineering", "Civil Engineering", "Electrical Engineering", "Electronics & Communication"], "required": True, "is_default": True}
    ]
    
    if request.method == 'POST':
        # Read form configuration from JSON input or form fields
        config_data = request.form.get('config_json', '[]')
        try:
            custom_fields = json.loads(config_data)
            # Combine default fields and custom fields
            full_config = default_fields + custom_fields
            post.form_config = json.dumps(full_config)
            post.has_registration_form = True
            db.session.commit()
            flash('Registration form configuration saved successfully!', 'success')
            return redirect(url_for('dashboard.index'))
        except Exception as e:
            flash(f'Failed to save form config: {e}', 'danger')
            
    # Load existing custom fields (filtering out default ones)
    existing_custom = []
    if post.form_config:
        try:
            all_fields = json.loads(post.form_config)
            existing_custom = [f for f in all_fields if not f.get('is_default')]
        except Exception:
            existing_custom = []
            
    return render_template('posts/form_builder.html', post=post, custom_fields=existing_custom, default_fields=default_fields)


@posts_bp.route('/<int:post_id>/form-builder/auto', methods=['POST'])
@login_required
@role_required('DEPT_COORDINATOR')
def form_builder_auto(post_id):
    """AJAX endpoint to auto-suggest custom fields based on post details."""
    post = PrincipalPost.query.get_or_404(post_id)
    if current_user.department_id not in [d.id for d in post.departments]:
        return jsonify({"error": "Unauthorized"}), 403
        
    from services.form_generator import FormGenerator
    suggested_fields = FormGenerator.generate_fields(post)
    return jsonify({"success": True, "fields": suggested_fields})


@posts_bp.route('/<int:post_id>/register', methods=['GET', 'POST'])
def register(post_id):
    """Public route for students to register for the activity."""
    post = PrincipalPost.query.get_or_404(post_id)
    
    # Activity must be approved and have a registration form
    if post.approval_status != 'APPROVED' or not post.has_registration_form:
        abort(404)
        
    import json
    
    # Parse form configuration
    fields = []
    if post.form_config:
        try:
            fields = json.loads(post.form_config)
        except Exception:
            pass
            
    if not fields:
        abort(500, "Registration form configuration is corrupt.")
        
    if request.method == 'POST':
        student_name = request.form.get('student_name', '').strip()
        enrollment_no = request.form.get('enrollment_no', '').strip()
        email = request.form.get('email', '').strip()
        phone = request.form.get('phone', '').strip()
        semester = request.form.get('semester', '').strip()
        department = request.form.get('department', '').strip()
        
        # Basic validation
        if not student_name or not enrollment_no or not email or not department:
            flash('Full Name, Enrollment Number, Email, and Department are required.', 'danger')
            return render_template('posts/register.html', post=post, fields=fields)
            
        # Parse custom data answers
        custom_answers = {}
        for f in fields:
            if not f.get('is_default'):
                fid = f.get('id')
                val = request.form.get(f'custom_{fid}', '').strip()
                if f.get('required') and not val:
                    flash(f"The field '{f.get('label')}' is required.", 'danger')
                    return render_template('posts/register.html', post=post, fields=fields)
                custom_answers[fid] = val
                
        # Save Student Registration
        from models.student_registration import StudentRegistration
        reg = StudentRegistration(
            post_id=post.id,
            student_name=student_name,
            enrollment_no=enrollment_no,
            email=email,
            phone=phone or None,
            semester=semester or None,
            department=department or None,
            custom_data=json.dumps(custom_answers) if custom_answers else None
        )
        db.session.add(reg)
        db.session.commit()
        
        # Dynamic success message
        return render_template('posts/register.html', post=post, fields=fields, success_registered=True, student_name=student_name)
        
    return render_template('posts/register.html', post=post, fields=fields)


@posts_bp.route('/<int:post_id>/registrations/report')
@login_required
def registration_report(post_id):
    """Detailed registrations and statistical reports, visible to Lead Faculty, Coordinator, and Higher Authorities."""
    post = PrincipalPost.query.get_or_404(post_id)
    
    # Authorization checks
    is_mgmt = current_user.role in ('PRINCIPAL', 'CHAIRPERSON', 'RD_COORDINATOR')
    is_coord = current_user.role == 'DEPT_COORDINATOR' and current_user.department_id in [d.id for d in post.departments]
    is_assigned = current_user.id == post.assigned_faculty_id
    
    if not (is_mgmt or is_coord or is_assigned):
        abort(403)
        
    import json
    
    # Parse form config to get field headers
    fields = []
    custom_field_map = {}
    if post.form_config:
        try:
            fields = json.loads(post.form_config)
            custom_field_map = {f['id']: f['label'] for f in fields if not f.get('is_default')}
        except Exception:
            pass
            
    # Fetch registrations
    from models.student_registration import StudentRegistration
    registrations = StudentRegistration.query.filter_by(post_id=post.id).order_by(StudentRegistration.registered_at.desc()).all()
    
    # Helper to parse custom responses in template
    def get_custom_val(reg_obj, field_id):
        if not reg_obj.custom_data:
            return ""
        try:
            answers = json.loads(reg_obj.custom_data)
            return answers.get(field_id, "")
        except Exception:
            return ""
            
    # Calculations / Stats
    total_regs = len(registrations)
    semester_stats = {}
    for reg in registrations:
        sem = reg.semester or "Not Specified"
        semester_stats[sem] = semester_stats.get(sem, 0) + 1
        
    return render_template('posts/registration_report.html',
                           post=post,
                           registrations=registrations,
                           fields=fields,
                           custom_field_map=custom_field_map,
                           total_regs=total_regs,
                           semester_stats=semester_stats,
                           get_custom_val=get_custom_val)


@posts_bp.route('/<int:post_id>/report', methods=['GET', 'POST'])
@login_required
def report_form(post_id):
    """View/edit activity report before submitting it."""
    import json
    post = PrincipalPost.query.get_or_404(post_id)
    
    # Check if user is authorized
    is_mgmt = current_user.role in ('PRINCIPAL', 'CHAIRPERSON', 'RD_COORDINATOR')
    is_coord = current_user.role == 'DEPT_COORDINATOR' and current_user.department_id in [d.id for d in post.departments]
    is_assigned = current_user.id == post.assigned_faculty_id
    
    if not (is_mgmt or is_coord or is_assigned):
        abort(403)
        
    can_edit = is_coord or is_assigned or current_user.role == 'RD_COORDINATOR'
    
    # Check if a report already exists
    report = ActivityReport.query.filter_by(post_id=post.id).first()
    
    # Prefill default values from post if no report exists
    if not report:
        from models.student_registration import StudentRegistration
        reg_count = StudentRegistration.query.filter_by(post_id=post.id).count()
        
        date_str = ""
        if post.start_date:
            date_str = post.start_date.strftime('%A, %dth %B %Y')
            if post.end_date and post.end_date != post.start_date:
                date_str += " to " + post.end_date.strftime('%A, %dth %B %Y')
        else:
            date_str = "Not Specified"
            
        report_data = {
            'title': post.title,
            'event_type': 'Online workshop' if 'online' in post.title.lower() or 'online' in post.summary.lower() else 'Workshop',
            'event_date': date_str,
            'event_time': '12:00 PM to 2:00 PM',
            'event_mode': 'Online' if 'online' in post.title.lower() or 'online' in post.summary.lower() else 'Offline',
            'venue': 'Seminar Hall, GTU-ITR, Mehsana',
            'participants_demographic': 'GTU-ITR students and faculty members',
            'organized_by': 'GTU-ITR IIC Cell & GTU Venture',
            'supported_by': 'Institution’s Innovation Council (IIC) – Ministry of Education Initiative',
            'description': post.summary + "\n\n" + post.full_content,
            'num_participants': reg_count or 0,
            'status': 'DRAFT',
            'photos': []
        }
    else:
        photos = []
        if report.photos_json:
            try:
                photos = json.loads(report.photos_json)
            except Exception:
                pass
                
        report_data = {
            'title': report.title,
            'event_type': report.event_type,
            'event_date': report.event_date,
            'event_time': report.event_time,
            'event_mode': report.event_mode,
            'venue': report.venue,
            'participants_demographic': report.participants_demographic,
            'organized_by': report.organized_by,
            'supported_by': report.supported_by,
            'description': report.description,
            'num_participants': report.num_participants,
            'status': report.status,
            'photos': photos
        }
        
    if request.method == 'POST':
        if not can_edit:
            flash('You do not have permission to modify this report.', 'danger')
            return redirect(url_for('posts.report_form', post_id=post_id))
            
        action = request.form.get('action') # 'SAVE' or 'SUBMIT'
        
        # Parse fields from form
        title = request.form.get('title', '').strip()
        event_type = request.form.get('event_type', '').strip()
        event_date = request.form.get('event_date', '').strip()
        event_time = request.form.get('event_time', '').strip()
        event_mode = request.form.get('event_mode', 'Offline').strip()
        venue = request.form.get('venue', '').strip()
        participants_demographic = request.form.get('participants_demographic', '').strip()
        organized_by = request.form.get('organized_by', '').strip()
        supported_by = request.form.get('supported_by', '').strip()
        description = request.form.get('description', '').strip()
        num_participants = request.form.get('num_participants', type=int) or 0
        
        existing_photos = []
        if report and report.photos_json:
            try:
                existing_photos = json.loads(report.photos_json)
            except Exception:
                pass
                
        updated_photos = []
        for i, photo in enumerate(existing_photos):
            if request.form.get(f'delete_photo_{i}') == 'true':
                file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], photo['path'])
                if os.path.exists(file_path):
                    try:
                        os.remove(file_path)
                    except Exception:
                        pass
                continue
            caption = request.form.get(f'caption_existing_{i}', '').strip()
            updated_photos.append({
                'path': photo['path'],
                'caption': caption
            })
            
        # Handle uploads
        upload_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'reports', str(post.id))
        os.makedirs(upload_dir, exist_ok=True)
        
        for slot in range(6):
            file_key = f'photo_slot_{slot}'
            caption_key = f'caption_slot_{slot}'
            
            if file_key in request.files:
                file = request.files[file_key]
                caption = request.form.get(caption_key, '').strip()
                
                if file and file.filename and _allowed_file(file.filename):
                    filename = secure_filename(f"photo_{slot}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{file.filename}")
                    filepath = os.path.join(upload_dir, filename)
                    file.save(filepath)
                    updated_photos.append({
                        'path': f"reports/{post.id}/{filename}",
                        'caption': caption
                    })
                    
        # Save to DB
        if not report:
            report = ActivityReport(
                post_id=post.id,
                title=title,
                event_type=event_type,
                event_date=event_date,
                event_time=event_time,
                event_mode=event_mode,
                venue=venue,
                participants_demographic=participants_demographic,
                organized_by=organized_by,
                supported_by=supported_by,
                description=description,
                num_participants=num_participants,
                photos_json=json.dumps(updated_photos),
                status='SUBMITTED' if action == 'SUBMIT' else 'DRAFT'
            )
            db.session.add(report)
        else:
            report.title = title
            report.event_type = event_type
            report.event_date = event_date
            report.event_time = event_time
            report.event_mode = event_mode
            report.venue = venue
            report.participants_demographic = participants_demographic
            report.organized_by = organized_by
            report.supported_by = supported_by
            report.description = description
            report.num_participants = num_participants
            report.photos_json = json.dumps(updated_photos)
            
            if action == 'SUBMIT':
                report.status = 'SUBMITTED'
                
        if action == 'SUBMIT':
            post.progress_status = 'COMPLETED'
            
        db.session.commit()
        
        if action == 'SUBMIT':
            flash('Activity report has been submitted successfully, and the activity is marked COMPLETED!', 'success')
            return redirect(url_for('dashboard.index'))
        else:
            flash('Report draft saved successfully!', 'success')
            return redirect(url_for('posts.report_form', post_id=post.id))
            
    return render_template('posts/report_form.html', post=post, report=report, report_data=report_data, can_edit=can_edit)


@posts_bp.route('/<int:post_id>/report/download')
@login_required
def report_download(post_id):
    """Generate and download compiled activity report as a Word document."""
    post = PrincipalPost.query.get_or_404(post_id)
    report = ActivityReport.query.filter_by(post_id=post.id).first_or_404()
    
    is_mgmt = current_user.role in ('PRINCIPAL', 'CHAIRPERSON', 'RD_COORDINATOR')
    is_coord = current_user.role == 'DEPT_COORDINATOR' and current_user.department_id in [d.id for d in post.departments]
    is_assigned = current_user.id == post.assigned_faculty_id
    
    if not (is_mgmt or is_coord or is_assigned):
        abort(403)
        
    if report.status == 'DRAFT' and not (is_coord or is_assigned):
        abort(403, "Draft report is not visible to higher authorities yet.")
        
    logo_path = os.path.join(current_app.root_path, 'static', 'gtu_logo.png')
    
    # Generate Docx
    doc = ReportGenerator.generate(report, current_app.config['UPLOAD_FOLDER'], logo_path)
    
    export_dir = current_app.config.get('EXPORT_FOLDER', 'exports')
    os.makedirs(export_dir, exist_ok=True)
    
    filename = f"Activity_Report_{post.id}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}.docx"
    filepath = os.path.join(export_dir, filename)
    doc.save(filepath)
    
    from flask import send_from_directory
    return send_from_directory(export_dir, filename, as_attachment=True)


@posts_bp.route('/completed')
@login_required
@role_required('PRINCIPAL', 'CHAIRPERSON', 'RD_COORDINATOR', 'DEPT_COORDINATOR', 'FACULTY')
def completed_activities_list():
    """Page listing all completed activities with submitted reports (scoped by role)."""
    if current_user.role in ('PRINCIPAL', 'CHAIRPERSON', 'RD_COORDINATOR'):
        completed_posts = PrincipalPost.query.join(
            ActivityReport, PrincipalPost.id == ActivityReport.post_id
        ).filter(
            PrincipalPost.progress_status == 'COMPLETED',
            ActivityReport.status == 'SUBMITTED'
        ).order_by(PrincipalPost.created_at.desc()).all()
    elif current_user.role == 'DEPT_COORDINATOR' and current_user.department_id:
        completed_posts = PrincipalPost.query.join(
            ActivityReport, PrincipalPost.id == ActivityReport.post_id
        ).filter(
            PrincipalPost.progress_status == 'COMPLETED',
            ActivityReport.status == 'SUBMITTED',
            PrincipalPost.departments.any(id=current_user.department_id)
        ).order_by(PrincipalPost.created_at.desc()).all()
    elif current_user.role == 'FACULTY':
        completed_posts = PrincipalPost.query.join(
            ActivityReport, PrincipalPost.id == ActivityReport.post_id
        ).filter(
            PrincipalPost.progress_status == 'COMPLETED',
            ActivityReport.status == 'SUBMITTED',
            PrincipalPost.assigned_faculty_id == current_user.id
        ).order_by(PrincipalPost.created_at.desc()).all()
    else:
        completed_posts = []
        
    return render_template('posts/completed_activities.html', posts=completed_posts)


@posts_bp.route('/expired')
@login_required
@role_required('PRINCIPAL', 'CHAIRPERSON')
def expired_activities_list():
    """Page listing all expired activities (Principal & Chairperson only)."""
    PrincipalPost.check_and_update_expired()
    expired_posts = PrincipalPost.query.filter(
        PrincipalPost.progress_status == 'EXPIRED'
    ).order_by(PrincipalPost.created_at.desc()).all()
    
    return render_template('posts/expired_activities.html', posts=expired_posts)


@posts_bp.route('/calendar')
@login_required
def calendar_view():
    """Interactive calendar of activities based on publication/posting date."""
    PrincipalPost.check_and_update_expired()
    posts = PrincipalPost.query.filter(
        PrincipalPost.progress_status != 'EXPIRED'
    ).all()
    return render_template('posts/calendar.html', posts=posts)

