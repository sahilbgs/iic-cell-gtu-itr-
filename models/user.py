"""
GTU-ITR R&D & IIC Portal - User Model
"""
from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from extensions import db


# Valid user roles
ROLES = [
    'PRINCIPAL',
    'CHAIRPERSON',
    'RD_COORDINATOR',
    'DEPT_COORDINATOR',
    'FACULTY',
    'STUDENT_REP',
]

ROLE_LABELS = {
    'PRINCIPAL': 'Principal',
    'CHAIRPERSON': 'Chairperson',
    'RD_COORDINATOR': 'R&D Coordinator',
    'DEPT_COORDINATOR': 'Dept. Coordinator',
    'FACULTY': 'Faculty',
    'STUDENT_REP': 'Student Representative',
}


class User(UserMixin, db.Model):
    """User account with role-based access."""
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    full_name = db.Column(db.String(150), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='FACULTY')
    department_id = db.Column(db.Integer, db.ForeignKey('departments.id'), nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    phone = db.Column(db.String(20), nullable=True)
    designation = db.Column(db.String(100), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    department = db.relationship('Department', back_populates='users')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @property
    def role_label(self):
        return ROLE_LABELS.get(self.role, self.role)

    @property
    def is_management(self):
        return self.role in ('PRINCIPAL', 'CHAIRPERSON', 'RD_COORDINATOR')

    def can_access_dept(self, dept_id):
        if self.is_management:
            return True
        return self.department_id == dept_id

    def __repr__(self):
        return f'<User {self.email} ({self.role})>'
