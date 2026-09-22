"""
GTU-ITR R&D & IIC Portal - Database & Schema Explorer Routes
Blueprint: database  |  Prefix: /database and /admin/database
Provides visual schema overview, interconnected relationships graph, and live data table browser.
"""
import json
from datetime import datetime, date
from decimal import Decimal
from functools import wraps
from flask import Blueprint, render_template, request, jsonify, abort, Response, current_app, redirect
from flask_login import login_required, current_user
from sqlalchemy import inspect, text
from extensions import db, csrf

database_bp = Blueprint('database', __name__)


def admin_required(f):
    """Decorator: only MASTER_ADMIN, CHAIRPERSON, and PRINCIPAL can access database explorer and canvas."""
    @wraps(f)
    @login_required
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role not in ('MASTER_ADMIN', 'CHAIRPERSON', 'PRINCIPAL'):
            abort(403)
        return f(*args, **kwargs)
    return decorated

TABLE_DESCRIPTIONS = {
    'departments': 'College Academic Departments & Branches (HODs, Contact Details)',
    'users': 'Authorized Faculty, Management, HODs, & Student Representatives',
    'principal_posts': 'Central Activities, Hackathons, Circulars, & Event Directives',
    'principal_post_departments': 'Many-to-Many Bridge: Activities allocated to Academic Departments',
    'student_registrations': 'Student Applications & Registrations for Approved Activities',
    'team_attendance': 'Hackathon & Event Team Attendance, Presence, & Group Selfies',
    'sih_results': 'Smart India Hackathon 2026 Official Team Rankings, Scores, & SSIP Awards',
    'activity_reports': 'Post-Event Outcome Documentation, Attendance Counts, & Media',
    'landing_posts': 'Public Showcase Posts & Featured Highlights curated by Chairperson',
    'auth_audit_logs': 'Security & Compliance Trail: Login Attempts, Sessions, & Events',
    'visitor_sessions': 'Web Traffic Visitor Sessions, Duration, & Device Breakdown',
    'visitor_logs': 'Detailed Pageview Navigation & Endpoint Access Logs'
}

TABLE_ICONS = {
    'departments': 'building-2',
    'users': 'users',
    'principal_posts': 'file-text',
    'principal_post_departments': 'network',
    'student_registrations': 'user-check',
    'team_attendance': 'clipboard-check',
    'sih_results': 'trophy',
    'activity_reports': 'file-check-2',
    'landing_posts': 'sparkles',
    'auth_audit_logs': 'shield-alert',
    'visitor_sessions': 'globe',
    'visitor_logs': 'activity'
}

TABLE_COLORS = {
    'departments': '#3b82f6',
    'users': '#8b5cf6',
    'principal_posts': '#0f52ba',
    'principal_post_departments': '#6366f1',
    'student_registrations': '#10b981',
    'team_attendance': '#059669',
    'sih_results': '#f59e0b',
    'activity_reports': '#0284c7',
    'landing_posts': '#d62828',
    'auth_audit_logs': '#f59e0b',
    'visitor_sessions': '#06b6d4',
    'visitor_logs': '#64748b'
}


def serialize_value(val, col_name=''):
    """Serialize database values safely for JSON response."""
    if val is None:
        return None
    if 'password' in col_name.lower():
        return '•••••••••••• (Hash Protected)'
    if isinstance(val, (datetime, date)):
        return val.isoformat()
    if isinstance(val, Decimal):
        return float(val)
    if isinstance(val, bytes):
        return f'<{len(val)} bytes>'
    return val


def get_fk_labels_map():
    """Build a lookup map for foreign key IDs to human-readable names."""
    fk_labels = {
        'department_id': {},
        'user_id': {},
        'created_by': {},
        'approved_by': {},
        'assigned_faculty_id': {},
        'author_id': {},
        'post_id': {},
        'principal_post_id': {},
        'registration_id': {}
    }
    try:
        # Departments
        depts = db.session.execute(text("SELECT id, name, code FROM departments")).fetchall()
        for r in depts:
            fk_labels['department_id'][str(r[0])] = f"{r[1]} ({r[2]})"

        # Users
        users = db.session.execute(text("SELECT id, full_name, role FROM users")).fetchall()
        for r in users:
            label = f"{r[1]} [{r[2]}]"
            fk_labels['user_id'][str(r[0])] = label
            fk_labels['created_by'][str(r[0])] = label
            fk_labels['approved_by'][str(r[0])] = label
            fk_labels['assigned_faculty_id'][str(r[0])] = label
            fk_labels['author_id'][str(r[0])] = label

        # Principal Posts
        posts = db.session.execute(text("SELECT id, title FROM principal_posts")).fetchall()
        for r in posts:
            label = f"{r[1][:45]}..." if len(r[1]) > 45 else r[1]
            fk_labels['post_id'][str(r[0])] = label
            fk_labels['principal_post_id'][str(r[0])] = label

        # Student Registrations
        regs = db.session.execute(text("SELECT id, student_name, enrollment_no FROM student_registrations")).fetchall()
        for r in regs:
            fk_labels['registration_id'][str(r[0])] = f"{r[1]} ({r[2]})"
    except Exception as e:
        current_app.logger.warning(f"Error fetching fk_labels: {e}")

    return fk_labels


