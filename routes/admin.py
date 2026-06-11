"""
GTU-ITR R&D & IIC Portal - Admin Panel Routes
Blueprint: admin  |  Prefix: /admin
Only accessible by CHAIRPERSON role.
"""
from functools import wraps
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, abort, current_app
from werkzeug.utils import secure_filename
import os
from flask_login import login_required, current_user
from extensions import db
from models.user import User, ROLES, ROLE_LABELS
from models.department import Department
from models.landing_post import LandingPost

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')


def chairperson_required(f):
    """Decorator: only CHAIRPERSON can access admin routes."""
    @wraps(f)
    @login_required
    def decorated(*args, **kwargs):
        if current_user.role != 'CHAIRPERSON':
            abort(403)
        return f(*args, **kwargs)
    return decorated


# --------------------------------------------------------------------------- #
#  Admin Dashboard
# --------------------------------------------------------------------------- #
@admin_bp.route('/')
@chairperson_required
def index():
    """Admin panel – manage users, departments, faculties, and legal compliance."""
    import os
    from flask import current_app
    
    users = User.query.filter_by(is_deleted=False).order_by(User.full_name).all()
    departments = Department.query.filter_by(is_deleted=False).order_by(Department.name).all()
    
    # Legal & Compliance Verification checks
    base_path = current_app.root_path
    
    compliance_checks = {
        'ownership_doc': os.path.exists(os.path.join(base_path, 'OWNERSHIP.md')),
        'opensource_doc': os.path.exists(os.path.join(base_path, 'OPEN_SOURCE_COMPLIANCE.md')),
        'changelog_doc': os.path.exists(os.path.join(base_path, 'legal_records', 'CHANGELOG.md')),
        'architecture_doc': os.path.exists(os.path.join(base_path, 'legal_records', 'ARCHITECTURE.md')),
        'security_doc': os.path.exists(os.path.join(base_path, 'legal_records', 'SECURITY_AUDIT.md')),
        'deployment_doc': os.path.exists(os.path.join(base_path, 'legal_records', 'DEPLOYMENT.md')),
        'session_secure': current_app.config.get('SESSION_COOKIE_SECURE', False),
        'remember_secure': current_app.config.get('REMEMBER_COOKIE_SECURE', False),
        'csrf_enabled': current_app.config.get('WTF_CSRF_ENABLED', True),
        'privacy_policy_view': True,
        'terms_view': True
    }
    
    # Calculate overall compliance percentage
    total_checks = len(compliance_checks)
    passed_checks = sum(1 for v in compliance_checks.values() if v)
    compliance_score = int((passed_checks / total_checks) * 100) if total_checks > 0 else 0
    
    config_name = os.environ.get('FLASK_ENV', 'development')
    
    return render_template('admin/index.html',
                           users=users,
                           departments=departments,
                           roles=ROLES,
                           role_labels=ROLE_LABELS,
                           compliance_checks=compliance_checks,
                           compliance_score=compliance_score,
                           config_name=config_name)


# --------------------------------------------------------------------------- #
#  USER MANAGEMENT
# --------------------------------------------------------------------------- #
@admin_bp.route('/users/create', methods=['POST'])
@chairperson_required
def create_user():
    """Create a new user account."""
    email = request.form.get('email', '').strip().lower()
    full_name = request.form.get('full_name', '').strip()
    password = request.form.get('password', '')
    role = request.form.get('role', 'FACULTY')
    department_id = request.form.get('department_id', type=int)
    phone = request.form.get('phone', '').strip()
    designation = request.form.get('designation', '').strip()

    # Validation
    errors = []
    if not email:
        errors.append('Email is required.')
    if not full_name:
        errors.append('Full name is required.')
    if len(password) < 6:
        errors.append('Password must be at least 6 characters.')
    if role not in ROLES:
        errors.append('Invalid role selected.')
    if User.query.filter_by(email=email).first():
        errors.append('An account with that email already exists.')

    if errors:
        for err in errors:
            flash(err, 'danger')
        return redirect(url_for('admin.index'))

    user = User(
        email=email,
        full_name=full_name,
        role=role,
        department_id=department_id or None,
        phone=phone or None,
        designation=designation or None,
    )
    user.set_password(password)
    db.session.add(user)
    db.session.commit()

    flash(f'User "{full_name}" created successfully with role {ROLE_LABELS.get(role, role)}.', 'success')
    return redirect(url_for('admin.index'))


