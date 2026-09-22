"""
GTU-ITR R&D & IIC Portal - Registration Reports & Exports (CSV / Excel / Firebase)
"""
import io
import csv
import json
from datetime import datetime
from flask import render_template, redirect, url_for, flash, request, abort, Response
from flask_login import login_required, current_user
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

from models.principal_post import PrincipalPost
from models.student_registration import StudentRegistration
from . import posts_bp


@posts_bp.route('/<int:post_id>/registrations/report')
@login_required
def registration_report(post_id):
    """Detailed registrations and statistical reports, visible to Lead Faculty, Coordinator, and Higher Authorities."""
    post = PrincipalPost.query.get_or_404(post_id)

    # Authorization checks
    is_mgmt = current_user.is_management
    is_coord = current_user.role == 'HOD' and current_user.department_id in [d.id for d in post.departments]
    is_assigned = current_user.id == post.assigned_faculty_id

    if not (is_mgmt or is_coord or is_assigned):
        abort(403)

    # Parse form config to get field headers
    fields = []
    custom_field_map = {}
    if post.form_config:
        try:
            fields = json.loads(post.form_config)
            custom_field_map = {f['id']: f['label'] for f in fields}
        except Exception:
            pass

    # Fetch registrations
    registrations = StudentRegistration.query.filter_by(post_id=post.id).order_by(StudentRegistration.registered_at.desc()).all()

    # Helper to parse custom responses in template
    def get_custom_val(reg_obj, field_id):
        answers = {}
        if reg_obj.custom_data:
            try:
                answers = json.loads(reg_obj.custom_data) if isinstance(reg_obj.custom_data, str) else reg_obj.custom_data
            except Exception:
                answers = {}
        val = answers.get(field_id)
        if val is None or val == '':
            val = answers.get(f"field_{field_id}")
        if (val is None or val == '') and field_id in ('student_name', 'enrollment_no', 'department', 'semester', 'email', 'phone'):
            val = getattr(reg_obj, field_id, '')
        return str(val) if val is not None else ""

    # Helper to get full answers dict
    def get_all_answers(reg_obj):
        if not reg_obj.custom_data:
            return {}
        try:
            return json.loads(reg_obj.custom_data) if isinstance(reg_obj.custom_data, str) else reg_obj.custom_data
        except Exception:
            return {}

    # Calculations / Stats
    total_regs = len(registrations)
    semester_stats = {}
    for reg in registrations:
        sem = reg.semester or "Not Specified"
        semester_stats[sem] = semester_stats.get(sem, 0) + 1

    return render_template('posts/registration_report.html',
                           post=post,
                           registrations=registrations,
                           fields=fields,
                           custom_field_map=custom_field_map,
                           total_regs=total_regs,
                           semester_stats=semester_stats,
                           get_custom_val=get_custom_val,
                           get_all_answers=get_all_answers)


@posts_bp.route('/<int:post_id>/registrations/sync-firebase', methods=['POST'])
@login_required
def sync_firebase_manual(post_id):
    """Manually triggers two-way sync from Cloud Firebase to local database."""
    post = PrincipalPost.query.get_or_404(post_id)
    is_mgmt = current_user.is_management
    is_coord = current_user.role == 'HOD' and current_user.department_id in [d.id for d in post.departments]
    is_assigned = current_user.id == post.assigned_faculty_id
    if not (is_mgmt or is_coord or is_assigned):
        abort(403)

    from utils.firebase_sync import sync_firebase_to_database
    synced, total = sync_firebase_to_database()
    if synced > 0:
        flash(f"Firebase Sync Complete: {synced} new registrations imported into database (Total in Cloud: {total}).", "success")
    else:
        flash(f"Database is already up to date! All {total} registrations from Firebase are present.", "info")

    return redirect(url_for('posts.registration_report', post_id=post_id))


