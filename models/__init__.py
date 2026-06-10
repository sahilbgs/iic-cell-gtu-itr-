"""
GTU-ITR R&D & IIC Portal - Models Package
Imports all models so they are registered with SQLAlchemy.
"""
from models.user import User
from models.department import Department
from models.principal_post import PrincipalPost
from models.student_registration import StudentRegistration
from models.activity_report import ActivityReport
from models.landing_post import LandingPost

__all__ = [
    'User',
    'Department',
    'PrincipalPost',
    'StudentRegistration',
    'ActivityReport',
    'LandingPost',
]

