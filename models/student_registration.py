"""
GTU-ITR R&D & IIC Portal - Student Registration Model
"""
from datetime import datetime
from extensions import db

class StudentRegistration(db.Model):
    """Registration entry of a student for an approved Principal post/activity."""
    __tablename__ = 'student_registrations'

    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey('principal_posts.id', ondelete='CASCADE'), nullable=False)
    student_name = db.Column(db.String(150), nullable=False)
    enrollment_no = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(20), nullable=True)
    semester = db.Column(db.String(20), nullable=True)
    department = db.Column(db.String(100), nullable=True)
    
    # JSON-serialized string of answers to custom fields created in the form builder
    custom_data = db.Column(db.Text, nullable=True)
    
    registered_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationship
    post = db.relationship('PrincipalPost', backref=db.backref('registrations', cascade='all, delete-orphan'))

    def __repr__(self):
        return f'<StudentRegistration {self.id}: {self.student_name} ({self.enrollment_no})>'