# --------------------------------------------------------------------------- #
#  Web Page Views
# --------------------------------------------------------------------------- #
@database_bp.route('/database')
@database_bp.route('/admin/database')
@database_bp.route('/database-schema')
@admin_required
def explorer():
    """Render the Interactive Database Schema & Live Table Explorer page."""
    inspector = inspect(db.engine)
    table_names = inspector.get_table_names()

    # Preferred order of display showing logical flow
    ordered_tables = [
        'departments',
        'users',
        'principal_posts',
        'principal_post_departments',
        'student_registrations',
        'team_attendance',
        'sih_results',
        'activity_reports',
        'landing_posts',
        'auth_audit_logs',
        'visitor_sessions',
        'visitor_logs'
    ]
    # Add any extra tables that might exist
    for t in table_names:
        if t not in ordered_tables:
            ordered_tables.append(t)

    table_summaries = []
    total_db_records = 0

    for t in ordered_tables:
        if t not in table_names:
            continue
        try:
            row_count = db.session.execute(text(f'SELECT count(*) FROM "{t}"')).scalar() or 0
        except Exception:
            row_count = 0
        total_db_records += row_count

        cols = inspector.get_columns(t)
        pks = inspector.get_pk_constraint(t).get('constrained_columns', [])
        fks = inspector.get_foreign_keys(t)

        table_summaries.append({
            'name': t,
            'description': TABLE_DESCRIPTIONS.get(t, 'System Table'),
            'icon': TABLE_ICONS.get(t, 'table'),
            'color': TABLE_COLORS.get(t, '#475569'),
            'row_count': row_count,
            'column_count': len(cols),
            'pks': pks,
            'fks': [{'column': fk['constrained_columns'][0] if fk['constrained_columns'] else '',
                     'referred_table': fk['referred_table'],
                     'referred_column': fk['referred_columns'][0] if fk['referred_columns'] else ''}
                    for fk in fks]
        })

    return render_template(
        'database/explorer.html',
        tables=table_summaries,
        total_tables=len(table_summaries),
        total_records=total_db_records
    )


@database_bp.route('/database/canvas')
@database_bp.route('/database-canvas')
@database_bp.route('/canvas')
@admin_required
def canvas_view():
    """Render the Dedicated Full-Screen Interactive HTML5 Canvas Node-Graph page."""
    inspector = inspect(db.engine)
    table_names = inspector.get_table_names()

    ordered_tables = [
        'departments',
        'users',
        'principal_posts',
        'principal_post_departments',
        'student_registrations',
        'team_attendance',
        'sih_results',
        'activity_reports',
        'landing_posts',
        'auth_audit_logs',
        'visitor_sessions',
        'visitor_logs'
    ]
    for t in table_names:
        if t not in ordered_tables:
            ordered_tables.append(t)

    table_summaries = []
    total_db_records = 0

    for t in ordered_tables:
        if t not in table_names:
            continue
        try:
            row_count = db.session.execute(text(f'SELECT count(*) FROM "{t}"')).scalar() or 0
        except Exception:
            row_count = 0
        total_db_records += row_count

        cols = inspector.get_columns(t)
        pks = inspector.get_pk_constraint(t).get('constrained_columns', [])
        fks = inspector.get_foreign_keys(t)

        table_summaries.append({
            'name': t,
            'description': TABLE_DESCRIPTIONS.get(t, 'System Table'),
            'icon': TABLE_ICONS.get(t, 'table'),
            'color': TABLE_COLORS.get(t, '#475569'),
            'row_count': row_count,
            'column_count': len(cols),
            'pks': pks,
            'fks': [{'column': fk['constrained_columns'][0] if fk['constrained_columns'] else '',
                     'referred_table': fk['referred_table'],
                     'referred_column': fk['referred_columns'][0] if fk['referred_columns'] else ''}
                    for fk in fks]
        })

    return render_template(
        'database/canvas.html',
        tables=table_summaries,
        total_tables=len(table_summaries),
        total_records=total_db_records
    )








