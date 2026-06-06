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
from models.activity_report import ActivityReport

dashboard_bp = Blueprint('dashboard', __name__)


@dashboard_bp.route('/')
@login_required
def index():
    """Main dashboard – Scoped activity notices & coordinator/chairperson operations."""
    PrincipalPost.check_and_update_expired()

    # ---- Principal posts ---------------------------------------------------
    # Principal & Chairperson see all posts; others see only APPROVED posts for their dept
    if current_user.role in ('PRINCIPAL', 'CHAIRPERSON'):
        principal_posts = PrincipalPost.query.join(
            ActivityReport, PrincipalPost.id == ActivityReport.post_id, isouter=True
        ).filter(
            PrincipalPost.progress_status != 'EXPIRED',
            db.or_(
                PrincipalPost.progress_status != 'COMPLETED',
                ActivityReport.id == None,
                ActivityReport.status != 'SUBMITTED'
            )
        ).order_by(PrincipalPost.created_at.desc()).all()
    elif current_user.department_id:
        principal_posts = PrincipalPost.query.join(
            ActivityReport, PrincipalPost.id == ActivityReport.post_id, isouter=True
        ).filter(
            PrincipalPost.approval_status == 'APPROVED',
            PrincipalPost.progress_status != 'EXPIRED',
            PrincipalPost.departments.any(id=current_user.department_id),
            db.or_(
                PrincipalPost.progress_status != 'COMPLETED',
                ActivityReport.id == None,
                ActivityReport.status != 'SUBMITTED'
            )
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


@dashboard_bp.route('/privacy')
def privacy():
    """Public Privacy Policy page (compliant with DPDP Act, 2023)."""
    return render_template('legal/privacy_policy.html')


@dashboard_bp.route('/terms')
def terms():
    """Public Terms of Service page."""
    return render_template('legal/terms_of_service.html')
