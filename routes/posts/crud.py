"""
GTU-ITR R&D & IIC Portal - Principal Post CRUD & Status Routes
"""
import os
from datetime import datetime
from flask import render_template, redirect, url_for, flash, request, current_app, jsonify, abort, send_from_directory
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename

from extensions import db
from models.principal_post import PrincipalPost, POST_SOURCES, POST_STATUSES
from models.department import Department
from models.activity_report import ActivityReport
from models.user import User
from utils.decorators import principal_required, role_required
from . import posts_bp, _allowed_file


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
def view_post(post_id):
    """View full details and attachment of a post on a dedicated page."""
    post = PrincipalPost.query.get_or_404(post_id)
    if not current_user.is_authenticated:
        if not (post.is_public and post.approval_status == 'APPROVED'):
            return redirect(url_for('auth.login', next=request.url))
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


@posts_bp.route('/create', methods=['GET', 'POST'])
@login_required
@principal_required
def create():
    """Create a new shared principal post."""
    departments = Department.query.filter_by(is_deleted=False).order_by(Department.name).all()
    
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

        is_public = request.form.get('is_public') == '1'
        external_registration_url = request.form.get('external_registration_url', '').strip() or None

        post = PrincipalPost(
            title=title,
            source=source,
            summary=summary,
            full_content=full_content,
            progress_status=progress_status,
            department_id=department_id or None,
            created_by=current_user.id,
            start_date=start_date,
            end_date=end_date,
            is_public=is_public,
            external_registration_url=external_registration_url
        )

        # Auto-approve if created by PRINCIPAL, CHAIRPERSON, or MASTER_ADMIN
        if current_user.role in ('PRINCIPAL', 'CHAIRPERSON', 'MASTER_ADMIN'):
            post.approval_status = 'APPROVED'
            post.approved_by = current_user.id
            post.approval_date = datetime.utcnow()

        # Link departments relationship
        if department_id:
            dept = Department.query.get(department_id)
            if dept:
                post.departments = [dept]

        # Handle file attachment
        if 'attachment' in request.files and request.files['attachment'].filename:
            file = request.files['attachment']
            if _allowed_file(file.filename):
                import uuid
                clean_name = secure_filename(file.filename)
                filename = f"{uuid.uuid4().hex[:8]}_{clean_name}"
                upload_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'posts')
                os.makedirs(upload_dir, exist_ok=True)
                filepath = os.path.join(upload_dir, filename)
                file.save(filepath)
                post.attachment_path = f'posts/{filename}'
            else:
                flash('Unsupported attachment file format.', 'warning')
        elif request.form.get('pre_attachment_path', '').strip():
            # Use the file that was pre-saved during AI extraction (sanitized)
            pre_path = request.form.get('pre_attachment_path').strip()
            if pre_path.startswith('posts/') and '..' not in pre_path:
                post.attachment_path = pre_path

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
        
    departments = Department.query.filter_by(is_deleted=False).order_by(Department.name).all()
    
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
        post.is_public = request.form.get('is_public') == '1'
        post.external_registration_url = request.form.get('external_registration_url', '').strip() or None

        # Handle file attachment replacement
        if 'attachment' in request.files and request.files['attachment'].filename:
            file = request.files['attachment']
            if _allowed_file(file.filename):
                import uuid
                clean_name = secure_filename(file.filename)
                filename = f"{uuid.uuid4().hex[:8]}_{clean_name}"
                upload_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'posts')
                os.makedirs(upload_dir, exist_ok=True)
                filepath = os.path.join(upload_dir, filename)
                file.save(filepath)
                post.attachment_path = f'posts/{filename}'
            else:
                flash('Unsupported attachment file format.', 'warning')
        elif request.form.get('pre_attachment_path', '').strip():
            # Use the file that was pre-saved during AI extraction (sanitized)
            pre_path = request.form.get('pre_attachment_path').strip()
            if pre_path.startswith('posts/') and '..' not in pre_path:
                post.attachment_path = pre_path

        db.session.commit()

        # Real-time sync of updated dates/settings to Cloud Firebase
        try:
            from utils.firebase_sync import sync_post_settings_to_firebase
            sync_post_settings_to_firebase(post)
        except Exception as e:
            current_app.logger.warning(f"Could not sync post settings to Firebase: {e}")

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


@posts_bp.route('/<int:post_id>/toggle-public', methods=['POST'])
@login_required
def toggle_public(post_id):
    """Toggle public visibility for an activity on Announcements and Home Page."""
    post = PrincipalPost.query.get_or_404(post_id)
    
    if not post.can_be_managed_by(current_user):
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.is_json:
            return jsonify({'success': False, 'error': 'You do not have permission to modify this activity’s public status.'}), 403
        flash('You do not have permission to publish or unpublish this activity.', 'danger')
        return redirect(request.referrer or url_for('posts.manage'))

    post.is_public = not post.is_public
    db.session.commit()

    status_str = "published to Public Announcements & Home Page" if post.is_public else "hidden from public view (internal only)"
    flash_msg = f'Activity "{post.title[:35]}..." {status_str}.'

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.is_json:
        return jsonify({
            'success': True,
            'is_public': post.is_public,
            'message': flash_msg
        })

    flash(flash_msg, 'success')
    return redirect(request.referrer or url_for('posts.manage'))


@posts_bp.route('/uploads/<path:filename>')
def download_file(filename):
    """Serve files from the uploads directory securely."""
    as_attachment = request.args.get('download') == '1'

    # If unauthenticated, check if the file belongs to an approved, public post
    if not current_user.is_authenticated:
        base_fname = filename.split('/')[-1]
        public_post = PrincipalPost.query.filter(
            PrincipalPost.attachment_path.like(f'%{base_fname}%'),
            PrincipalPost.is_public == True,
            PrincipalPost.approval_status == 'APPROVED'
        ).first()
        if not public_post:
            return redirect(url_for('auth.login', next=request.url))

    return send_from_directory(current_app.config['UPLOAD_FOLDER'], filename, as_attachment=as_attachment)


@posts_bp.route('/<int:post_id>/assign-faculty', methods=['POST'])
@login_required
@role_required('HOD')
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
    faculty = User.query.filter_by(id=faculty_id, role='FACULTY', department_id=current_user.department_id, is_deleted=False).first()
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
    is_coord = current_user.role == 'HOD' and current_user.department_id in [d.id for d in post.departments]
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


@posts_bp.route('/completed')
@login_required
@role_required('PRINCIPAL', 'CHAIRPERSON', 'RD_COORDINATOR', 'HOD', 'FACULTY')
def completed_activities_list():
    """Page listing all completed activities with submitted reports (scoped by role)."""
    if current_user.is_management:
        completed_posts = PrincipalPost.query.join(
            ActivityReport, PrincipalPost.id == ActivityReport.post_id
        ).filter(
            PrincipalPost.progress_status == 'COMPLETED',
            ActivityReport.status == 'SUBMITTED'
        ).order_by(PrincipalPost.created_at.desc()).all()
    elif current_user.role == 'HOD' and current_user.department_id:
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
