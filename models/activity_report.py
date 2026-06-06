"""
GTU-ITR R&D & IIC Portal - Activity Report Model
"""
from datetime import datetime
from extensions import db

class ActivityReport(db.Model):
    """Activity Report model for storing filled details and photo paths for approved events."""
    __tablename__ = 'activity_reports'

    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey('principal_posts.id', ondelete='CASCADE'), nullable=False, unique=True)
    
    title = db.Column(db.String(300), nullable=False)
    event_type = db.Column(db.String(100), nullable=False)
    event_date = db.Column(db.String(100), nullable=False)
    event_time = db.Column(db.String(100), nullable=False)
    event_mode = db.Column(db.String(50), nullable=False, default='Offline')
    venue = db.Column(db.String(200), nullable=False)
    participants_demographic = db.Column(db.String(200), nullable=False)
    organized_by = db.Column(db.String(200), nullable=False)
    supported_by = db.Column(db.String(200), nullable=True)
    description = db.Column(db.Text, nullable=False)
    num_participants = db.Column(db.Integer, nullable=False, default=0)
    
    # Store photos as JSON string: [{'path': 'reports/1/photo.jpg', 'caption': ''}]
    photos_json = db.Column(db.Text, nullable=True)
    
    # Report Status: 'DRAFT' or 'SUBMITTED'
    status = db.Column(db.String(20), nullable=False, default='DRAFT')
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship back to PrincipalPost
    post = db.relationship('PrincipalPost', backref=db.backref('activity_report', uselist=False, cascade='all, delete-orphan'))

    def __repr__(self):
        return f'<ActivityReport {self.id} for Post {self.post_id}: {self.title[:30]}>'
