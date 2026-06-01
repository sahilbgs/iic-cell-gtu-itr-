"""
GTU-ITR R&D & IIC Portal - Scoped Dashboard Routes
Blueprint: dashboard  |  Prefix: (none – root)
"""
from flask import Blueprint, render_template
from flask_login import login_required, current_user
from extensions import db
from models.department import Department
from models.user import User
from models.principal_post import PrincipalPost

dashboard_bp = Blueprint('dashboard', __name__)


@dashboard_bp.route('/')
@login_required
def index():
    """Main dashboard – Scoped activity notices & coordinator/chairperson operations."""

    # ---- Principal posts ---------------------------------------------------
    # Principal & Chairperson see all posts; others see only APPROVED posts for their dept
    if current_user.role in ('PRINCIPAL', 'CHAIRPERSON'):
        principal_posts = PrincipalPost.query.order_by(PrincipalPost.created_at.desc()).all()
    elif current_user.department_id:
        principal_posts = PrincipalPost.query.filter(
            PrincipalPost.approval_status == 'APPROVED',
            PrincipalPost.departments.any(id=current_user.department_id)
        ).order_by(PrincipalPost.created_at.desc()).all()
    else:
        principal_posts = []

    # Departments list for Chairperson allocation dropdown
    departments = []
    if current_user.role == 'CHAIRPERSON':
        departments = Department.query.order_by(Department.name).all()

    # Fetch faculty members of coordinator's department
    dept_faculty = []
    if current_user.role == 'DEPT_COORDINATOR':
        dept_faculty = User.query.filter_by(role='FACULTY', department_id=current_user.department_id).order_by(User.full_name).all()

    return render_template('dashboard.html',
                           principal_posts=principal_posts,
                           departments=departments,
                           dept_faculty=dept_faculty,
                           )
