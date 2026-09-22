"""
GTU-ITR R&D & IIC Portal - Dynamic Form Builder & Registration Routes
"""
import os
import json
import time
import uuid
from datetime import datetime
from flask import render_template, redirect, url_for, flash, request, current_app, jsonify, abort
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename

from extensions import db
from models.principal_post import PrincipalPost
from models.student_registration import StudentRegistration
from . import posts_bp

ALLOWED_REG_FILE_EXT = {'pdf', 'docx', 'doc', 'txt', 'png', 'jpg', 'jpeg', 'zip', 'rar', 'pptx', 'ppt', 'csv', 'xlsx'}


@posts_bp.route('/<int:post_id>/form-builder', methods=['GET', 'POST'])
@login_required
def form_builder(post_id):
    """Coordinator or assigned Faculty Lead accesses and configures the student registration form builder."""
    post = PrincipalPost.query.get_or_404(post_id)
    
    # Check permissions using can_be_managed_by
    if not post.can_be_managed_by(current_user):
        abort(403)
        
    # Starter suggested fields that are 100% editable, reorderable, or removable
    starter_fields = [
        {"id": "student_name", "label": "Full Name", "type": "text", "required": True, "placeholder": "Enter your full legal name"},
        {"id": "enrollment_no", "label": "Enrollment Number", "type": "text", "required": True, "placeholder": "e.g. 231040107082"},
        {"id": "email", "label": "Email Address", "type": "email", "required": True, "placeholder": "e.g. student@gtu.ac.in"},
        {"id": "phone", "label": "Phone / WhatsApp Number", "type": "tel", "required": False, "placeholder": "e.g. +91 98765 43210"},
        {"id": "department", "label": "Department", "type": "select", "options": ["Computer Engineering", "Information Technology", "Mechanical Engineering", "Civil Engineering", "Electrical Engineering", "Electronics & Communication"], "required": True},
        {"id": "semester", "label": "Current Semester", "type": "select", "options": ["1", "2", "3", "4", "5", "6", "7", "8"], "required": False}
    ]
    
    if request.method == 'POST':
        # Read form configuration from JSON input
        config_data = request.form.get('config_json', '[]')
        deadline_str = request.form.get('registration_deadline', '').strip()
        
        try:
            full_config = json.loads(config_data)
            if not isinstance(full_config, list) or len(full_config) == 0:
                full_config = starter_fields

            # Guarantee all field IDs are unique and valid
            seen_ids = set()
            for idx, f in enumerate(full_config):
                fid = (f.get('id') or '').strip()
                if not fid or fid in seen_ids:
                    fid = f"{fid or 'field'}_{int(time.time())}_{idx + 1}"
                    f['id'] = fid
                seen_ids.add(fid)

            post.form_config = json.dumps(full_config)
            post.has_registration_form = True
            
            # Save custom registration deadline
            if deadline_str:
                try:
                    post.registration_deadline = datetime.strptime(deadline_str, '%Y-%m-%dT%H:%M')
                except ValueError:
                    try:
                        post.registration_deadline = datetime.strptime(deadline_str, '%Y-%m-%d')
                    except ValueError:
                        post.registration_deadline = None
            else:
                post.registration_deadline = None

            # Save customizable form heading, subtitle, and badge
            form_title = request.form.get('form_title', '').strip()
            form_subtitle = request.form.get('form_subtitle', '').strip()
            form_badge = request.form.get('form_badge', '').strip()

            post.form_title = form_title or None
            post.form_subtitle = form_subtitle or None
            post.form_badge = form_badge or None

            if 'external_registration_url' in request.form:
                post.external_registration_url = request.form.get('external_registration_url', '').strip() or None
            if 'is_public' in request.form:
                post.is_public = request.form.get('is_public') == '1'

            db.session.commit()

            # Real-time sync of updated deadline to Cloud Firebase
            try:
                from utils.firebase_sync import sync_post_settings_to_firebase
                sync_post_settings_to_firebase(post)
            except Exception as e:
                current_app.logger.warning(f"Could not sync post settings to Firebase: {e}")

            flash('Registration form configuration and settings saved successfully!', 'success')
            return redirect(url_for('dashboard.index'))
        except Exception as e:
            flash(f'Failed to save form config: {e}', 'danger')
            
    # Load existing fields (or use starter editable fields if none set yet)
    existing_fields = []
    if post.form_config:
        try:
            existing_fields = json.loads(post.form_config)
        except Exception:
            existing_fields = []
            
    if not existing_fields:
        existing_fields = starter_fields
            
    return render_template('posts/form_builder.html', post=post, existing_fields=existing_fields)