@posts_bp.route('/<int:post_id>/registrations/export-csv')
@login_required
def export_registrations_csv(post_id):
    """Export all student registrations as a downloadable UTF-8 CSV/Excel spreadsheet."""
    post = PrincipalPost.query.get_or_404(post_id)

    is_mgmt = current_user.is_management
    is_coord = current_user.role == 'HOD' and current_user.department_id in [d.id for d in post.departments]
    is_assigned = current_user.id == post.assigned_faculty_id
    if not (is_mgmt or is_coord or is_assigned):
        abort(403)

    fields = []
    if post.form_config:
        try:
            fields = json.loads(post.form_config)
        except Exception:
            pass

    registrations = StudentRegistration.query.filter_by(post_id=post.id).order_by(StudentRegistration.registered_at.asc()).all()

    output = io.StringIO()
    output.write('\ufeff')  # UTF-8 BOM for Excel
    writer = csv.writer(output)

    host_url = request.host_url.rstrip('/')

    if fields:
        headers = ['#']
        for f in fields:
            headers.append((f.get('label') or f.get('id') or '').strip())
        headers.append('Registered At')
        writer.writerow(headers)

        for idx, reg in enumerate(registrations, start=1):
            answers = {}
            if reg.custom_data:
                try:
                    answers = json.loads(reg.custom_data) if isinstance(reg.custom_data, str) else reg.custom_data
                except Exception:
                    answers = {}

            row = [idx]
            for f in fields:
                fid = f.get('id')
                ftype = f.get('type')
                val = answers.get(fid)
                if val is None or val == '':
                    val = answers.get(f"field_{fid}")
                if (val is None or val == '') and fid in ('student_name', 'enrollment_no', 'department', 'semester', 'email', 'phone'):
                    val = getattr(reg, fid, '')
                if val is None:
                    val = ''

                if ftype == 'file' and val:
                    val = f"{host_url}/posts/uploads/{val}"
                row.append(str(val))
            row.append(reg.registered_at.strftime('%Y-%m-%d %H:%M:%S'))
            writer.writerow(row)
    else:
        headers = ['#', 'Student Name', 'Enrollment Number', 'Department', 'Semester', 'Email', 'Phone', 'Registered At']
        writer.writerow(headers)

        for idx, reg in enumerate(registrations, start=1):
            row = [
                idx,
                reg.student_name,
                reg.enrollment_no,
                reg.department or '',
                reg.semester or '',
                reg.email or '',
                reg.phone or '',
                reg.registered_at.strftime('%Y-%m-%d %H:%M:%S')
            ]
            writer.writerow(row)

    safe_title = "".join(c for c in post.title[:35] if c.isalnum() or c in (' ', '_', '-')).strip().replace(' ', '_')
    filename = f"registrations_{safe_title}_{post.id}.csv"

    return Response(
        output.getvalue(),
        mimetype='text/csv; charset=utf-8',
        headers={'Content-Disposition': f'attachment; filename="{filename}"'}
    )


