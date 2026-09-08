"""
GTU-ITR Analytics & Visitor Tracking Utility
Accurately records real visitor IPs, session durations, device info, and user audit events.
"""
import uuid
from datetime import datetime, timezone
from flask import request, session, g
from extensions import db
from models.analytics import VisitorSession, VisitorLog, AuthAuditLog


def get_real_client_ip():
    """Extract true client IP address behind Cloudflare Tunnel or reverse proxy."""
    cf_ip = request.headers.get('CF-Connecting-IP')
    if cf_ip:
        return cf_ip.strip()
    
    x_forwarded = request.headers.get('X-Forwarded-For')
    if x_forwarded:
        return x_forwarded.split(',')[0].strip()
        
    x_real_ip = request.headers.get('X-Real-IP')
    if x_real_ip:
        return x_real_ip.strip()
        
    return request.remote_addr or '127.0.0.1'


def parse_user_agent(ua_string):
    """Parse User-Agent string into (device_type, browser, os)."""
    if not ua_string:
        return 'Unknown', 'Unknown', 'Unknown'
        
    ua = ua_string.lower()
    
    # Device
    if 'mobile' in ua or ('android' in ua and 'mobile' in ua) or 'iphone' in ua:
        device = 'Mobile'
    elif 'ipad' in ua or 'tablet' in ua:
        device = 'Tablet'
    elif any(b in ua for b in ['bot', 'crawler', 'spider', 'curl', 'wget', 'python', 'postman']):
        device = 'Bot/CLI'
    else:
        device = 'Desktop'
        
    # OS
    if 'android' in ua:
        os_name = 'Android'
    elif 'iphone' in ua or 'ipad' in ua or 'ios' in ua:
        os_name = 'iOS'
    elif 'windows' in ua:
        os_name = 'Windows'
    elif 'macintosh' in ua or 'mac os' in ua:
        os_name = 'macOS'
    elif 'linux' in ua:
        os_name = 'Linux'
    else:
        os_name = 'Other'
        
    # Browser
    if 'edg' in ua:
        browser = 'Edge'
    elif 'chrome' in ua or 'crios' in ua:
        browser = 'Chrome'
    elif 'firefox' in ua or 'fxios' in ua:
        browser = 'Firefox'
    elif 'safari' in ua and 'chrome' not in ua:
        browser = 'Safari'
    elif 'curl' in ua:
        browser = 'curl'
    elif 'python' in ua:
        browser = 'Python'
    else:
        browser = 'Browser'
        
    return device, browser, os_name


def should_skip_tracking(path):
    """Determine if a request path should be skipped from database logging (e.g. static files)."""
    if not path:
        return True
    
    # Skip static files, favicon, fonts, uploads, heartbeat pings
    skip_prefixes = (
        '/static/',
        '/favicon.ico',
        '/robots.txt',
        '/api/analytics/heartbeat',
    )
    if path.startswith(skip_prefixes):
        return True
        
    skip_extensions = ('.css', '.js', '.png', '.jpg', '.jpeg', '.gif', '.svg', '.ico', '.woff', '.woff2', '.ttf', '.map')
    if any(path.lower().endswith(ext) for ext in skip_extensions):
        return True
        
    return False


def track_request(response):
    """Called in after_request to record page view and update session."""
    try:
        path = request.path
        if should_skip_tracking(path):
            return response

        # Don't track HEAD or OPTIONS requests from health checks
        if request.method in ('HEAD', 'OPTIONS'):
            return response

        ip = get_real_client_ip()
        ua_str = request.headers.get('User-Agent', '')[:500]
        device, browser, os_name = parse_user_agent(ua_str)
        referrer = request.referrer[:512] if request.referrer else None
        
        # Session ID from cookie or generate new
        session_id = request.cookies.get('_gtu_vid')
        is_new_session = False
        if not session_id:
            session_id = str(uuid.uuid4())
            is_new_session = True
            # Set cookie on response
            response.set_cookie(
                '_gtu_vid',
                session_id,
                max_age=30 * 86400,  # 30 days
                httponly=True,
                samesite='Lax'
            )

        # Current user if authenticated
        from flask_login import current_user
        user_id = None
        user_email = None
        user_name = None
        user_role = None
        
        if current_user and current_user.is_authenticated:
            user_id = current_user.id
            user_email = current_user.email
            user_name = current_user.full_name
            user_role = current_user.role

        now = datetime.utcnow()

        # Update or create VisitorSession
        vs = VisitorSession.query.filter_by(session_id=session_id).first()
        if not vs:
            vs = VisitorSession(
                session_id=session_id,
                ip_address=ip,
                user_id=user_id,
                user_email=user_email,
                user_name=user_name,
                user_role=user_role,
                first_seen=now,
                last_seen=now,
                duration_seconds=0,
                pageviews=1,
                device_type=device,
                browser=browser,
                os=os_name,
                entry_path=path[:512],
                exit_path=path[:512],
                referrer=referrer,
                is_active=True
            )
            db.session.add(vs)
        else:
            # Update existing session
            if user_id and not vs.user_id:
                vs.user_id = user_id
                vs.user_email = user_email
                vs.user_name = user_name
                vs.user_role = user_role
            
            delta_seconds = int((now - vs.first_seen).total_seconds()) if vs.first_seen else 0
            vs.duration_seconds = max(vs.duration_seconds or 0, delta_seconds)
            vs.last_seen = now
            vs.pageviews = (vs.pageviews or 0) + 1
            vs.exit_path = path[:512]
            vs.is_active = True

        # Log specific page visit
        vlog = VisitorLog(
            session_id=session_id,
            ip_address=ip,
            user_id=user_id,
            user_email=user_email,
            user_name=user_name,
            user_role=user_role,
            method=request.method,
            path=path[:512],
            status_code=response.status_code,
            user_agent=ua_str,
            device_type=device,
            browser=browser,
            os=os_name,
            referrer=referrer,
            timestamp=now
        )
        db.session.add(vlog)
        db.session.commit()

    except Exception:
        db.session.rollback()

    return response


def log_auth_event(event_type, status, user=None, email=None, reason=None, session_duration=None):
    """Record an authentication event (LOGIN_SUCCESS, LOGIN_FAILED, LOGOUT)."""
    try:
        ip = get_real_client_ip()
        ua_str = request.headers.get('User-Agent', '')[:500]
        device, browser, os_name = parse_user_agent(ua_str)
        
        user_id = user.id if user else None
        user_email = user.email if user else (email or 'Unknown')
        user_name = user.full_name if user else None
        user_role = user.role if user else None

        audit = AuthAuditLog(
            user_id=user_id,
            user_email=user_email,
            user_name=user_name,
            user_role=user_role,
            event_type=event_type,
            status=status,
            ip_address=ip,
            user_agent=ua_str,
            device_type=device,
            browser=browser,
            os=os_name,
            reason=reason,
            session_duration=session_duration,
            created_at=datetime.utcnow()
        )
        db.session.add(audit)
        db.session.commit()
    except Exception:
        db.session.rollback()