@posts_bp.route('/<int:post_id>/form-builder/auto', methods=['POST'])
@login_required
def form_builder_auto(post_id):
    """AJAX endpoint to auto-suggest custom fields based on post details."""
    post = PrincipalPost.query.get_or_404(post_id)
    if not post.can_be_managed_by(current_user):
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
        
    # Format closed deadline text for display
    closed_deadline_formatted = None
    if post.registration_deadline:
        closed_deadline_formatted = post.registration_deadline.strftime('%B %d, %Y at %I:%M %p')
    elif post.end_date:
        closed_deadline_formatted = post.end_date.strftime('%B %d, %Y')

    # Check if registration is closed (deadline passed or completed)
    if post.is_registration_closed:
        return render_template('posts/register.html', post=post, fields=[], 
                               is_closed=True, 
                               closed_deadline_formatted=closed_deadline_formatted or 'recently')

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
        answers = {}

        # Loop through all configured form fields
        for f in fields:
            fid = f.get('id')
            ftype = f.get('type', 'text')
            flabel = f.get('label', 'Field')
            is_req = f.get('required', False)

            val = ""
            if ftype == 'file':
                # File upload handling
                file_obj = request.files.get(f'field_{fid}') or request.files.get(fid)
                if file_obj and file_obj.filename:
                    fname = secure_filename(file_obj.filename)
                    ext = fname.rsplit('.', 1)[1].lower() if '.' in fname else ''
                    if ext not in ALLOWED_REG_FILE_EXT:
                        flash(f"File for '{flabel}' must be one of: {', '.join(sorted(ALLOWED_REG_FILE_EXT))}", 'danger')
                        return render_template('posts/register.html', post=post, fields=fields)

                    upload_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'registrations', str(post.id))
                    os.makedirs(upload_dir, exist_ok=True)
                    stored_fname = f"{uuid.uuid4().hex[:8]}_{fname}"
                    file_obj.save(os.path.join(upload_dir, stored_fname))
                    val = f"registrations/{post.id}/{stored_fname}"
                elif is_req:
                    flash(f"Please upload a file for '{flabel}'.", 'danger')
                    return render_template('posts/register.html', post=post, fields=fields)
            elif ftype == 'checkbox':
                vals = request.form.getlist(f'field_{fid}') or request.form.getlist(fid)
                val = ", ".join(vals)
                if is_req and not val:
                    flash(f"The field '{flabel}' is required.", 'danger')
                    return render_template('posts/register.html', post=post, fields=fields)
            else:
                val = request.form.get(f'field_{fid}', '').strip()
                if not val:
                    val = request.form.get(fid, '').strip()
                if is_req and not val:
                    flash(f"The field '{flabel}' is required.", 'danger')
                    return render_template('posts/register.html', post=post, fields=fields)

            answers[fid] = val

        # Extract core columns for StudentRegistration database record
        student_name = answers.get('student_name') or ""
        if not student_name:
            for fid, v in answers.items():
                fl = next((f.get('label', '').lower() for f in fields if f.get('id') == fid), '')
                if 'name' in fl or 'student' in fl:
                    student_name = v
                    break
        if not student_name:
            student_name = "Registered Participant"

        enrollment_no = answers.get('enrollment_no') or ""
        if not enrollment_no:
            for fid, v in answers.items():
                fl = next((f.get('label', '').lower() for f in fields if f.get('id') == fid), '')
                if any(kw in fl for kw in ['enroll', 'roll', 'enrolment']) or fl.strip() in ('id', 'id no', 'id number', 'student id'):
                    enrollment_no = v
                    break
        if not enrollment_no:
            enrollment_no = f"REG-{int(time.time())}"

        email = answers.get('email') or ""
        if not email:
            for f in fields:
                if f.get('type') == 'email' and answers.get(f.get('id')):
                    email = answers[f['id']]
                    break

        phone = answers.get('phone') or ""
        if not phone:
            for f in fields:
                if f.get('type') == 'tel' and answers.get(f.get('id')):
                    phone = answers[f['id']]
                    break

        semester = answers.get('semester') or ""
        if not semester:
            for fid, v in answers.items():
                fl = next((f.get('label', '').lower() for f in fields if f.get('id') == fid), '')
                if 'sem' in fl:
                    semester = v
                    break

        department = answers.get('department') or ""
        if not department:
            for fid, v in answers.items():
                fl = next((f.get('label', '').lower() for f in fields if f.get('id') == fid), '')
                if 'dept' in fl or 'branch' in fl or 'department' in fl:
                    department = v
                    break

        # Duplicate check if valid enrollment or email exists
        if email or (enrollment_no and not enrollment_no.startswith('REG-')):
            dup_filters = []
            if enrollment_no and not enrollment_no.startswith('REG-'):
                dup_filters.append(StudentRegistration.enrollment_no == enrollment_no)
            if email and email != 'not-provided@gtu.ac.in':
                dup_filters.append(StudentRegistration.email == email)

            if dup_filters:
                existing_reg = StudentRegistration.query.filter(
                    StudentRegistration.post_id == post.id,
                    db.or_(*dup_filters)
                ).first()
                if existing_reg:
                    # Automatically update existing team's details, presentation files, and custom data
                    existing_reg.student_name = student_name or existing_reg.student_name
                    existing_reg.phone = phone or existing_reg.phone
                    existing_reg.semester = semester or existing_reg.semester
                    existing_reg.department = department or existing_reg.department
                    existing_reg.custom_data = json.dumps(answers)
                    db.session.commit()

                    # Trigger auto-export to attendance database and links
                    if post.id == 2:
                        try:
                            from routes.attendance import export_sih_teams_json
                            export_sih_teams_json()
                        except Exception as e:
                            current_app.logger.warning(f"Could not auto-export SIH teams: {e}")

                    # Real-time Cloud Firebase Backup
                    try:
                        from utils.firebase_sync import backup_single_registration_to_firebase
                        backup_single_registration_to_firebase(existing_reg, post, answers)
                    except Exception as e:
                        current_app.logger.warning(f"Could not backup registration to Firebase: {e}")

                    flash('Your registration and uploaded files have been updated successfully!', 'success')
                    return render_template('posts/register.html', post=post, fields=fields, success_registered=True, student_name=student_name)

        # Save Student Registration
        reg = StudentRegistration(
            post_id=post.id,
            student_name=student_name,
            enrollment_no=enrollment_no,
            email=email or 'not-provided@gtu.ac.in',
            phone=phone or None,
            semester=semester or None,
            department=department or None,
            custom_data=json.dumps(answers)
        )
        db.session.add(reg)
        db.session.commit()

        # Trigger auto-export to attendance database and links
        if post.id == 2:
            try:
                from routes.attendance import export_sih_teams_json
                export_sih_teams_json()
            except Exception as e:
                current_app.logger.warning(f"Could not auto-export SIH teams: {e}")

        # Real-time Cloud Firebase Backup
        try:
            from utils.firebase_sync import backup_single_registration_to_firebase
            backup_single_registration_to_firebase(reg, post, answers)
        except Exception as e:
            current_app.logger.warning(f"Could not backup registration to Firebase in real-time: {e}")

        # Dynamic success message
        return render_template('posts/register.html', post=post, fields=fields, success_registered=True, student_name=student_name)

    return render_template('posts/register.html', post=post, fields=fields)
