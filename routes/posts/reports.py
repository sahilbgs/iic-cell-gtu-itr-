"""
GTU-ITR R&D & IIC Portal - Activity Report Routes (Draft, Submit, Download DOCX)
"""
import os
import json
from datetime import datetime
from flask import render_template, redirect, url_for, flash, request, current_app, abort, send_from_directory
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename

from extensions import db
from models.principal_post import PrincipalPost
from models.activity_report import ActivityReport
from services.report_generator import ReportGenerator
from . import posts_bp, _allowed_file


@posts_bp.route('/<int:post_id>/report', methods=['GET', 'POST'])
@login_required
def report_form(post_id):
    """View/edit activity report before submitting it."""
    post = PrincipalPost.query.get_or_404(post_id)
    
    # Check if user is authorized
    is_mgmt = current_user.is_management
    is_coord = current_user.role == 'HOD' and current_user.department_id in [d.id for d in post.departments]
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
            
        action = request.form.get('action')  # 'SAVE' or 'SUBMIT'
        
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
    
    is_mgmt = current_user.is_management
    is_coord = current_user.role == 'HOD' and current_user.department_id in [d.id for d in post.departments]
    is_assigned = current_user.id == post.assigned_faculty_id
    
    if not (is_mgmt or is_coord or is_assigned):
        abort(403)
        
    if report.status == 'DRAFT' and not (is_coord or is_assigned):
        abort(403, "Draft report is not visible to higher authorities yet.")
        
    logo_path = os.path.join(current_app.root_path, 'static', 'images', 'gtu_logo.png')
    if not os.path.exists(logo_path):
        logo_path = os.path.join(current_app.root_path, 'static', 'gtu_logo.png')
    
    # Generate Docx
    doc = ReportGenerator.generate(report, current_app.config['UPLOAD_FOLDER'], logo_path)
    
    export_dir = current_app.config.get('EXPORT_FOLDER', 'exports')
    os.makedirs(export_dir, exist_ok=True)
    
    filename = f"Activity_Report_{post.id}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}.docx"
    filepath = os.path.join(export_dir, filename)
    doc.save(filepath)
    
    return send_from_directory(export_dir, filename, as_attachment=True)