@admin_bp.route('/users/<int:user_id>/edit', methods=['POST'])
@chairperson_required
def edit_user(user_id):
    """Edit an existing user."""
    user = User.query.get_or_404(user_id)

    user.full_name = request.form.get('full_name', user.full_name).strip()
    user.email = request.form.get('email', user.email).strip().lower()
    user.role = request.form.get('role', user.role)
    user.phone = request.form.get('phone', '').strip() or None
    user.designation = request.form.get('designation', '').strip() or None

    dept_id = request.form.get('department_id', type=int)
    user.department_id = dept_id or None

    # Optional password reset
    new_password = request.form.get('new_password', '').strip()
    if new_password:
        if len(new_password) < 6:
            flash('Password must be at least 6 characters.', 'danger')
            return redirect(url_for('admin.index'))
        user.set_password(new_password)

    if user.role not in ROLES:
        flash('Invalid role selected.', 'danger')
        return redirect(url_for('admin.index'))

    db.session.commit()
    flash(f'User "{user.full_name}" updated successfully.', 'success')
    return redirect(url_for('admin.index'))


@admin_bp.route('/users/<int:user_id>/toggle-active', methods=['POST'])
@chairperson_required
def toggle_user_active(user_id):
    """Activate / deactivate a user."""
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        flash('You cannot deactivate your own account.', 'warning')
        return redirect(url_for('admin.index'))
    user.is_active = not user.is_active
    db.session.commit()
    status = 'activated' if user.is_active else 'deactivated'
    flash(f'User "{user.full_name}" has been {status}.', 'success')
    return redirect(url_for('admin.index'))


@admin_bp.route('/users/<int:user_id>/delete', methods=['POST'])
@chairperson_required
def delete_user(user_id):
    """Soft delete a user."""
    if user_id == current_user.id:
        flash('You cannot delete your own account.', 'danger')
        return redirect(url_for('admin.index'))
    
    user = User.query.get_or_404(user_id)
    user.is_deleted = True
    user.is_active = False # Deactivate as well
    db.session.commit()
    flash(f'User {user.full_name} has been deleted.', 'success')
    return redirect(url_for('admin.index'))


# --------------------------------------------------------------------------- #
#  DEPARTMENT MANAGEMENT
# --------------------------------------------------------------------------- #
@admin_bp.route('/departments/create', methods=['POST'])
@chairperson_required
def create_department():
    """Create a new department."""
    name = request.form.get('name', '').strip()
    code = request.form.get('code', '').strip().upper()
    hod_name = request.form.get('hod_name', '').strip()
    email = request.form.get('dept_email', '').strip()
    phone = request.form.get('dept_phone', '').strip()

    errors = []
    if not name:
        errors.append('Department name is required.')
    if not code:
        errors.append('Department code is required.')
    if Department.query.filter_by(code=code, is_deleted=False).first():
        errors.append(f'Department with code "{code}" already exists.')
    if Department.query.filter_by(name=name, is_deleted=False).first():
        errors.append(f'Department with name "{name}" already exists.')

    if errors:
        for err in errors:
            flash(err, 'danger')
        return redirect(url_for('admin.index'))

    dept = Department(
        name=name,
        code=code,
        hod_name=hod_name or None,
        email=email or None,
        phone=phone or None,
    )
    db.session.add(dept)
    db.session.commit()

    flash(f'Department "{name}" ({code}) created successfully.', 'success')
    return redirect(url_for('admin.index'))


