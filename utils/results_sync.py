"""
GTU-ITR IIC & R&D Cell - SIH 2026 Results Photo Synchronizer
Automatically syncs group selfie photos from PostgreSQL team_attendance records
into the static/sih_photos directory, updates static/sih_2026_results_data.json,
and rebuilds static/sih-results.html in real-time.
"""

import os
import json
import base64
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

BASE_DIR = '/home/gtu-itr/iic-cell-gtu-itr-'
STATIC_DIR = os.path.join(BASE_DIR, 'static')
PHOTOS_DIR = os.path.join(STATIC_DIR, 'sih_photos')
RESULTS_JSON_PATH = os.path.join(STATIC_DIR, 'sih_2026_results_data.json')
RESULTS_HTML_PATH = os.path.join(STATIC_DIR, 'sih-results.html')
BUILD_SCRIPT_PATH = os.path.join(STATIC_DIR, 'build_full_results_page.py')


def normalize_key(text):
    """Normalizes string for fuzzy key comparison (lowercase alphanumeric only)."""
    return ''.join(c.lower() for c in str(text or '') if c.isalnum())


def get_photo_filename(reg_id=None, team_name=None):
    """Determines canonical image filename based on reg_id or team_name."""
    if reg_id:
        digits = ''.join(c for c in str(reg_id) if c.isdigit())
        if digits:
            return f"reg_{int(digits)}.jpg"
    slug = normalize_key(team_name)[:30] or 'photo'
    return f"team_{slug}.jpg"


def extract_and_save_photo(selfie_data, filename):
    """
    Decodes Base64 data URI or raw base64 string and writes it as JPEG.
    Returns the web URL path e.g. /static/sih_photos/filename.
    """
    if not selfie_data or len(str(selfie_data).strip()) < 50:
        return None

    str_data = str(selfie_data).strip()

    # If it's already a relative web path pointing to an existing file
    if str_data.startswith('/static/sih_photos/'):
        disk_path = os.path.join(BASE_DIR, str_data.lstrip('/'))
        if os.path.exists(disk_path) and os.path.getsize(disk_path) > 100:
            return str_data

    # Extract base64 payload
    if ',' in str_data:
        _, encoded = str_data.split(',', 1)
    else:
        encoded = str_data

    try:
        binary_bytes = base64.b64decode(encoded)
        if len(binary_bytes) < 50:
            return None

        os.makedirs(PHOTOS_DIR, exist_ok=True)
        file_path = os.path.join(PHOTOS_DIR, filename)

        with open(file_path, 'wb') as f:
            f.write(binary_bytes)

        logger.info(f"Saved team photo: {file_path} ({len(binary_bytes)} bytes)")
        return f"/static/sih_photos/{filename}"
    except Exception as e:
        logger.error(f"Failed to decode base64 photo for {filename}: {e}")
        return None


def match_team(item, reg_id=None, team_name=None):
    """Checks if a results item matches given reg_id or team_name."""
    # 1. Compare numeric reg_id
    if reg_id and item.get('reg_id'):
        d1 = ''.join(c for c in str(reg_id) if c.isdigit())
        d2 = ''.join(c for c in str(item.get('reg_id')) if c.isdigit())
        if d1 and d2 and int(d1) == int(d2):
            return True

    # 2. Compare normalized team name
    if team_name and item.get('team_name'):
        n1 = normalize_key(team_name)
        n2 = normalize_key(item.get('team_name'))
        if n1 == n2:
            return True
        if len(n1) >= 4 and len(n2) >= 4:
            if n1 in n2 or n2 in n1:
                return True

    return False


def rebuild_results_html():
    """Executes the results generator script to update static/sih-results.html."""
    try:
        import subprocess
        python_bin = os.path.join(BASE_DIR, 'venv/bin/python3')
        if not os.path.exists(python_bin):
            python_bin = '/usr/bin/python3'
        cmd = [python_bin, BUILD_SCRIPT_PATH]
        res = subprocess.run(cmd, cwd=BASE_DIR, capture_output=True, text=True, timeout=15)
        if res.returncode == 0:
            logger.info("Successfully rebuilt sih-results.html")
            return True
        else:
            logger.error(f"Rebuild failed: {res.stderr}")
            return False
    except Exception as e:
        logger.error(f"Exception while rebuilding sih-results.html: {e}")
        return False


def sync_single_team_photo(reg_id=None, team_name=None, selfie_image=None):
    """
    Synchronizes a single team photo immediately:
    1. Extracts and writes image to static/sih_photos/
    2. Updates static/sih_2026_results_data.json
    3. Rebuilds static/sih-results.html
    """
    if not selfie_image or len(str(selfie_image).strip()) < 50:
        return False

    filename = get_photo_filename(reg_id, team_name)
    photo_url = extract_and_save_photo(selfie_image, filename)
    if not photo_url:
        return False

    # Update JSON
    try:
        if not os.path.exists(RESULTS_JSON_PATH):
            return False

        with open(RESULTS_JSON_PATH, 'r') as f:
            results = json.load(f)

        matched = False
        for t in results:
            if match_team(t, reg_id, team_name):
                t['photo_url'] = photo_url
                t['has_photo'] = True
                matched = True
                logger.info(f"Updated photo for team: {t.get('team_name')} -> {photo_url}")
                break

        if matched:
            with open(RESULTS_JSON_PATH, 'w') as f:
                json.dump(results, f, indent=2)

            # Rebuild HTML
            rebuild_results_html()
            return True
    except Exception as e:
        logger.error(f"Error in sync_single_team_photo: {e}")

    return False


