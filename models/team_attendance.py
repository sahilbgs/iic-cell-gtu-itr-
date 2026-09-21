"""
GTU-ITR R&D & IIC Portal - Team Attendance Model
Stores venue attendance, presence status, and group selfie submissions.
"""
from datetime import datetime
from extensions import db

class TeamAttendance(db.Model):
    """Attendance record for a registered hackathon team."""
    __tablename__ = 'team_attendance'

    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey('principal_posts.id', ondelete='CASCADE'), nullable=True)
    registration_id = db.Column(db.Integer, db.ForeignKey('student_registrations.id', ondelete='SET NULL'), nullable=True)
    
    team_name = db.Column(db.String(150), nullable=False)
    leader_name = db.Column(db.String(150), nullable=False)
    leader_phone = db.Column(db.String(50), nullable=True)
    leader_enrollment = db.Column(db.String(50), nullable=True)
    
    psid = db.Column(db.String(50), nullable=True)
    ps_title = db.Column(db.Text, nullable=True)
    theme = db.Column(db.String(150), nullable=True)
    
    total_members = db.Column(db.Integer, default=0)
    present_count = db.Column(db.Integer, default=0)
    absent_count = db.Column(db.Integer, default=0)
    
    # JSON-serialized array of member details and their status (present/absent)
    members_presence = db.Column(db.Text, nullable=True)
    
    # Base64 or relative file path to the uploaded group selfie
    selfie_image = db.Column(db.Text, nullable=True)
    
    remarks = db.Column(db.String(255), nullable=True)
    location_meta = db.Column(db.String(255), nullable=True)
    
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        import json
        return {
            'id': self.id,
            'post_id': self.post_id,
            'registration_id': self.registration_id,
            'team_name': self.team_name,
            'leader_name': self.leader_name,
            'leader_phone': self.leader_phone,
            'leader_enrollment': self.leader_enrollment,
            'psid': self.psid,
            'ps_title': self.ps_title,
            'theme': self.theme,
            'total_members': self.total_members,
            'present_count': self.present_count,
            'absent_count': self.absent_count,
            'members_presence': json.loads(self.members_presence) if self.members_presence else [],
            'selfie_image': self.selfie_image,
            'remarks': self.remarks,
            'location_meta': self.location_meta,
            'submitted_at': self.submitted_at.isoformat() if self.submitted_at else None,
            'submitted_at_formatted': self.submitted_at.strftime('%d %b %Y, %I:%M %p') if self.submitted_at else None
        }

    def __repr__(self):
        return f'<TeamAttendance {self.id}: {self.team_name} ({self.present_count}/{self.total_members})>'