@admin_bp.route('/departments/<int:dept_id>/edit', methods=['POST'])
@chairperson_required
def edit_department(dept_id):
    """Edit an existing department."""
    dept = Department.query.get_or_404(dept_id)
    dept.name = request.form.get('name', dept.name).strip()
    dept.code = request.form.get('code', dept.code).strip().upper()
    dept.hod_name = request.form.get('hod_name', '').strip() or None
    dept.email = request.form.get('dept_email', '').strip() or None
    dept.phone = request.form.get('dept_phone', '').strip() or None

    db.session.commit()
    flash(f'Department "{dept.name}" updated successfully.', 'success')
    return redirect(url_for('admin.index'))


@admin_bp.route('/departments/<int:dept_id>/delete', methods=['POST'])
@chairperson_required
def delete_department(dept_id):
    """Soft delete a department."""
    dept = Department.query.get_or_404(dept_id)
    dept.is_deleted = True
    db.session.commit()
    flash(f'Department {dept.name} has been deleted.', 'success')
    return redirect(url_for('admin.index', tab='departments-tab'))


# --------------------------------------------------------------------------- #
#  API: User data for edit modal (AJAX)
# --------------------------------------------------------------------------- #
@admin_bp.route('/api/users/<int:user_id>', methods=['GET'])
@chairperson_required
def api_get_user(user_id):
    """Return user data as JSON for edit modal."""
    user = User.query.get_or_404(user_id)
    return jsonify({
        'id': user.id,
        'email': user.email,
        'full_name': user.full_name,
        'role': user.role,
        'department_id': user.department_id,
        'phone': user.phone or '',
        'designation': user.designation or '',
        'is_active': user.is_active,
    })


@admin_bp.route('/api/departments/<int:dept_id>', methods=['GET'])
@chairperson_required
def api_get_department(dept_id):
    """Return department data as JSON for edit modal."""
    dept = Department.query.get_or_404(dept_id)
    return jsonify({
        'id': dept.id,
        'name': dept.name,
        'code': dept.code,
        'hod_name': dept.hod_name or '',
        'email': dept.email or '',
        'phone': dept.phone or '',
    })

# --------------------------------------------------------------------------- #
#  LANDING PAGE POSTS MANAGEMENT (Chairperson)
# --------------------------------------------------------------------------- #
from datetime import datetime

@admin_bp.route('/landing-posts')
@chairperson_required
def manage_landing_posts():
    """View and manage landing page posts."""
    posts = LandingPost.query.filter_by(is_deleted=False).order_by(LandingPost.created_at.desc()).all()
    return render_template('admin/landing_posts.html', posts=posts)

@admin_bp.route('/landing-posts/create', methods=['POST'])
@chairperson_required
def create_landing_post():
    """Create a new landing page post with optional media upload."""
    title = request.form.get('title', '').strip()
    description = request.form.get('description', '').strip()
    media_file = request.files.get('media_file')
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
    
    if not title or not description:
        if is_ajax:
            return jsonify({'success': False, 'message': 'Title and description are required.'}), 400
        flash('Title and description are required.', 'danger')
        return redirect(url_for('admin.manage_landing_posts'))
    
    post = LandingPost(
        title=title,
        description=description,
        author_id=current_user.id
    )
    
    try:
        if media_file and media_file.filename:
            filename = secure_filename(media_file.filename)
            timestamp = int(datetime.utcnow().timestamp())
            safe_filename = f"landing_{timestamp}_{filename}"
            
            upload_folder = current_app.config.get('UPLOAD_FOLDER', 'uploads')
            if not os.path.isabs(upload_folder):
                upload_folder = os.path.join(current_app.root_path, upload_folder)
            os.makedirs(upload_folder, exist_ok=True)
            file_path = os.path.join(upload_folder, safe_filename)
            media_file.save(file_path)
            
            post.media_path = safe_filename
            
            # Simple mime type checking
            ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''
            if ext in ['mp4', 'webm', 'ogg']:
                post.media_type = 'video'
            else:
                post.media_type = 'image'
                
        db.session.add(post)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        if is_ajax:
            return jsonify({'success': False, 'message': f'Server Error: {str(e)}'}), 500
        flash(f'Error creating post: {str(e)}', 'danger')
        return redirect(url_for('admin.manage_landing_posts'))
    
    if is_ajax:
        return jsonify({'success': True, 'message': 'Landing post created successfully.'}), 200
    
    flash('Landing post created successfully.', 'success')
    return redirect(url_for('admin.manage_landing_posts'))