def sync_all_attendance_photos_to_results():
    """
    Scans all records in PostgreSQL `team_attendance`, checks for photos,
    extracts any missing photos, updates results dataset, and regenerates results HTML.
    Returns the updated results data list.
    """
    attendance_records = []
    try:
        from extensions import db
        from models.team_attendance import TeamAttendance

        attendance_records = TeamAttendance.query.filter(
            TeamAttendance.selfie_image.isnot(None)
        ).all()
    except Exception as e:
        logger.warning(f"Could not query via extensions.db, attempting direct psycopg2: {e}")
        attendance_records = []
        try:
            import psycopg2
            conn = psycopg2.connect('postgresql://gtu_admin:44113290@localhost:5432/iic_cell_gtu')
            cur = conn.cursor()
            cur.execute('SELECT id, registration_id, team_name, selfie_image FROM team_attendance WHERE selfie_image IS NOT NULL AND LENGTH(selfie_image) > 50;')
            rows = cur.fetchall()
            for r in rows:
                class DummyRec: pass
                d = DummyRec()
                d.id, d.registration_id, d.team_name, d.selfie_image = r
                attendance_records.append(d)
            conn.close()
        except Exception as pge:
            logger.error(f"Database direct query failed: {pge}")

    if not os.path.exists(RESULTS_JSON_PATH):
        logger.error(f"Results JSON not found at {RESULTS_JSON_PATH}")
        return []

    with open(RESULTS_JSON_PATH, 'r') as f:
        results = json.load(f)

    changed = False

    # Also build map of existing disk photos
    os.makedirs(PHOTOS_DIR, exist_ok=True)
    existing_files = set(os.listdir(PHOTOS_DIR))

    for rec in attendance_records:
        selfie = getattr(rec, 'selfie_image', None)
        if not selfie or len(str(selfie).strip()) < 50:
            continue

        reg_id = getattr(rec, 'registration_id', None)
        team_name = getattr(rec, 'team_name', '')
        filename = get_photo_filename(reg_id, team_name)

        disk_path = os.path.join(PHOTOS_DIR, filename)
        file_exists = filename in existing_files and os.path.exists(disk_path) and os.path.getsize(disk_path) > 100

        # If file missing or needs writing
        photo_url = None
        if not file_exists:
            photo_url = extract_and_save_photo(selfie, filename)
            if photo_url:
                existing_files.add(filename)
                changed = True
        else:
            photo_url = f"/static/sih_photos/{filename}"

        if photo_url:
            for t in results:
                if match_team(t, reg_id, team_name):
                    if t.get('photo_url') != photo_url or not t.get('has_photo'):
                        t['photo_url'] = photo_url
                        t['has_photo'] = True
                        changed = True
                        logger.info(f"Synced photo for team {t.get('team_name')} ({t.get('reg_id')}) -> {photo_url}")
                    break

    # Also check if any file in static/sih_photos corresponds to a team in results without photo_url
    for t in results:
        if not t.get('photo_url'):
            reg_id = t.get('reg_id')
            digits = ''.join(c for c in str(reg_id) if c.isdigit())
            if digits:
                candidate = f"reg_{int(digits)}.jpg"
                if candidate in existing_files:
                    t['photo_url'] = f"/static/sih_photos/{candidate}"
                    t['has_photo'] = True
                    changed = True

    if changed:
        with open(RESULTS_JSON_PATH, 'w') as f:
            json.dump(results, f, indent=2)
        rebuild_results_html()
        logger.info(f"Results JSON and HTML synchronized with {len(attendance_records)} attendance records.")

    return results


def get_live_results_data():
    """
    Returns the freshest SIH 2026 results data, triggering a sync if any discrepancy
    between PostgreSQL attendance records and JSON is detected.
    """
    try:
        from models.team_attendance import TeamAttendance
        db_count = TeamAttendance.query.filter(
            TeamAttendance.selfie_image.isnot(None),
            TeamAttendance.selfie_image != ''
        ).count()
    except Exception:
        db_count = None

    if os.path.exists(RESULTS_JSON_PATH):
        with open(RESULTS_JSON_PATH, 'r') as f:
            results = json.load(f)
        json_photo_count = sum(1 for t in results if t.get('has_photo') or t.get('photo_url'))
    else:
        results = []
        json_photo_count = 0

    # If DB has more photos than JSON, trigger a full sync
    if db_count is not None and db_count > json_photo_count:
        return sync_all_attendance_photos_to_results()

    return results