@database_bp.route('/api/database/graph')
@admin_required
def api_graph():
    """Return nodes and edges formatted for HTML5 Canvas / Vis.js network visualization."""
    inspector = inspect(db.engine)
    table_names = inspector.get_table_names()

    TABLE_GROUPS = {
        'departments': 'Academic Core',
        'users': 'Academic Core',
        'principal_posts': 'Central Activities',
        'principal_post_departments': 'Central Activities',
        'activity_reports': 'Central Activities',
        'student_registrations': 'Student Participation',
        'team_attendance': 'Hackathon & Attendance',
        'sih_results': 'Hackathon & Attendance',
        'landing_posts': 'Public Showcase',
        'auth_audit_logs': 'System Security',
        'visitor_sessions': 'Traffic Intelligence',
        'visitor_logs': 'Traffic Intelligence'
    }

    nodes = []
    edges = []
    edge_id = 1

    for t in table_names:
        row_count = db.session.execute(text(f'SELECT count(*) FROM "{t}"')).scalar() or 0
        cols = inspector.get_columns(t)
        pks = inspector.get_pk_constraint(t).get('constrained_columns', [])
        fks = inspector.get_foreign_keys(t)

        nodes.append({
            'id': t,
            'label': f"{t}\n({row_count:,} rows)",
            'title': f"<b>Table: {t}</b><br/>{TABLE_DESCRIPTIONS.get(t, '')}<br/><b>Records:</b> {row_count:,}<br/><b>Columns:</b> {len(cols)}",
            'group': TABLE_GROUPS.get(t, 'Other'),
            'color': {
                'background': TABLE_COLORS.get(t, '#475569'),
                'border': '#1e293b',
                'highlight': {'background': '#d62828', 'border': '#ffffff'},
                'hover': {'background': '#2563eb', 'border': '#ffffff'}
            },
            'shape': 'box',
            'font': {'color': '#ffffff', 'size': 14, 'bold': True, 'face': 'Inter, sans-serif'},
            'margin': 14,
            'shadow': {'enabled': True, 'color': 'rgba(0,0,0,0.25)', 'size': 10, 'x': 3, 'y': 3},
            'row_count': row_count,
            'column_count': len(cols),
            'columns': [{'name': c['name'], 'type': str(c['type']), 'is_pk': c['name'] in pks} for c in cols]
        })

        for fk in fks:
            from_col = fk['constrained_columns'][0] if fk['constrained_columns'] else ''
            to_tbl = fk['referred_table']
            to_col = fk['referred_columns'][0] if fk['referred_columns'] else ''
            if to_tbl in table_names:
                edges.append({
                    'id': f"e_{edge_id}",
                    'from': t,
                    'to': to_tbl,
                    'label': from_col,
                    'title': f"<b>Foreign Key Connection:</b><br/>{t}.{from_col} ➔ {to_tbl}.{to_col}",
                    'arrows': 'to',
                    'color': {'color': '#6366f1', 'highlight': '#d62828', 'hover': '#2563eb', 'opacity': 0.85},
                    'font': {'size': 11, 'color': '#475569', 'background': '#ffffff', 'strokeWidth': 1},
                    'smooth': {'type': 'cubicBezier', 'roundness': 0.35},
                    'width': 2.5
                })
                edge_id += 1

    return jsonify({
        'nodes': nodes,
        'edges': edges,
        'total_nodes': len(nodes),
        'total_edges': len(edges)
    })