@posts_bp.route('/<int:post_id>/registrations/export-excel')
@login_required
def export_registrations_excel(post_id):
    """Export all student registrations as a professionally styled Microsoft Excel (.xlsx) workbook."""
    post = PrincipalPost.query.get_or_404(post_id)

    is_mgmt = current_user.is_management
    is_coord = current_user.role == 'HOD' and current_user.department_id in [d.id for d in post.departments]
    is_assigned = current_user.id == post.assigned_faculty_id
    if not (is_mgmt or is_coord or is_assigned):
        abort(403)

    fields = []
    if post.form_config:
        try:
            fields = json.loads(post.form_config)
        except Exception:
            pass

    registrations = StudentRegistration.query.filter_by(post_id=post.id).order_by(StudentRegistration.registered_at.asc()).all()

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Registrations"

    # Set grid lines visible
    ws.views.sheetView[0].showGridLines = True

    # Styling Palettes
    navy_fill = PatternFill(start_color="0F52BA", end_color="0F52BA", fill_type="solid")
    header_font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
    title_font = Font(name="Calibri", size=14, bold=True, color="002060")
    sub_font = Font(name="Calibri", size=10, italic=True, color="555555")
    data_font = Font(name="Calibri", size=10, color="000000")
    link_font = Font(name="Calibri", size=10, color="0F52BA", underline="single")
    zebra_fill = PatternFill(start_color="F8FAFC", end_color="F8FAFC", fill_type="solid")

    thin_border_side = Side(style="thin", color="CBD5E1")
    cell_border = Border(left=thin_border_side, right=thin_border_side, top=thin_border_side, bottom=thin_border_side)
    center_align = Alignment(horizontal="center", vertical="center", wrap_text=True)
    left_align = Alignment(horizontal="left", vertical="center", wrap_text=True)

    # Top Title Rows
    ws.append(["GUJARAT TECHNOLOGICAL UNIVERSITY (GTU) — ITR IIC & R&D CELL"])
    ws.cell(row=1, column=1).font = title_font
    ws.row_dimensions[1].height = 26

    depts_str = ", ".join([d.code for d in post.departments]) if post.departments else "All Departments"
    faculty_str = post.assigned_faculty.full_name if post.assigned_faculty else "Unassigned"
    ws.append([f"Activity: {post.title} | Allocated: {depts_str} | Lead Faculty: {faculty_str}"])
    ws.cell(row=2, column=1).font = sub_font
    ws.row_dimensions[2].height = 18

    ws.append([f"Total Registered Participants: {len(registrations)} | Generated: {datetime.now().strftime('%d %B %Y, %I:%M %p')}"])
    ws.cell(row=3, column=1).font = sub_font
    ws.row_dimensions[3].height = 18

    ws.append([])  # Blank row 4

    # Headers Row 5
    if fields:
        headers = ['#']
        for f in fields:
            headers.append((f.get('label') or f.get('id') or '').strip())
        headers.append('Registered Timestamp')
    else:
        headers = ['#', 'Student Name', 'Enrollment Number', 'Department', 'Semester', 'Email Address', 'Phone Number', 'Registered Timestamp']

    ws.append(headers)
    header_row_idx = 5
    ws.row_dimensions[header_row_idx].height = 28

    for col_idx in range(1, len(headers) + 1):
        c = ws.cell(row=header_row_idx, column=col_idx)
        c.fill = navy_fill
        c.font = header_font
        c.alignment = center_align
        c.border = cell_border

    host_url = request.host_url.rstrip('/')

    # Data Rows
    for r_idx, reg in enumerate(registrations, start=1):
        answers = {}
        if reg.custom_data:
            try:
                answers = json.loads(reg.custom_data) if isinstance(reg.custom_data, str) else reg.custom_data
            except Exception:
                answers = {}

        curr_row = header_row_idx + r_idx
        ws.row_dimensions[curr_row].height = 22
        is_even = (r_idx % 2 == 0)

        hyperlinks = {}
        if fields:
            row_data = [r_idx]
            for c_idx, f in enumerate(fields, start=2):
                fid = f.get('id')
                ftype = f.get('type')
                val = answers.get(fid)
                if val is None or val == '':
                    val = answers.get(f"field_{fid}")
                if (val is None or val == '') and fid in ('student_name', 'enrollment_no', 'department', 'semester', 'email', 'phone'):
                    val = getattr(reg, fid, '')
                if val is None:
                    val = ''

                if ftype == 'file' and val:
                    val_str = str(val).strip()
                    display_val = val_str.split('/')[-1] if '/' in val_str else val_str
                    dl_url = f"{host_url}/posts/uploads/{val_str}"
                    row_data.append(display_val)
                    hyperlinks[c_idx] = dl_url
                elif ftype == 'url' and val:
                    url_str = str(val).strip()
                    row_data.append(url_str)
                    target_url = url_str if url_str.startswith(('http://', 'https://')) else f"https://{url_str}"
                    hyperlinks[c_idx] = target_url
                else:
                    row_data.append(val)
            row_data.append(reg.registered_at.strftime('%Y-%m-%d %H:%M:%S'))
        else:
            row_data = [
                r_idx,
                reg.student_name,
                reg.enrollment_no,
                reg.department or '',
                reg.semester or '',
                reg.email or '',
                reg.phone or '',
                reg.registered_at.strftime('%Y-%m-%d %H:%M:%S')
            ]

        ws.append(row_data)

        for col_idx in range(1, len(row_data) + 1):
            cell = ws.cell(row=curr_row, column=col_idx)
            cell.font = data_font
            cell.border = cell_border
            if is_even:
                cell.fill = zebra_fill

            if col_idx in hyperlinks:
                cell.hyperlink = hyperlinks[col_idx]
                cell.font = link_font

            # Alignment
            if col_idx in (1, len(row_data)):
                cell.alignment = center_align
            else:
                cell.alignment = left_align

    # Auto-fit column widths
    for col in ws.columns:
        col_letter = get_column_letter(col[0].column)
        max_len = 0
        for cell in col:
            if cell.row < header_row_idx:
                continue
            val_str = str(cell.value or '')
            if len(val_str) > max_len:
                max_len = len(val_str)
        ws.column_dimensions[col_letter].width = max(min(max_len + 4, 50), 14)

    output = io.BytesIO()
    wb.save(output)
    output.seek(0)

    safe_title = "".join(c for c in post.title[:35] if c.isalnum() or c in (' ', '_', '-')).strip().replace(' ', '_')
    filename = f"registrations_{safe_title}_{post.id}.xlsx"

    return Response(
        output.read(),
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        headers={'Content-Disposition': f'attachment; filename="{filename}"'}
    )
