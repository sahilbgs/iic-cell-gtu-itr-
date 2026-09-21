"""
GTU-ITR Portal — Firebase to PostgreSQL Synchronization Engine
Auto-syncs student registrations & activity deadline settings between Cloud Firebase and PostgreSQL.
"""
import os
import json
import time
import logging
import threading
import urllib.request
from datetime import datetime

logger = logging.getLogger('firebase_sync')

FIREBASE_PROJECT_ID = os.getenv("FIREBASE_PROJECT_ID", "iic-student-form-clone")
FIREBASE_API_KEY = os.getenv("FIREBASE_API_KEY", "AIzaSyBRAEuMlSKddLiYBK6ShTj4jlLFynxpEN0")


def to_firestore_value(v):
    """Converts a Python primitive/dict to Firestore REST API typed format."""
    if v is None:
        return {"nullValue": None}
    elif isinstance(v, bool):
        return {"booleanValue": v}
    elif isinstance(v, int):
        return {"integerValue": str(v)}
    elif isinstance(v, float):
        return {"doubleValue": v}
    elif isinstance(v, str):
        return {"stringValue": v}
    elif isinstance(v, list):
        return {"arrayValue": {"values": [to_firestore_value(x) for x in v]}}
    elif isinstance(v, dict):
        return {"mapValue": {"fields": {k: to_firestore_value(val) for k, val in v.items()}}}
    return {"stringValue": str(v)}


def from_firestore_value(v):
    """Converts a Firestore REST API typed value object to standard Python primitive."""
    if not isinstance(v, dict):
        return v
    if "stringValue" in v:
        return v["stringValue"]
    if "integerValue" in v:
        return int(v["integerValue"])
    if "doubleValue" in v:
        return float(v["doubleValue"])
    if "booleanValue" in v:
        return v["booleanValue"]
    if "nullValue" in v:
        return None
    if "arrayValue" in v:
        return [from_firestore_value(x) for x in v["arrayValue"].get("values", [])]
    if "mapValue" in v:
        return {k: from_firestore_value(val) for k, val in v["mapValue"].get("fields", {}).items()}
    return v


def sync_post_settings_to_firebase(post):
    """
    Syncs the latest activity title, deadline, and registration status to Cloud Firebase.
    Allows Netlify clone forms to dynamically update deadline & countdown in real-time.
    """
    def _do():
        deadline_iso = post.registration_deadline.strftime("%Y-%m-%dT%H:%M:%S") if post.registration_deadline else ""
        deadline_fmt = post.registration_deadline.strftime("%b %d, %Y at %I:%M %p") if post.registration_deadline else ""

        payload = {
            "post_id": post.id,
            "title": post.title,
            "registration_deadline": deadline_iso,
            "registration_deadline_formatted": deadline_fmt,
            "is_closed": getattr(post, 'is_registration_closed', False),
            "updated_at": datetime.utcnow().isoformat()
        }

        url = f"https://firestore.googleapis.com/v1/projects/{FIREBASE_PROJECT_ID}/databases/(default)/documents/activity_settings/post_{post.id}?key={FIREBASE_API_KEY}"
        body = json.dumps({"fields": {k: to_firestore_value(v) for k, v in payload.items()}}).encode("utf-8")
        req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"}, method="PATCH")

        try:
            with urllib.request.urlopen(req, timeout=5) as resp:
                print(f"[Firebase Settings] Successfully synced deadline for Post {post.id} to Cloud ({deadline_fmt or 'No deadline'})")
        except Exception as e:
            logger.warning(f"[Firebase Settings] Could not sync post settings: {e}")

    threading.Thread(target=_do, daemon=True).start()


def backup_single_registration_to_firebase(reg, post, answers=None):
    """
    Immediately backs up a single registration to Cloud Firebase in a background thread.
    Zero latency impact on user request.
    """
    def _do_backup():
        if answers is None:
            cdata = {}
            if reg.custom_data:
                try:
                    cdata = json.loads(reg.custom_data) if isinstance(reg.custom_data, str) else reg.custom_data
                except Exception:
                    cdata = {}
        else:
            cdata = answers

        leader = cdata.get("field_1788437462474_22") or reg.student_name
        category = cdata.get("field_1788437127088_17") or "-"
        psid = str(cdata.get("field_1788437197832_18") or "-")
        ps_title = cdata.get("field_1788437260250_19") or "-"
        theme = cdata.get("field_1788437366313_21") or "-"

        doc_data = {
            "reg_id": f"REG-LOCAL-{reg.id:04d}",
            "post_id": post.id,
            "post_title": post.title,
            "team_name": reg.student_name,
            "student_name": reg.student_name,
            "enrollment_no": reg.enrollment_no,
            "email": reg.email,
            "phone": reg.phone or "",
            "semester": reg.semester or "",
            "department": reg.department or "",
            "leader_name": leader,
            "problem_category": category,
            "psid": psid,
            "ps_title": ps_title,
            "theme": theme,
            "submitted_at": reg.registered_at.isoformat() if reg.registered_at else datetime.utcnow().isoformat(),
            "source": "Main Server Real-Time",
            "answers": cdata
        }

        doc_id = f"server_reg_{reg.id}"
        url = f"https://firestore.googleapis.com/v1/projects/{FIREBASE_PROJECT_ID}/databases/(default)/documents/registrations/{doc_id}?key={FIREBASE_API_KEY}"
        body = json.dumps({"fields": {k: to_firestore_value(v) for k, v in doc_data.items()}}).encode("utf-8")
        req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"}, method="PATCH")

        try:
            with urllib.request.urlopen(req, timeout=5) as resp:
                print(f"[Firebase Backup] Real-time backup saved to Firestore for {reg.student_name} (ID: {doc_id})")
        except Exception as e:
            logger.warning(f"[Firebase Backup] Could not backup registration {reg.id}: {e}")

    threading.Thread(target=_do_backup, daemon=True).start()


