"""
GTU-ITR R&D & IIC Portal - Scoped Dashboard Routes
Blueprint: dashboard  |  Prefix: (none – root)
"""
from flask import Blueprint, render_template, redirect, url_for, send_from_directory, current_app, request, jsonify
from flask_login import login_required, current_user
from models.landing_post import LandingPost
from extensions import db
from models.department import Department
from models.user import User
from models.principal_post import PrincipalPost
from models.activity_report import ActivityReport

dashboard_bp = Blueprint('dashboard', __name__)


@dashboard_bp.route('/')
def landing():
    """Public landing page."""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))

    PrincipalPost.check_and_update_expired()

    # Fetch landing updates from Chairperson (pinned first, then newest)
    landing_posts = LandingPost.query.filter_by(is_hidden=False, is_deleted=False)\
        .order_by(LandingPost.is_pinned.desc(), LandingPost.created_at.desc()).all()

    # Fetch public activities that are approved and not expired
    public_activities = PrincipalPost.query.filter_by(
        approval_status='APPROVED',
        is_public=True
    ).filter(
        PrincipalPost.progress_status != 'EXPIRED'
    ).order_by(PrincipalPost.created_at.desc()).all()

    return render_template('landing.html', landing_posts=landing_posts, public_activities=public_activities)


@dashboard_bp.route('/announcements')
def announcements():
    """Public announcements page showcasing active registrations and running activities."""
    PrincipalPost.check_and_update_expired()

    # Base query: approved, public, not expired
    query = PrincipalPost.query.filter_by(
        approval_status='APPROVED',
        is_public=True
    ).filter(
        PrincipalPost.progress_status != 'EXPIRED'
    )

    filter_tab = request.args.get('filter', 'all')
    dept_id = request.args.get('department_id', type=int)
    search_query = request.args.get('q', '').strip()

    if filter_tab == 'registrations':
        # Activities with open registration (either internal form or external link)
        query = query.filter(
            db.or_(
                PrincipalPost.has_registration_form == True,
                PrincipalPost.external_registration_url != None
            )
        )
    elif filter_tab == 'running':
        # Activities currently in progress
        query = query.filter(PrincipalPost.progress_status == 'IN_PROGRESS')

    if dept_id:
        query = query.filter(
            db.or_(
                PrincipalPost.department_id == dept_id,
                PrincipalPost.departments.any(id=dept_id)
            )
        )

    if search_query:
        query = query.filter(
            db.or_(
                PrincipalPost.title.ilike(f'%{search_query}%'),
                PrincipalPost.summary.ilike(f'%{search_query}%'),
                PrincipalPost.full_content.ilike(f'%{search_query}%')
            )
        )

    activities = query.order_by(PrincipalPost.created_at.desc()).all()
    departments = Department.query.filter_by(is_deleted=False).order_by(Department.name).all()

    return render_template('announcements.html',
                           activities=activities,
                           departments=departments,
                           current_filter=filter_tab,
                           current_dept=dept_id,
                           search_query=search_query)


@dashboard_bp.route('/media/<filename>')
def serve_media(filename):
    """Serve uploaded media for the landing page."""
    return send_from_directory(current_app.config.get('UPLOAD_FOLDER', 'uploads'), filename)


@dashboard_bp.route('/dashboard')
@login_required
def index():
    """Main dashboard – Scoped activity notices & coordinator/chairperson operations."""
    PrincipalPost.check_and_update_expired()

    # ---- Principal posts ---------------------------------------------------
    # Principal & Chairperson see all posts; others see only APPROVED posts for their dept
    if current_user.role in ('PRINCIPAL', 'CHAIRPERSON', 'MASTER_ADMIN'):
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
    if current_user.role in ('CHAIRPERSON', 'MASTER_ADMIN'):
        departments = Department.query.filter_by(is_deleted=False).order_by(Department.name).all()

    # Fetch faculty members of HOD's department
    dept_faculty = []
    if current_user.role == 'HOD':
        dept_faculty = User.query.filter_by(role='FACULTY', department_id=current_user.department_id, is_deleted=False).order_by(User.full_name).all()

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


@dashboard_bp.route('/attendance')
def sih_attendance():
    """Dedicated Team Attendance Portal for SIH 2026 students."""
    return send_from_directory(current_app.static_folder, 'attendance.html')


@dashboard_bp.route('/attendance-admin')
def sih_attendance_admin():
    """SIH 2026 Attendance Manager & Link Dispatcher Console."""
    return send_from_directory(current_app.static_folder, 'attendance-admin.html')


@dashboard_bp.route('/sih-results')
def sih_results():
    """Smart India Hackathon (SIH 2026) Official Results & Team Rankings with Selfies."""
    return send_from_directory(current_app.static_folder, 'sih-results.html')


@dashboard_bp.route('/results')
def sih_results_alias():
    """Short URL alias for SIH 2026 results."""
    return redirect(url_for('dashboard.sih_results'))


@dashboard_bp.route('/api/sih-results')
def api_sih_results():
    """API endpoint to get the full JSON dataset of SIH 2026 results with live photos."""
    from utils.results_sync import get_live_results_data
    data = get_live_results_data()
    for t in data:
        t.pop('leader_phone', None)
    resp = jsonify(data)
    resp.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    resp.headers['Pragma'] = 'no-cache'
    resp.headers['Expires'] = '0'
    return resp


@dashboard_bp.route('/api/sih-results/sync', methods=['GET', 'POST'])
def api_sih_results_sync():
    """Force synchronization of all attendance photos into results data and page."""
    from utils.results_sync import sync_all_attendance_photos_to_results
    data = sync_all_attendance_photos_to_results()
    return jsonify({
        'success': True,
        'message': 'SIH 2026 results synchronized successfully with all attendance photos',
        'teams_count': len(data),
        'photos_count': sum(1 for t in data if t.get('has_photo'))
    })


@dashboard_bp.route('/api/sih-results/upload-photo', methods=['POST'])
def api_upload_team_photo():
    """Directly uploads or attaches a verified photo to a team in the SIH 2026 results."""
    try:
        from utils.results_sync import sync_single_team_photo
        from models.team_attendance import TeamAttendance
        import base64

        data = request.get_json(silent=True) or {}
        reg_id = data.get('reg_id') or request.form.get('reg_id')
        team_name = data.get('team_name') or request.form.get('team_name')
        photo_b64 = data.get('photo') or data.get('selfie_image')

        # Check multipart file upload
        if 'photo_file' in request.files:
            file = request.files['photo_file']
            if file and file.filename:
                raw_bytes = file.read()
                photo_b64 = 'data:image/jpeg;base64,' + base64.b64encode(raw_bytes).decode('utf-8')

        if not photo_b64:
            return jsonify({'success': False, 'error': 'No image data provided'}), 400

        # Update or create attendance record in DB if exists
        digits = ''.join(c for c in str(reg_id or '') if c.isdigit())
        clean_team_id = int(digits) if digits else None

        att = TeamAttendance.query.filter(
            db.or_(
                TeamAttendance.registration_id == clean_team_id if clean_team_id else False,
                TeamAttendance.team_name.ilike((team_name or '').strip())
            )
        ).first()

        if att:
            att.selfie_image = photo_b64
            db.session.commit()

        # Sync to results files
        ok = sync_single_team_photo(reg_id=reg_id, team_name=team_name, selfie_image=photo_b64)
        if ok:
            return jsonify({'success': True, 'message': f'Photo attached to team {team_name or reg_id}'})
        else:
            return jsonify({'success': False, 'error': 'Failed to match team in results dataset'}), 404

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


