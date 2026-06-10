"""
GTU-ITR R&D & IIC Portal - Department Model
"""
from extensions import db


class Department(db.Model):
    """Academic department."""
    __tablename__ = 'departments'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), unique=True, nullable=False)
    code = db.Column(db.String(10), unique=True, nullable=False)
    hod_name = db.Column(db.String(150), nullable=True)
    email = db.Column(db.String(120), nullable=True)
    phone = db.Column(db.String(20), nullable=True)
    is_deleted = db.Column(db.Boolean, default=False, nullable=False)

    # Relationships
    users = db.relationship('User', back_populates='department', lazy='dynamic')

    def __repr__(self):
        return f'<Department {self.code}: {self.name}>'
