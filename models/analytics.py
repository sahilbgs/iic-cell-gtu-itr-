"""
GTU-ITR Portal - Analytics & Audit Log Models
Tracks visitor traffic, IP addresses, session duration, and authentication audit trail.
"""
from datetime import datetime
from extensions import db


class AuthAuditLog(db.Model):
    """Logs every login attempt, successful login, logout, and session event."""
    __tablename__ = 'auth_audit_logs'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    user_email = db.Column(db.String(120), nullable=True, index=True)
    user_name = db.Column(db.String(120), nullable=True)
    user_role = db.Column(db.String(40), nullable=True)
    event_type = db.Column(db.String(30), nullable=False, index=True)  # LOGIN_SUCCESS, LOGIN_FAILED, LOGOUT
    status = db.Column(db.String(20), nullable=False, default='SUCCESS')  # SUCCESS, FAILED
    ip_address = db.Column(db.String(64), nullable=False, index=True)
    user_agent = db.Column(db.String(500), nullable=True)
    device_type = db.Column(db.String(30), nullable=True)
    browser = db.Column(db.String(50), nullable=True)
    os = db.Column(db.String(50), nullable=True)
    reason = db.Column(db.String(255), nullable=True)
    session_duration = db.Column(db.Integer, nullable=True)  # Duration in seconds (on logout)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'user_email': self.user_email or 'Anonymous',
            'user_name': self.user_name or (self.user_email or 'Guest'),
            'user_role': self.user_role or 'GUEST',
            'event_type': self.event_type,
            'status': self.status,
            'ip_address': self.ip_address,
            'device_type': self.device_type,
            'browser': self.browser,
            'os': self.os,
            'reason': self.reason,
            'session_duration': self.session_duration,
            'session_duration_formatted': format_duration(self.session_duration or 0) if self.session_duration else None,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None
        }


class VisitorSession(db.Model):
    """Tracks unique visitor sessions, time spent, and total pages viewed."""
    __tablename__ = 'visitor_sessions'

    session_id = db.Column(db.String(64), primary_key=True)
    ip_address = db.Column(db.String(64), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    user_email = db.Column(db.String(120), nullable=True, index=True)
    user_name = db.Column(db.String(120), nullable=True)
    user_role = db.Column(db.String(40), nullable=True)
    first_seen = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    last_seen = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    duration_seconds = db.Column(db.Integer, default=0)
    pageviews = db.Column(db.Integer, default=1)
    device_type = db.Column(db.String(30), nullable=True)
    browser = db.Column(db.String(50), nullable=True)
    os = db.Column(db.String(50), nullable=True)
    entry_path = db.Column(db.String(512), nullable=True)
    exit_path = db.Column(db.String(512), nullable=True)
    referrer = db.Column(db.String(512), nullable=True)
    is_active = db.Column(db.Boolean, default=True)

    def to_dict(self):
        return {
            'session_id': self.session_id,
            'ip_address': self.ip_address,
            'user_id': self.user_id,
            'user_email': self.user_email or 'Guest / Public Visitor',
            'user_name': self.user_name or 'Anonymous Visitor',
            'user_role': self.user_role or 'VISITOR',
            'first_seen': self.first_seen.strftime('%Y-%m-%d %H:%M:%S') if self.first_seen else None,
            'last_seen': self.last_seen.strftime('%Y-%m-%d %H:%M:%S') if self.last_seen else None,
            'duration_seconds': self.duration_seconds or 0,
            'duration_formatted': format_duration(self.duration_seconds or 0),
            'pageviews': self.pageviews or 1,
            'device_type': self.device_type or 'Desktop',
            'browser': self.browser or 'Unknown',
            'os': self.os or 'Unknown',
            'entry_path': self.entry_path or '/',
            'exit_path': self.exit_path or '/',
            'referrer': self.referrer or 'Direct',
            'is_active': bool(self.is_active)
        }


class VisitorLog(db.Model):
    """Logs individual page views and visits with client IP, path, status, and device."""
    __tablename__ = 'visitor_logs'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    session_id = db.Column(db.String(64), nullable=True, index=True)
    ip_address = db.Column(db.String(64), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    user_email = db.Column(db.String(120), nullable=True, index=True)
    user_name = db.Column(db.String(120), nullable=True)
    user_role = db.Column(db.String(40), nullable=True)
    method = db.Column(db.String(10), nullable=False, default='GET')
    path = db.Column(db.String(512), nullable=False, index=True)
    status_code = db.Column(db.Integer, nullable=False, default=200)
    response_time_ms = db.Column(db.Integer, nullable=True)
    user_agent = db.Column(db.String(500), nullable=True)
    device_type = db.Column(db.String(30), nullable=True)
    browser = db.Column(db.String(50), nullable=True)
    os = db.Column(db.String(50), nullable=True)
    referrer = db.Column(db.String(512), nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    def to_dict(self):
        return {
            'id': self.id,
            'session_id': self.session_id,
            'ip_address': self.ip_address,
            'user_id': self.user_id,
            'user_email': self.user_email or 'Guest',
            'user_name': self.user_name or 'Visitor',
            'user_role': self.user_role or 'VISITOR',
            'method': self.method,
            'path': self.path,
            'status_code': self.status_code,
            'response_time_ms': self.response_time_ms,
            'device_type': self.device_type or 'Desktop',
            'browser': self.browser or 'Unknown',
            'os': self.os or 'Unknown',
            'referrer': self.referrer or 'Direct',
            'timestamp': self.timestamp.strftime('%Y-%m-%d %H:%M:%S') if self.timestamp else None
        }


def format_duration(seconds):
    """Format seconds into human-readable string (e.g., '3m 24s', '45s', '1h 12m')."""
    if not seconds or seconds < 1:
        return '< 1s'
    seconds = int(seconds)
    if seconds < 60:
        return f"{seconds}s"
    minutes = seconds // 60
    remaining_secs = seconds % 60
    if minutes < 60:
        if remaining_secs > 0:
            return f"{minutes}m {remaining_secs}s"
        return f"{minutes}m"
    hours = minutes // 60
    remaining_mins = minutes % 60
    return f"{hours}h {remaining_mins}m"
