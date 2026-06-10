"""
GTU-ITR R&D & IIC Portal - Authentication Routes
Blueprint: auth  |  Prefix: /auth
"""
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from extensions import db
from models.user import User, ROLES, ROLE_LABELS
from models.department import Department

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')


# --------------------------------------------------------------------------- #
#  Login
# --------------------------------------------------------------------------- #
@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """User login."""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))

    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        remember = bool(request.form.get('remember'))

        user = User.query.filter_by(email=email).first()

        if user is None or user.is_deleted or not user.check_password(password):
            flash('Invalid email or password.', 'danger')
            return render_template('auth/login.html')

        if not user.is_active:
            flash('Your account has been deactivated. Contact administration.', 'warning')
            return render_template('auth/login.html')

        login_user(user, remember=remember)
        flash(f'Welcome back, {user.full_name}!', 'success')

        # Redirect to next page or dashboard
        next_page = request.args.get('next')
        if next_page and next_page.startswith('/'):
            return redirect(next_page)
        return redirect(url_for('dashboard.index'))

    return render_template('auth/login.html')


# --------------------------------------------------------------------------- #
#  Logout
# --------------------------------------------------------------------------- #
@auth_bp.route('/logout')
@login_required
def logout():
    """Log out the current user."""
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))




# --------------------------------------------------------------------------- #
#  Profile
# --------------------------------------------------------------------------- #
@auth_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    """View and update own profile."""
    if request.method == 'POST':
        current_user.full_name = request.form.get('full_name', current_user.full_name).strip()
        current_user.phone = request.form.get('phone', '').strip() or None
        current_user.designation = request.form.get('designation', '').strip() or None

        # Password change (optional)
        new_password = request.form.get('new_password', '')
        if new_password:
            if len(new_password) < 6:
                flash('New password must be at least 6 characters.', 'danger')
                return render_template('auth/profile.html')
            confirm = request.form.get('confirm_new_password', '')
            if new_password != confirm:
                flash('New passwords do not match.', 'danger')
                return render_template('auth/profile.html')
            current_user.set_password(new_password)
            flash('Password updated.', 'success')

        db.session.commit()
        flash('Profile updated.', 'success')
        return redirect(url_for('auth.profile'))

    return render_template('auth/profile.html')