@admin_bp.route('/landing-posts/<int:post_id>/toggle-pin', methods=['POST'])
@chairperson_required
def toggle_pin_landing_post(post_id):
    post = LandingPost.query.get_or_404(post_id)
    post.is_pinned = not post.is_pinned
    db.session.commit()
    flash(f'Post {"pinned" if post.is_pinned else "unpinned"}.', 'success')
    return redirect(url_for('admin.manage_landing_posts'))

@admin_bp.route('/landing-posts/<int:post_id>/toggle-hide', methods=['POST'])
@chairperson_required
def toggle_hide_landing_post(post_id):
    post = LandingPost.query.get_or_404(post_id)
    post.is_hidden = not post.is_hidden
    db.session.commit()
    flash(f'Post {"hidden" if post.is_hidden else "unhidden"}.', 'success')
    return redirect(url_for('admin.manage_landing_posts'))

@admin_bp.route('/landing-posts/<int:post_id>/delete', methods=['POST'])
@chairperson_required
def delete_landing_post(post_id):
    post = LandingPost.query.get_or_404(post_id)
    post.is_deleted = True
    db.session.commit()
    flash('Post deleted.', 'success')
    return redirect(url_for('admin.manage_landing_posts'))

# --------------------------------------------------------------------------- #
#  MAINTENANCE PAGE (Soft Deletes)
# --------------------------------------------------------------------------- #
from flask import session

@admin_bp.route('/maintenance', methods=['GET', 'POST'])
@chairperson_required
def maintenance():
    """Secure maintenance page for restoring soft-deleted data."""
    if request.method == 'POST':
        password = request.form.get('password')
        if password == '44113290@sahil':
            session['maintenance_unlocked'] = True
            flash('Maintenance mode unlocked.', 'success')
            return redirect(url_for('admin.maintenance'))
        else:
            flash('Invalid maintenance password.', 'danger')
            return redirect(url_for('admin.maintenance'))
            
    if not session.get('maintenance_unlocked'):
        return render_template('admin/maintenance_login.html')
        
    deleted_users = User.query.filter_by(is_deleted=True).all()
    deleted_depts = Department.query.filter_by(is_deleted=True).all()
    deleted_posts = LandingPost.query.filter_by(is_deleted=True).all()
    
    return render_template('admin/maintenance.html', 
                           deleted_users=deleted_users,
                           deleted_depts=deleted_depts,
                           deleted_posts=deleted_posts)

@admin_bp.route('/maintenance/restore/<string:model_type>/<int:item_id>', methods=['POST'])
@chairperson_required
def restore_item(model_type, item_id):
    if not session.get('maintenance_unlocked'):
        return abort(403)
        
    if model_type == 'user':
        item = User.query.get_or_404(item_id)
        item.is_active = True
    elif model_type == 'department':
        item = Department.query.get_or_404(item_id)
    elif model_type == 'landing_post':
        item = LandingPost.query.get_or_404(item_id)
    else:
        return abort(400)
        
    item.is_deleted = False
    db.session.commit()
    flash(f'{model_type.replace("_", " ").title()} restored successfully.', 'success')
    return redirect(url_for('admin.maintenance'))