def fetch_firebase_registrations():
    """Fetches all registration documents from Cloud Firebase Firestore REST API."""
    url = f"https://firestore.googleapis.com/v1/projects/{FIREBASE_PROJECT_ID}/databases/(default)/documents/registrations?key={FIREBASE_API_KEY}&pageSize=500"
    req = urllib.request.Request(url, headers={"User-Agent": "GTU-ITR-SyncService/1.0"}, method="GET")

    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            docs = data.get("documents", [])
            parsed_records = []
            for doc in docs:
                raw_fields = doc.get("fields", {})
                fields = {k: from_firestore_value(v) for k, v in raw_fields.items()}
                parsed_records.append(fields)
            return parsed_records
    except Exception as e:
        logger.warning(f"[Firebase Sync] Could not reach Firebase API: {e}")
        return []


def sync_firebase_to_database(app=None):
    """
    Syncs any new student registrations stored in Firebase to the local PostgreSQL database,
    and also ensures activity settings (deadline) are updated in Firebase.
    Returns (synced_count, total_count).
    """
    from extensions import db
    from models.student_registration import StudentRegistration
    from models.principal_post import PrincipalPost

    def _do_sync():
        # 1. Sync active post deadlines to Firebase
        try:
            posts = PrincipalPost.query.filter_by(has_registration_form=True, approval_status='APPROVED').all()
            for p in posts:
                sync_post_settings_to_firebase(p)
        except Exception as err:
            logger.debug(f"[Firebase Sync] Error syncing post settings: {err}")

        # 2. Sync student registrations from Firebase to PostgreSQL
        records = fetch_firebase_registrations()
        if not records:
            return 0, 0

        synced_count = 0
        for rec in records:
            post_id = rec.get("post_id", 2)
            team_name = (rec.get("team_name") or rec.get("student_name") or "").strip()
            if not team_name:
                continue

            answers = rec.get("answers", {})
            if isinstance(answers, str):
                try:
                    answers = json.loads(answers)
                except Exception:
                    answers = {}

            # Normalize answers keys if they have 'field_field_' or 'field_' prefixes
            norm_answers = {}
            for k, v in answers.items():
                norm_answers[k] = v
                if k.startswith("field_field_"):
                    norm_answers[k[6:]] = v
                elif k in ('field_student_name', 'field_semester', 'field_department', 'field_enrollment_no'):
                    norm_answers[k[6:]] = v

            enrollment_no = str(rec.get("enrollment_no") or norm_answers.get("field_1788437569088_25") or norm_answers.get("enrollment_no") or "").strip()
            email = str(rec.get("email") or norm_answers.get("field_1788437675426_28") or norm_answers.get("email") or "").strip()
            phone = str(rec.get("phone") or norm_answers.get("field_1788437682339_29") or norm_answers.get("phone") or "").strip()
            semester = str(rec.get("semester") or norm_answers.get("semester") or "").strip()
            department = str(rec.get("department") or norm_answers.get("field_1788437598077_26") or norm_answers.get("department") or "IIC").strip()

            query = StudentRegistration.query.filter_by(post_id=post_id)
            if enrollment_no and enrollment_no != "N/A":
                existing = query.filter((StudentRegistration.student_name == team_name) | (StudentRegistration.enrollment_no == enrollment_no)).first()
            else:
                existing = query.filter(StudentRegistration.student_name == team_name).first()

            if existing:
                continue

            sub_at = datetime.utcnow()
            raw_sub = rec.get("submitted_at")
            if raw_sub:
                try:
                    clean_iso = raw_sub.replace("Z", "+00:00")
                    sub_at = datetime.fromisoformat(clean_iso).replace(tzinfo=None)
                except Exception:
                    sub_at = datetime.utcnow()

            new_reg = StudentRegistration(
                post_id=post_id,
                student_name=team_name,
                enrollment_no=enrollment_no or "N/A",
                email=email or "N/A",
                phone=phone or None,
                semester=semester or None,
                department=department or None,
                custom_data=json.dumps(norm_answers) if norm_answers else None,
                registered_at=sub_at
            )
            db.session.add(new_reg)
            synced_count += 1
            print(f"[Firebase Sync] Synced new team into PostgreSQL: {team_name} (Enrollment: {enrollment_no})")

        if synced_count > 0:
            db.session.commit()
            print(f"[Firebase Sync] Successfully committed {synced_count} new registrations to PostgreSQL!")

        return synced_count, len(records)

    if app:
        with app.app_context():
            return _do_sync()
    else:
        return _do_sync()


def start_firebase_sync_scheduler(app):
    """
    Launches a daemon thread that runs an initial sync immediately on server boot,
    and then repeats every 5 minutes in the background.
    """
    def _worker():
        time.sleep(3)
        print("[Firebase Sync] Server started! Running initial sync from Cloud Firebase...")
        try:
            with app.app_context():
                synced, total = sync_firebase_to_database()
                print(f"[Firebase Sync] Initial boot sync complete: {synced} new records imported (Total in cloud: {total}).")
        except Exception as e:
            print(f"[Firebase Sync] Initial boot sync exception: {e}")

        while True:
            time.sleep(300)
            try:
                with app.app_context():
                    synced, _ = sync_firebase_to_database()
                    if synced > 0:
                        print(f"[Firebase Sync] Periodic sync: {synced} new registrations imported from Cloud Firebase.")
            except Exception as e:
                logger.debug(f"[Firebase Sync] Periodic loop note: {e}")

    thread = threading.Thread(target=_worker, daemon=True, name="FirebaseSyncWorker")
    thread.start()
    return thread
