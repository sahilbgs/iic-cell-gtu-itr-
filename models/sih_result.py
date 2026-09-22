"""
GTU-ITR R&D & IIC Portal - SIH Results Model
Stores official evaluation rankings, scores, categories, and award recommendations for hackathon teams.
"""
from datetime import datetime
from extensions import db


class SihResult(db.Model):
    """Official hackathon evaluation results, rankings, and SSIP recommendations."""
    __tablename__ = 'sih_results'

    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey('principal_posts.id', ondelete='CASCADE'), nullable=True, default=2)
    registration_id = db.Column(db.Integer, db.ForeignKey('student_registrations.id', ondelete='SET NULL'), nullable=True)

    rank = db.Column(db.Integer, nullable=False, index=True)
    team_name = db.Column(db.String(150), nullable=False, index=True)
    category = db.Column(db.String(50), nullable=True)  # Software / Hardware
    psid = db.Column(db.String(50), nullable=True)
    leader_name = db.Column(db.String(150), nullable=True)
    leader_enrollment = db.Column(db.String(50), nullable=True)
    score_str = db.Column(db.String(20), nullable=True)
    score_num = db.Column(db.Integer, nullable=True)
    is_top_20 = db.Column(db.Boolean, default=False, nullable=False)
    is_ssip = db.Column(db.Boolean, default=False, nullable=False)
    reg_id = db.Column(db.String(50), nullable=True)
    photo_url = db.Column(db.String(300), nullable=True)
    status = db.Column(db.String(50), nullable=True)
    remarks = db.Column(db.Text, nullable=True)
    has_photo = db.Column(db.Boolean, default=False, nullable=False)
    team_no = db.Column(db.Integer, nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    post = db.relationship('PrincipalPost', backref=db.backref('sih_results', lazy='dynamic'))
    registration = db.relationship('StudentRegistration', backref=db.backref('sih_result', uselist=False))

    def to_dict(self):
        return {
            'id': self.id,
            'rank': self.rank,
            'team_name': self.team_name,
            'category': self.category,
            'psid': self.psid,
            'leader_name': self.leader_name,
            'leader_enrollment': self.leader_enrollment,
            'score_str': self.score_str,
            'score_num': self.score_num,
            'is_top_20': self.is_top_20,
            'is_ssip': self.is_ssip,
            'reg_id': self.reg_id,
            'photo_url': self.photo_url,
            'status': self.status,
            'remarks': self.remarks,
            'has_photo': self.has_photo,
            'team_no': self.team_no
        }

    def __repr__(self):
        return f'<SihResult Rank {self.rank}: {self.team_name} ({self.score_str})>'
