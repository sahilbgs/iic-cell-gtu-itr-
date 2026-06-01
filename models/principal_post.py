"""
GTU-ITR R&D & IIC Portal - Principal Post Model
"""
from datetime import datetime
from extensions import db

POST_SOURCES = [
    ('COMPANY', 'Company'),
    ('FIRM', 'Firm'),
    ('UNIVERSITY', 'University'),
]

POST_STATUSES = [
    ('NOT_STARTED', 'Not Started'),
    ('IN_PROGRESS', 'In Progress'),
    ('COMPLETED', 'Completed'),
    ('ON_HOLD', 'On Hold'),
]

APPROVAL_STATUSES = [
    ('PENDING', 'Pending Review'),
    ('APPROVED', 'Approved'),
    ('REJECTED', 'Rejected'),
]


principal_post_departments = db.Table(
    'principal_post_departments',
    db.Column('principal_post_id', db.Integer, db.ForeignKey('principal_posts.id', ondelete='CASCADE'), primary_key=True),
    db.Column('department_id', db.Integer, db.ForeignKey('departments.id', ondelete='CASCADE'), primary_key=True)
)


class PrincipalPost(db.Model):
    """Activity or notice shared by the Principal received from external entities."""
    __tablename__ = 'principal_posts'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(300), nullable=False)  # Activity Heading
    source = db.Column(db.String(50), nullable=False, default='COMPANY')  # Company, Firm, University
    summary = db.Column(db.Text, nullable=False)
    full_content = db.Column(db.Text, nullable=False)
    start_date = db.Column(db.Date, nullable=True)
    end_date = db.Column(db.Date, nullable=True)
    attachment_path = db.Column(db.String(300), nullable=True)
    progress_status = db.Column(db.String(20), nullable=False, default='NOT_STARTED')
    
    # Linked department (optional)
    department_id = db.Column(db.Integer, db.ForeignKey('departments.id'), nullable=True)

    # Chairperson approval workflow
    approval_status = db.Column(db.String(20), nullable=False, default='PENDING')
    approved_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    approval_date = db.Column(db.DateTime, nullable=True)
    rejection_reason = db.Column(db.Text, nullable=True)
    approval_note = db.Column(db.Text, nullable=True)

    # Faculty assignment and student registration fields
    assigned_faculty_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    has_registration_form = db.Column(db.Boolean, default=False, nullable=False)
    form_config = db.Column(db.Text, nullable=True)

    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    creator = db.relationship('User', foreign_keys=[created_by])
    department = db.relationship('Department', foreign_keys=[department_id])
    departments = db.relationship('Department', secondary=principal_post_departments, backref=db.backref('principal_posts', lazy='dynamic'))
    approver = db.relationship('User', foreign_keys=[approved_by])
    assigned_faculty = db.relationship('User', foreign_keys=[assigned_faculty_id], backref=db.backref('assigned_posts', lazy='dynamic'))

    @property
    def source_label(self):
        return dict(POST_SOURCES).get(self.source, self.source)

    @property
    def status_label(self):
        return dict(POST_STATUSES).get(self.progress_status, self.progress_status)

    @property
    def approval_label(self):
        return dict(APPROVAL_STATUSES).get(self.approval_status, self.approval_status)

    @property
    def progress_percentage(self):
        if self.approval_status == 'APPROVED' and self.progress_status == 'NOT_STARTED':
            return 10
        percentages = {
            'NOT_STARTED': 0,
            'ON_HOLD': 25,
            'IN_PROGRESS': 50,
            'COMPLETED': 100
        }
        return percentages.get(self.progress_status, 0)

    def __repr__(self):
        return f'<PrincipalPost {self.id}: {self.title[:50]}>'
