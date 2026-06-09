"""
GTU-ITR R&D & IIC Portal - Access Control Decorators
"""
from functools import wraps
from flask import abort, flash, redirect, url_for
from flask_login import current_user


def role_required(*roles):
    """
    Decorator to restrict route access to specific user roles.

    Usage:
        @role_required('PRINCIPAL', 'CHAIRPERSON', 'RD_COORDINATOR')
        def admin_dashboard():
            ...
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                flash('Please log in to access this page.', 'warning')
                return redirect(url_for('auth.login'))
            if current_user.role not in roles:
                abort(403)
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def principal_required(f):
    """Restrict to Principal only."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'PRINCIPAL':
            abort(403)
        return f(*args, **kwargs)
    return decorated_function


def management_required(f):
    """Restrict to Principal, Chairperson, and R&D Coordinator."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login'))
        if current_user.role not in ('PRINCIPAL', 'CHAIRPERSON', 'RD_COORDINATOR'):
            abort(403)
        return f(*args, **kwargs)
    return decorated_function


def dept_or_above_required(f):
    """Restrict to HOD and above (excludes Faculty and Student Rep)."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login'))
        if current_user.role in ('STUDENT_REP',):
            abort(403)
        return f(*args, **kwargs)
    return decorated_function


def can_access_department(department_id):
    """
    Check if the current user can access data from a specific department.
    - PRINCIPAL, CHAIRPERSON, RD_COORDINATOR: access all departments
    - HOD, FACULTY: only their own department
    - STUDENT_REP: only their own department (view only)
    """
    if current_user.role in ('PRINCIPAL', 'CHAIRPERSON', 'RD_COORDINATOR'):
        return True
    return current_user.department_id == department_id
