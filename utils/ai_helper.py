"""
GTU-ITR R&D & IIC Portal - AI Helpers Bridge
Provides convenient helper functions matching the expectations of route files,
delegating to the primary services layer.
"""
import logging
from datetime import date
from services.ai_engine import AIEngine
from services.ai_classifier import SchemeClassifier
from services.ai_proposal_generator import ProposalGenerator
from services.ai_report_generator import ReportGenerator

logger = logging.getLogger(__name__)


def classify_scheme_text(text: str) -> dict | None:
    """
    Classify a raw scheme circular or grant letter.
    Delegates to SchemeClassifier.
    """
    try:
        result = SchemeClassifier.classify(text)
        if result:
            # Add category label for the templates that expect it
            from models.scheme import SCHEME_CATEGORIES
            result['category_label'] = dict(SCHEME_CATEGORIES).get(result['category'], result['category'])
            result['confidence'] = "High (Local Phi-3 Model)"
        return result
    except Exception as exc:
        logger.error("classify_scheme_text helper failed: %s", exc)
        return None


def generate_proposal_draft(context: str) -> dict | None:
    """
    Draft a research proposal based on contextual parameters.
    Attempts to parse values like topic from the context block, then runs the generator.
    """
    try:
        # Simple extraction of key details from context block
        topic = "Not specified"
        department = "Not specified"
        funding_agency = "Not specified"
        
        for line in context.split('\n'):
            if line.startswith("Research Topic:"):
                topic = line.split(":", 1)[1].strip()
            elif line.startswith("Scheme:"):
                funding_agency = line.split(":", 1)[1].strip()
            elif line.startswith("Funding Agency:"):
                funding_agency = line.split(":", 1)[1].strip()

        # Call the actual service
        draft = ProposalGenerator.generate(
            topic=topic,
            department=department,
            funding_agency=funding_agency
        )
        
        if draft:
            # Inject keys expected by routes/ai_tools.py
            draft['topic'] = topic
            # Try to determine a budget amount
            draft['budget_amount'] = 500000.0
            import re
            m = re.search(r'(?:₹|Rs\.?)\s*([\d,]+)', draft['budget'] or '')
            if m:
                try:
                    draft['budget_amount'] = float(m.group(1).replace(',', ''))
                except ValueError:
                    pass
        return draft
    except Exception as exc:
        logger.error("generate_proposal_draft helper failed: %s", exc)
        return None


def summarize_text(text: str) -> str | None:
    """
    Summarize any raw text or report content.
    Uses AIEngine directly with a summarization prompt.
    """
    try:
        prompt = (
            "<|system|>\nYou are a professional academic summarizer. "
            "Provide a concise, bulleted executive summary of the following text.\n"
            "<|user|>\n"
            f"{text[:8000]}\n"
            "<|assistant|>\n"
            "Summary:"
        )
        response = AIEngine.generate(prompt, temperature=0.4)
        return response
    except Exception as exc:
        logger.error("summarize_text helper failed: %s", exc)
        return None


def generate_report_summary(content: str) -> str | None:
    """
    Generates a concise bullet point summary of periodic R&D performance data.
    """
    try:
        prompt = (
            "<|system|>\nYou are an assistant for a university R&D office. "
            "Create a brief 2-3 sentence executive highlight of this monthly/periodic report data.\n"
            "<|user|>\n"
            f"{content[:5000]}\n"
            "<|assistant|>\n"
            "Highlight Summary:"
        )
        response = AIEngine.generate(prompt, temperature=0.3)
        return response
    except Exception as exc:
        logger.error("generate_report_summary helper failed: %s", exc)
        return None


def analyze_trends(analysis_text: str) -> str | None:
    """
    Uses the AI Engine to interpret aggregated trend metrics and write a descriptive summary.
    """
    try:
        prompt = (
            "<|system|>\nYou are an R&D trend analyzer at Gujarat Technological University. "
            "Analyze the R&D statistics listed below and provide a professional, encouraging "
            "interpretation of the research outputs, growth areas, and recommendations.\n"
            "<|user|>\n"
            f"{analysis_text}\n"
            "<|assistant|>\n"
            "Analysis:"
        )
        response = AIEngine.generate(prompt, temperature=0.6)
        return response
    except Exception as exc:
        logger.error("analyze_trends helper failed: %s", exc)
        return None
