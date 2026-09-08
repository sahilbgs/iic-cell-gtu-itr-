"""
GTU-ITR Portal - Analytics & Visitor Intelligence Routes
Provides live visitor tracking, heartbeat ping, session duration calculation, and admin reporting.
"""
from datetime import datetime, timedelta
from flask import Blueprint, render_template, request, jsonify, abort
from flask_login import login_required, current_user
from sqlalchemy import func, desc, distinct
from extensions import db, csrf
from models.analytics import VisitorSession, VisitorLog, AuthAuditLog, format_duration

analytics_bp = Blueprint('analytics', __name__)


# --------------------------------------------------------------------------- #
#  Heartbeat Endpoint (Pings from active client tabs)
# --------------------------------------------------------------------------- #
@analytics_bp.route('/api/analytics/heartbeat', methods=['POST'])
@csrf.exempt
def heartbeat():
    """Client-side heartbeat ping to accurately measure time spent on site."""
    try:
        session_id = request.cookies.get('_gtu_vid')
        data = request.get_json(silent=True) or request.form
        if not session_id and data:
            session_id = data.get('session_id')

        if not session_id:
            return jsonify({'status': 'missing_session'}), 400

        vs = VisitorSession.query.filter_by(session_id=session_id).first()
        now = datetime.utcnow()
        
        if vs:
            delta_seconds = int((now - vs.first_seen).total_seconds()) if vs.first_seen else 0
            vs.duration_seconds = max(vs.duration_seconds or 0, delta_seconds)
            vs.last_seen = now
            vs.is_active = True
            
            if data and data.get('current_path'):
                vs.exit_path = data.get('current_path')[:512]
                
            db.session.commit()
            return jsonify({
                'status': 'ok',
                'duration_seconds': vs.duration_seconds,
                'duration_formatted': format_duration(vs.duration_seconds)
            })
    except Exception as e:
        db.session.rollback()
        return jsonify({'status': 'error', 'message': str(e)}), 500

    return jsonify({'status': 'ignored'}), 200


# --------------------------------------------------------------------------- #
#  Analytics Summary API
# --------------------------------------------------------------------------- #
@analytics_bp.route('/api/analytics/stats')
def analytics_stats():
    """Returns real-time analytics stats for server console & admin dashboards."""
    try:
        now = datetime.utcnow()
        five_mins_ago = now - timedelta(minutes=5)
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

        # Totals
        total_sessions = VisitorSession.query.count()
        total_visitors = db.session.query(func.count(distinct(VisitorSession.ip_address))).scalar() or 0
        today_visitors = db.session.query(func.count(distinct(VisitorSession.ip_address))).filter(VisitorSession.first_seen >= today_start).scalar() or 0
        active_visitors = VisitorSession.query.filter(VisitorSession.last_seen >= five_mins_ago).count()
        total_pageviews = VisitorLog.query.count()

        # Average Time Spent
        avg_seconds = db.session.query(func.avg(VisitorSession.duration_seconds)).filter(VisitorSession.duration_seconds > 0).scalar() or 0
        avg_duration_formatted = format_duration(int(avg_seconds))

        # Device Breakdown
        device_counts = dict(
            db.session.query(VisitorSession.device_type, func.count(VisitorSession.session_id))
            .group_by(VisitorSession.device_type)
            .all()
        )

        # OS Breakdown
        os_counts = dict(
            db.session.query(VisitorSession.os, func.count(VisitorSession.session_id))
            .group_by(VisitorSession.os)
            .order_by(desc(func.count(VisitorSession.session_id)))
            .limit(6)
            .all()
        )

        # Top Visited Pages
        top_pages_query = (
            db.session.query(
                VisitorLog.path,
                func.count(VisitorLog.id).label('views'),
                func.count(distinct(VisitorLog.ip_address)).label('unique_visitors')
            )
            .group_by(VisitorLog.path)
            .order_by(desc('views'))
            .limit(10)
            .all()
        )
        top_pages = [{'path': r[0], 'views': r[1], 'unique_visitors': r[2]} for r in top_pages_query]

        # Recent Visitor Sessions (Kis IP se kis ne site visit kiye, duration, user)
        recent_sessions = [
            vs.to_dict() for vs in
            VisitorSession.query.order_by(desc(VisitorSession.last_seen)).limit(50).all()
        ]

        # Recent Login / Logout Audit Trail (Kub login kiy, kun logout)
        recent_auth_logs = [
            a.to_dict() for a in
            AuthAuditLog.query.order_by(desc(AuthAuditLog.created_at)).limit(50).all()
        ]

        # Recent Detailed Pageviews / Logs
        recent_pageviews = [
            vl.to_dict() for vl in
            VisitorLog.query.order_by(desc(VisitorLog.timestamp)).limit(50).all()
        ]

        return jsonify({
            'total_sessions': total_sessions,
            'total_visitors': total_visitors,
            'today_visitors': today_visitors,
            'active_visitors': active_visitors,
            'total_pageviews': total_pageviews,
            'avg_duration_seconds': int(avg_seconds),
            'avg_duration_formatted': avg_duration_formatted,
            'device_breakdown': device_counts,
            'os_breakdown': os_counts,
            'top_pages': top_pages,
            'recent_sessions': recent_sessions,
            'recent_auth_logs': recent_auth_logs,
            'recent_pageviews': recent_pageviews,
            'server_time': now.strftime('%Y-%m-%d %H:%M:%S UTC')
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# --------------------------------------------------------------------------- #
#  Admin Web View
# --------------------------------------------------------------------------- #
@analytics_bp.route('/admin/analytics')
@login_required
def admin_analytics_view():
    """Portal Admin view for Visitor Analytics and Login/Logout logs."""
    if current_user.role not in ('CHAIRPERSON', 'MASTER_ADMIN', 'PRINCIPAL'):
        abort(403)
    return render_template('admin/analytics.html')
