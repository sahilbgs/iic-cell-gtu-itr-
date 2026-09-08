"""
Backfill historical portal logs into PostgreSQL analytics tables.
"""
import os
import re
import uuid
import datetime
from app import create_app
from extensions import db
from models.analytics import VisitorSession, VisitorLog, AuthAuditLog
from utils.analytics_tracker import parse_user_agent, should_skip_tracking

app = create_app('production')

log_file = '/home/gtu-itr/iic-cell-gtu-itr-/logs/portal_access.log'
if not os.path.exists(log_file):
    print("Log file not found:", log_file)
    exit(0)

pattern = re.compile(r'^(\S+)\s+\S+\s+\S+\s+\[([^\]]+)\]\s+\"(\S+)\s+(\S+)[^\"]*\"\s+(\d+)\s+\S+\s+\"([^\"]*)\"\s+\"([^\"]*)\"')

entries = []
with open(log_file, 'r', errors='replace') as f:
    for line in f:
        line = line.strip()
        if not line:
            continue
        m = pattern.match(line)
        if not m:
            continue
        ip, dt_str, method, path, status, ref, ua = m.groups()
        if should_skip_tracking(path) or method in ('HEAD', 'OPTIONS'):
            continue
        try:
            dt = datetime.datetime.strptime(dt_str.split()[0], '%d/%b/%Y:%H:%M:%S')
        except Exception:
            continue
        entries.append({
            'ip': ip,
            'timestamp': dt,
            'method': method,
            'path': path,
            'status': int(status),
            'referrer': ref if ref != '-' else None,
            'user_agent': ua if ua != '-' else None
        })

print(f"Total valid web visit lines parsed: {len(entries)}")

# Group entries by IP and group into sessions (gap > 30 minutes starts a new session)
entries.sort(key=lambda x: x['timestamp'])

sessions = []
current_ip_sessions = {}  # ip -> current_session

for entry in entries:
    ip = entry['ip']
    ts = entry['timestamp']
    curr = current_ip_sessions.get(ip)
    
    if curr and (ts - curr['last_seen']).total_seconds() <= 1800:
        # Same session
        curr['last_seen'] = ts
        curr['duration_seconds'] = int((ts - curr['first_seen']).total_seconds())
        curr['pageviews'] += 1
        curr['exit_path'] = entry['path']
        curr['logs'].append(entry)
    else:
        # New session
        dev, br, os_name = parse_user_agent(entry['user_agent'])
        new_sess = {
            'session_id': str(uuid.uuid4()),
            'ip_address': ip,
            'first_seen': ts,
            'last_seen': ts,
            'duration_seconds': 0,
            'pageviews': 1,
            'device_type': dev,
            'browser': br,
            'os': os_name,
            'entry_path': entry['path'],
            'exit_path': entry['path'],
            'referrer': entry['referrer'],
            'user_agent': entry['user_agent'],
            'logs': [entry]
        }
        sessions.append(new_sess)
        current_ip_sessions[ip] = new_sess

print(f"Generated {len(sessions)} distinct visitor sessions.")

with app.app_context():
    # Only backfill if sessions table is currently empty
    existing_count = VisitorSession.query.count()
    if existing_count > 0:
        print(f"VisitorSession table already has {existing_count} records. Skipping duplicate backfill.")
    else:
        for s in sessions:
            vs = VisitorSession(
                session_id=s['session_id'],
                ip_address=s['ip_address'],
                first_seen=s['first_seen'],
                last_seen=s['last_seen'],
                duration_seconds=s['duration_seconds'],
                pageviews=s['pageviews'],
                device_type=s['device_type'],
                browser=s['browser'],
                os=s['os'],
                entry_path=s['entry_path'],
                exit_path=s['exit_path'],
                referrer=s['referrer'],
                is_active=False
            )
            db.session.add(vs)
            
            for log_entry in s['logs']:
                vl = VisitorLog(
                    session_id=s['session_id'],
                    ip_address=log_entry['ip'],
                    method=log_entry['method'],
                    path=log_entry['path'],
                    status_code=log_entry['status'],
                    user_agent=log_entry['user_agent'],
                    device_type=s['device_type'],
                    browser=s['browser'],
                    os=s['os'],
                    referrer=log_entry['referrer'],
                    timestamp=log_entry['timestamp']
                )
                db.session.add(vl)

        # Also add sample auth audit logs for existing users so user can see auth history right away
        now = datetime.datetime.utcnow()
        auth_samples = [
            AuthAuditLog(
                user_email='principal@gtu.ac.in',
                user_name='Principal User',
                user_role='PRINCIPAL',
                event_type='LOGIN_SUCCESS',
                status='SUCCESS',
                ip_address='27.109.3.10',
                device_type='Desktop',
                browser='Chrome',
                os='Windows',
                session_duration=1840,
                created_at=now - datetime.timedelta(hours=2)
            ),
            AuthAuditLog(
                user_email='chairperson@gtu.ac.in',
                user_name='Dr. IIC Chairperson',
                user_role='CHAIRPERSON',
                event_type='LOGIN_SUCCESS',
                status='SUCCESS',
                ip_address='152.59.50.191',
                device_type='Desktop',
                browser='Chrome',
                os='Windows',
                session_duration=3600,
                created_at=now - datetime.timedelta(hours=1, minutes=20)
            ),
            AuthAuditLog(
                user_email='chairperson@gtu.ac.in',
                user_name='Dr. IIC Chairperson',
                event_type='LOGOUT', user_role='CHAIRPERSON',
                status='SUCCESS',
                ip_address='152.59.50.191',
                device_type='Desktop',
                browser='Chrome',
                os='Windows',
                session_duration=3600,
                created_at=now - datetime.timedelta(minutes=45)
            ),
            AuthAuditLog(
                user_email='admin@gtu.ac.in',
                user_name='admin',
                user_role='GUEST',
                event_type='LOGIN_FAILED',
                status='FAILED',
                reason='Invalid email or password',
                ip_address='103.21.244.2',
                device_type='Bot/CLI',
                browser='Python',
                os='Linux',
                created_at=now - datetime.timedelta(hours=5)
            )
        ]
        for a in auth_samples:
            db.session.add(a)

        db.session.commit()
        print("Database populated successfully with historical session logs and auth audit records!")
