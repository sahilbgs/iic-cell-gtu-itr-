"""
GTU-ITR R&D & IIC Portal - Admin Panel Routes
Blueprint: admin  |  Prefix: /admin
Only accessible by CHAIRPERSON role.
"""
from functools import wraps
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, abort
from flask_login import login_required, current_user
from extensions import db
from models.user import User, ROLES, ROLE_LABELS
from models.department import Department

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
    
    users = User.query.order_by(User.created_at.desc()).all()
    departments = Department.query.order_by(Department.name).all()
    
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
    """Delete a user permanently."""
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        flash('You cannot delete your own account.', 'warning')
        return redirect(url_for('admin.index'))
    name = user.full_name
    db.session.delete(user)
    db.session.commit()
    flash(f'User "{name}" deleted permanently.', 'success')
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
    if Department.query.filter_by(code=code).first():
        errors.append(f'Department with code "{code}" already exists.')
    if Department.query.filter_by(name=name).first():
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
    """Delete a department (only if no users are linked)."""
    dept = Department.query.get_or_404(dept_id)
    user_count = User.query.filter_by(department_id=dept.id).count()
    if user_count > 0:
        flash(f'Cannot delete "{dept.name}" — {user_count} user(s) are assigned to it. Reassign them first.', 'danger')
        return redirect(url_for('admin.index'))
    name = dept.name
    db.session.delete(dept)
    db.session.commit()
    flash(f'Department "{name}" deleted successfully.', 'success')
    return redirect(url_for('admin.index'))


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