# --------------------------------------------------------------------------- #
#  JSON API Endpoints
# --------------------------------------------------------------------------- #
@database_bp.route('/api/database/schema')
@admin_required
def api_schema():
    """Return complete schema metadata, columns, PKs, FKs, and relationships."""
    inspector = inspect(db.engine)
    table_names = inspector.get_table_names()

    schema_data = {}
    relations = []
    total_records = 0

    for t in table_names:
        row_count = db.session.execute(text(f'SELECT count(*) FROM "{t}"')).scalar() or 0
        total_records += row_count
        cols = inspector.get_columns(t)
        pk_info = inspector.get_pk_constraint(t)
        pks = pk_info.get('constrained_columns', [])
        fks = inspector.get_foreign_keys(t)

        formatted_cols = []
        for c in cols:
            is_pk = c['name'] in pks
            fk_target = None
            for fk in fks:
                if c['name'] in fk['constrained_columns']:
                    idx = fk['constrained_columns'].index(c['name'])
                    fk_target = f"{fk['referred_table']}.{fk['referred_columns'][idx]}"
                    break

            formatted_cols.append({
                'name': c['name'],
                'type': str(c['type']),
                'nullable': c.get('nullable', True),
                'primary_key': is_pk,
                'foreign_key': fk_target
            })

        formatted_fks = []
        for fk in fks:
            from_col = fk['constrained_columns'][0] if fk['constrained_columns'] else ''
            to_tbl = fk['referred_table']
            to_col = fk['referred_columns'][0] if fk['referred_columns'] else ''
            formatted_fks.append({
                'column': from_col,
                'referred_table': to_tbl,
                'referred_column': to_col
            })
            relations.append({
                'from_table': t,
                'from_column': from_col,
                'to_table': to_tbl,
                'to_column': to_col,
                'label': f"{t}.{from_col} -> {to_tbl}.{to_col}"
            })

        schema_data[t] = {
            'name': t,
            'description': TABLE_DESCRIPTIONS.get(t, 'System Entity Table'),
            'icon': TABLE_ICONS.get(t, 'database'),
            'color': TABLE_COLORS.get(t, '#64748b'),
            'row_count': row_count,
            'primary_keys': pks,
            'foreign_keys': formatted_fks,
            'columns': formatted_cols
        }

    return jsonify({
        'database': 'iic_cell_gtu',
        'engine': 'PostgreSQL 16',
        'tables': schema_data,
        'relations': relations,
        'total_tables': len(table_names),
        'total_records': total_records
    })


