"""
GTU-ITR R&D & IIC Portal - Services Package
Provides AI-powered services, notification, and export utilities.
"""

from services.ai_engine import AIEngine
from services.document_parser import DocumentParser
from services.ai_classifier import SchemeClassifier
from services.ai_email_drafter import EmailDrafter
from services.ai_proposal_generator import ProposalGenerator
from services.ai_report_generator import ReportGenerator
from services.notifications import NotificationService
from services.export import PDFExporter, ExcelExporter

__all__ = [
    'AIEngine',
    'DocumentParser',
    'SchemeClassifier',
    'EmailDrafter',
    'ProposalGenerator',
    'ReportGenerator',
    'NotificationService',
    'PDFExporter',
    'ExcelExporter',
]
