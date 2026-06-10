"""
GTU-ITR R&D & IIC Portal - Landing Post Model
"""
from datetime import datetime
from extensions import db

class LandingPost(db.Model):
    """Posts created by the Chairperson to show on the public landing page."""
    __tablename__ = 'landing_posts'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(300), nullable=False)
    description = db.Column(db.Text, nullable=False)
    media_path = db.Column(db.String(300), nullable=True)
    media_type = db.Column(db.String(20), nullable=True)  # 'image' or 'video'
    is_pinned = db.Column(db.Boolean, default=False, nullable=False)
    is_hidden = db.Column(db.Boolean, default=False, nullable=False)
    is_deleted = db.Column(db.Boolean, default=False, nullable=False)
    
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    author = db.relationship('User', foreign_keys=[author_id])

    def __repr__(self):
        return f'<LandingPost {self.id}: {self.title[:50]}>'