@database_bp.route('/api/database/table/<string:table_name>')
@admin_required
def api_table_data(table_name):
    """Return paginated, searchable, sorted records for a specific table."""
    inspector = inspect(db.engine)
    existing_tables = inspector.get_table_names()

    if table_name not in existing_tables:
        return jsonify({'error': f'Table "{table_name}" does not exist.'}), 404

    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('page_size', 25, type=int)
    page_size = max(5, min(100, page_size))  # clamp between 5 and 100
    search = request.args.get('search', '').strip()
    sort_by = request.args.get('sort_by', '').strip()
    sort_dir = request.args.get('sort_dir', 'asc').lower()
    if sort_dir not in ('asc', 'desc'):
        sort_dir = 'asc'

    cols = inspector.get_columns(table_name)
    col_names = [c['name'] for c in cols]
    pk_info = inspector.get_pk_constraint(table_name)
    pks = pk_info.get('constrained_columns', [])
    fks = inspector.get_foreign_keys(table_name)

    fk_map = {}
    for fk in fks:
        for i, cname in enumerate(fk['constrained_columns']):
            fk_map[cname] = {
                'referred_table': fk['referred_table'],
                'referred_column': fk['referred_columns'][i]
            }

    # Build base select
    where_clauses = []
    params = {}

    if search:
        search_terms = []
        for c in cols:
            ctype = str(c['type']).upper()
            if any(t in ctype for t in ['CHAR', 'TEXT', 'VARCHAR']):
                param_key = f"s_{c['name']}"
                search_terms.append(f'CAST("{c["name"]}" AS TEXT) ILIKE :{param_key}')
                params[param_key] = f"%{search}%"
            elif any(t in ctype for t in ['INT', 'SERIAL']):
                if search.isdigit():
                    param_key = f"s_{c['name']}"
                    search_terms.append(f'"{c["name"]}" = :{param_key}')
                    params[param_key] = int(search)

        if search_terms:
            where_clauses.append(f"({' OR '.join(search_terms)})")

    where_sql = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""

    # Count total
    count_sql = text(f'SELECT count(*) FROM "{table_name}" {where_sql}')
    total_rows = db.session.execute(count_sql, params).scalar() or 0

    # Sorting
    if sort_by and sort_by in col_names:
        order_sql = f'ORDER BY "{sort_by}" {sort_dir.upper()} NULLS LAST'
    elif pks:
        order_sql = f'ORDER BY "{pks[0]}" ASC'
    else:
        order_sql = f'ORDER BY 1 ASC'

    offset = (page - 1) * page_size
    data_sql = text(f'SELECT * FROM "{table_name}" {where_sql} {order_sql} LIMIT {page_size} OFFSET {offset}')
    result = db.session.execute(data_sql, params)

    rows = []
    for row in result:
        row_dict = {}
        mapping = row._mapping
        for cname in col_names:
            row_dict[cname] = serialize_value(mapping.get(cname), cname)
        rows.append(row_dict)

    total_pages = max(1, (total_rows + page_size - 1) // page_size)
    fk_labels = get_fk_labels_map()

    return jsonify({
        'table': table_name,
        'description': TABLE_DESCRIPTIONS.get(table_name, ''),
        'icon': TABLE_ICONS.get(table_name, 'database'),
        'columns': [{'name': c['name'], 'type': str(c['type']), 'is_pk': c['name'] in pks} for c in cols],
        'primary_keys': pks,
        'foreign_keys': fk_map,
        'fk_labels': fk_labels,
        'rows': rows,
        'total_rows': total_rows,
        'page': page,
        'page_size': page_size,
        'total_pages': total_pages
    })


@database_bp.route('/api/database/record/<string:table_name>/<string:record_id>')
@admin_required
def api_record_detail(table_name, record_id):
    """Return single record detail with all its directly interconnected parent and child records."""
    inspector = inspect(db.engine)
    if table_name not in inspector.get_table_names():
        return jsonify({'error': 'Table not found'}), 404

    pk_info = inspector.get_pk_constraint(table_name)
    pks = pk_info.get('constrained_columns', [])
    if not pks:
        return jsonify({'error': 'Table has no primary key'}), 400

    pk_col = pks[0]
    row = db.session.execute(
        text(f'SELECT * FROM "{table_name}" WHERE "{pk_col}" = :rid'),
        {'rid': record_id}
    ).fetchone()

    if not row:
        return jsonify({'error': 'Record not found'}), 404

    row_data = {c['name']: serialize_value(row._mapping.get(c['name']), c['name'])
                for c in inspector.get_columns(table_name)}

    # Fetch connected child/parent records based on table relationships
    interconnected = {}

    if table_name == 'departments':
        dept_id = int(record_id) if record_id.isdigit() else 0
        # Users in department
        u_rows = db.session.execute(
            text('SELECT id, full_name, email, role, designation FROM users WHERE department_id = :did'),
            {'did': dept_id}
        ).fetchall()
        interconnected['users'] = [dict(r._mapping) for r in u_rows]

        # Posts allocated to department
        p_rows = db.session.execute(
            text('''
                SELECT p.id, p.title, p.progress_status, p.approval_status
                FROM principal_posts p
                JOIN principal_post_departments pd ON pd.principal_post_id = p.id
                WHERE pd.department_id = :did
            '''),
            {'did': dept_id}
        ).fetchall()
        interconnected['principal_posts'] = [dict(r._mapping) for r in p_rows]

    elif table_name == 'users':
        user_id = int(record_id) if record_id.isdigit() else 0
        # Posts created by or assigned to user
        p_rows = db.session.execute(
            text('SELECT id, title, progress_status, approval_status FROM principal_posts WHERE created_by = :uid OR assigned_faculty_id = :uid'),
            {'uid': user_id}
        ).fetchall()
        interconnected['principal_posts'] = [dict(r._mapping) for r in p_rows]

        # Auth logs
        auth_rows = db.session.execute(
            text('SELECT id, event_type, status, ip_address, created_at FROM auth_audit_logs WHERE user_id = :uid ORDER BY created_at DESC LIMIT 10'),
            {'uid': user_id}
        ).fetchall()
        interconnected['auth_audit_logs'] = [
            {k: serialize_value(v, k) for k, v in dict(r._mapping).items()} for r in auth_rows
        ]

    elif table_name == 'principal_posts':
        post_id = int(record_id) if record_id.isdigit() else 0
        # Allocated Departments
        d_rows = db.session.execute(
            text('''
                SELECT d.id, d.name, d.code, d.hod_name
                FROM departments d
                JOIN principal_post_departments pd ON pd.department_id = d.id
                WHERE pd.principal_post_id = :pid
            '''),
            {'pid': post_id}
        ).fetchall()
        interconnected['departments'] = [dict(r._mapping) for r in d_rows]

        # Student Registrations
        reg_rows = db.session.execute(
            text('SELECT id, student_name, enrollment_no, email, department, registered_at FROM student_registrations WHERE post_id = :pid ORDER BY id ASC'),
            {'pid': post_id}
        ).fetchall()
        interconnected['student_registrations'] = [
            {k: serialize_value(v, k) for k, v in dict(r._mapping).items()} for r in reg_rows
        ]

        # Team Attendance
        att_rows = db.session.execute(
            text('SELECT id, registration_id, team_name, leader_name, present_count, total_members, submitted_at FROM team_attendance WHERE post_id = :pid ORDER BY id ASC'),
            {'pid': post_id}
        ).fetchall()
        interconnected['team_attendance'] = [
            {k: serialize_value(v, k) for k, v in dict(r._mapping).items()} for r in att_rows
        ]

        # Activity Report
        rpt = db.session.execute(
            text('SELECT id, title, event_mode, venue, num_participants, status FROM activity_reports WHERE post_id = :pid'),
            {'pid': post_id}
        ).fetchone()
        interconnected['activity_report'] = dict(rpt._mapping) if rpt else None

    elif table_name == 'student_registrations':
        reg_id = int(record_id) if record_id.isdigit() else 0
        # Team attendance linked to this registration
        att_rows = db.session.execute(
            text('SELECT id, team_name, leader_name, present_count, total_members, submitted_at FROM team_attendance WHERE registration_id = :rid'),
            {'rid': reg_id}
        ).fetchall()
        interconnected['team_attendance'] = [
            {k: serialize_value(v, k) for k, v in dict(r._mapping).items()} for r in att_rows
        ]

    return jsonify({
        'table': table_name,
        'record': row_data,
        'interconnected': interconnected,
        'fk_labels': get_fk_labels_map()
    })


@database_bp.route('/api/database/flow-tree')
@admin_required
def api_flow_tree():
    """Return full interconnected tree data: Departments -> Users & Posts -> Registrations -> Attendance."""
    try:
        # Departments
        depts_res = db.session.execute(
            text('SELECT id, name, code, hod_name FROM departments ORDER BY name ASC')
        ).fetchall()

        tree = []
        for d in depts_res:
            dept_dict = dict(d._mapping)
            # Users in dept
            users_res = db.session.execute(
                text('SELECT id, full_name, email, role, designation FROM users WHERE department_id = :did'),
                {'did': d[0]}
            ).fetchall()
            dept_dict['users'] = [dict(u._mapping) for u in users_res]

            # Posts for dept
            posts_res = db.session.execute(
                text('''
                    SELECT p.id, p.title, p.progress_status, p.approval_status,
                           u.full_name as faculty_lead
                    FROM principal_posts p
                    LEFT JOIN users u ON u.id = p.assigned_faculty_id
                    JOIN principal_post_departments pd ON pd.principal_post_id = p.id
                    WHERE pd.department_id = :did
                '''),
                {'did': d[0]}
            ).fetchall()

            posts_list = []
            for p in posts_res:
                p_dict = dict(p._mapping)
                # Count registrations and attendance for this post
                reg_count = db.session.execute(
                    text('SELECT count(*) FROM student_registrations WHERE post_id = :pid'),
                    {'pid': p[0]}
                ).scalar() or 0
                att_count = db.session.execute(
                    text('SELECT count(*) FROM team_attendance WHERE post_id = :pid'),
                    {'pid': p[0]}
                ).scalar() or 0
                p_dict['registration_count'] = reg_count
                p_dict['attendance_count'] = att_count
                posts_list.append(p_dict)

            dept_dict['posts'] = posts_list
            tree.append(dept_dict)

        return jsonify({'tree': tree})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@database_bp.route('/api/database/export/<string:table_name>')
@admin_required
def export_table(table_name):
    """Export table data as JSON or CSV."""
    inspector = inspect(db.engine)
    if table_name not in inspector.get_table_names():
        abort(404)

    fmt = request.args.get('format', 'json').lower()
    cols = [c['name'] for c in inspector.get_columns(table_name)]

    result = db.session.execute(text(f'SELECT * FROM "{table_name}"'))
    rows = []
    for r in result:
        m = r._mapping
        rows.append({c: serialize_value(m.get(c), c) for c in cols})

    if fmt == 'csv':
        import io
        import csv
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=cols)
        writer.writeheader()
        for r in rows:
            writer.writerow(r)
        csv_data = output.getvalue()
        return Response(
            csv_data,
            mimetype='text/csv',
            headers={'Content-Disposition': f'attachment;filename={table_name}.csv'}
        )

    return Response(
        json.dumps(rows, indent=2),
        mimetype='application/json',
        headers={'Content-Disposition': f'attachment;filename={table_name}.json'}
    )
