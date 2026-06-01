"""
GTU-ITR R&D & IIC Portal - AI Post Extractor Service
Sends raw email or announcement text to the local AI engine to extract structured details,
with a robust regex and keyword-based heuristic fallback.
"""
import json
import logging
import re
from datetime import datetime

from services.ai_engine import AIEngine

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# System prompt for local AI model (Phi-3)
# ---------------------------------------------------------------------------
_SYSTEM_PROMPT = """\
You are an expert assistant for a university Research & Development and IIC office.
Analyse the following document text representing an email, proposal, or notice received by the Principal from a company, firm, or university. Extract the key details.

Return your answer as a single, valid JSON object with exactly these keys:

{
  "activity_heading": "<activity title or heading>",
  "source": "<one of: COMPANY, FIRM, UNIVERSITY>",
  "summary": "<concise 2-3 sentence summary of the activity/email>",
  "start_date": "<start date in YYYY-MM-DD format, or null if not found>",
  "end_date": "<end date/deadline in YYYY-MM-DD format, or null if not found>",
  "department": "<one of: CE, IT, ME, CIV, EE, EC, or null if not specific to a department>",
  "full_content": "<the full detailed body/text of the announcement>"
}

Rules:
- Return ONLY the JSON object, no additional text or markdown fencing.
- If a field cannot be determined, use null.
- The source MUST be one of: COMPANY, FIRM, UNIVERSITY.
- The department MUST be one of: CE, IT, ME, CIV, EE, EC, or null.
"""


class PostExtractor:
    """
    Extracts structured principal post metadata from raw email/document text using the
    local AI engine, falling back to a pattern-based heuristic ruleset on failure.
    """

    _EXPECTED_KEYS = {
        'activity_heading', 'source', 'summary', 'start_date', 'end_date',
        'department', 'full_content'
    }

    _VALID_SOURCES = {'COMPANY', 'FIRM', 'UNIVERSITY'}
    _VALID_DEPARTMENTS = {'CE', 'IT', 'ME', 'CIV', 'EE', 'EC'}

    @classmethod
    def extract(cls, raw_text: str, use_ai: bool = True) -> dict:
        """
        Analyse *raw_text* and return a dict of post fields.
        Always returns a valid dictionary (falling back to heuristics if AI fails or is disabled).
        """
        if not raw_text or not raw_text.strip():
            logger.warning("PostExtractor.extract() called with empty text.")
            return cls._heuristic_extract("")

        if use_ai:
            try:
                # Truncate to fit context window
                truncated = raw_text[:8_000]

                prompt = (
                    f"{_SYSTEM_PROMPT}\n\n"
                    f"--- EMAIL / DOCUMENT TEXT ---\n{truncated}\n--- END ---\n\n"
                    "JSON:"
                )

                response = AIEngine.generate(
                    prompt,
                    temperature=0.2,   # Low temperature for factual extraction
                    top_p=0.8,
                )

                if response:
                    parsed = cls._extract_json(response)
                    if parsed:
                        return cls._normalise(parsed, raw_text)
                    else:
                        logger.warning("Could not parse JSON from AI response, falling back to heuristics.")
                else:
                    logger.warning("AI Engine returned None, falling back to heuristics.")

            except Exception as exc:
                logger.error("AI Post extraction failed: %s. Falling back to heuristics.", exc)

        # Fallback to heuristics if AI is disabled or fails
        return cls._heuristic_extract(raw_text)

    # ------------------------------------------------------------------
    # JSON extraction helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _extract_json(text: str) -> dict | None:
        """Attempt to extract JSON from AI output."""
        try:
            return json.loads(text)
        except (json.JSONDecodeError, TypeError):
            pass

        # Search for {...} block
        patterns = [
            r'```json\s*(\{.*?\})\s*```',
            r'```\s*(\{.*?\})\s*```',
            r'(\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\})',
        ]
        for pattern in patterns:
            match = re.search(pattern, text, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group(1))
                except (json.JSONDecodeError, TypeError):
                    continue
        return None

    @classmethod
    def _normalise(cls, data: dict, original_text: str) -> dict:
        """Ensure the dictionary matches exactly what we expect."""
        result = {}
        for key in cls._EXPECTED_KEYS:
            result[key] = data.get(key)

        # Enforce enum values
        if result.get('source') not in cls._VALID_SOURCES:
            result['source'] = 'COMPANY'

        if result.get('department') not in cls._VALID_DEPARTMENTS:
            result['department'] = None

        # Clean dates
        for date_key in ('start_date', 'end_date'):
            val = result.get(date_key)
            if val:
                # Basic YYYY-MM-DD validation
                if not re.match(r'^\d{4}-\d{2}-\d{2}$', str(val)):
                    result[date_key] = None

        # Ensure full_content is not empty
        if not result.get('full_content'):
            result['full_content'] = original_text

        # Ensure summary is not empty
        if not result.get('summary'):
            result['summary'] = original_text[:200] + '...' if len(original_text) > 200 else original_text

        return result

    # ------------------------------------------------------------------
    # Heuristic Rule-Based Fallback
    # ------------------------------------------------------------------

    @classmethod
    def _heuristic_extract(cls, text: str) -> dict:
        """
        Fast rule-based regex and keyword extractor for principal posts.
        Extremely reliable fallback that guarantees fields are populated.
        """
        result = {
            'activity_heading': '',
            'source': 'COMPANY',
            'summary': '',
            'start_date': None,
            'end_date': None,
            'department': None,
            'full_content': text
        }

        if not text or not text.strip():
            return result

        text_lower = text.lower()

        # 1. Heading Extraction
        heading = ""
        # Try to find conference/workshop quotes first
        quote_pattern = r'(?:conference|workshop|seminar|hackathon|round table|program)\s+(?:on|about)\s+["\u201c\u201d\'\u2018\u2019]([^"\u201c\u201d\'\u2018\u2019\n]+)["\u201c\u201d\'\u2018\u2019]'
        quote_match = re.search(quote_pattern, text, re.IGNORECASE)
        if quote_match:
            heading = quote_match.group(1).strip()

        if not heading:
            # Try keyword-based extraction BEFORE falling back to first line
            # Normalize newlines to spaces for matching (handles "Conference\non\n...")
            text_flat = re.sub(r'\s+', ' ', text)
            text_flat_lower = text_flat.lower()

            keywords = ['conference on', 'seminar on', 'workshop on', 'round table on',
                        'hackathon on', 'symposium on', 'summit on']
            for kw in keywords:
                if kw in text_flat_lower:
                    idx = text_flat_lower.find(kw)
                    # Get text after the keyword
                    after = text_flat[idx + len(kw):].strip()
                    # Clean leading punctuation/quotes
                    after = re.sub(r'^[\s:,.\"\u201c\u201d\'\u2018\u2019]+', '', after)
                    # Extract until we hit a date, a known section header, or 120 chars
                    title = ''
                    for chunk in re.split(r'(?=\d{1,2}(?:st|nd|rd|th)?[\s\-\u2013])', after, maxsplit=1):
                        chunk = chunk.strip()
                        if chunk:
                            title = chunk
                            break
                    # Trim at known stop words
                    for stop in ['Patron', 'About', 'Invitee', 'Registration',
                                 'Objective', 'Organized', 'organised']:
                        stop_idx = title.find(stop)
                        if stop_idx > 10:
                            title = title[:stop_idx].strip()
                    # Clean trailing punctuation
                    title = re.sub(r'[\s:,.\"\u201c\u201d\'\u2018\u2019]+$', '', title)
                    if len(title) > 10:
                        heading = title[:150]
                    break

        if not heading:
            # Check lines for Subject/Title patterns
            lines = [ln.strip() for ln in text.split('\n') if ln.strip()]
            for line in lines[:5]:
                if ":" in line and any(line.lower().startswith(x) for x in ('subject', 'sub', 'title', 're', 'activity')):
                    heading = line.split(":", 1)[1].strip()
                    break

            if not heading and lines:
                # Filter salutations and org names for top line fallback
                for line in lines[:5]:
                    line_l = line.lower()
                    if any(sal in line_l for sal in ('dear', 'respected', 'warm greetings', 'hello', 'hi')):
                        continue
                    # Skip pure organization name lines (short lines with just a name)
                    if any(org in line_l for org in ('university', 'nyas', 'new delhi', 'ahmedabad')) and len(line) < 50:
                        continue
                    if line.strip() in ('&', 'on', 'and'):
                        continue
                    heading = line[:120]
                    break
                if not heading:
                    heading = lines[0][:120]

        result['activity_heading'] = heading if heading else "External Shared Post"

        # 2. Source Classification
        if any(kw in text_lower for kw in ('university', 'college', 'institute', 'gtu', 'academic', 'professor', 'registrar', 'chancellor')):
            result['source'] = 'UNIVERSITY'
        elif any(kw in text_lower for kw in ('firm', 'consultancy', 'partnership', 'association', 'society')):
            result['source'] = 'FIRM'
        else:
            result['source'] = 'COMPANY'

        # 3. Department Classification
        dept_keywords = {
            'CE': ('computer', 'ce', 'software', 'programming', 'computation', 'cse'),
            'IT': ('information technology', 'it', 'network', 'cloud', 'database'),
            'ME': ('mechanical', 'me', 'cad', 'thermodynamics', 'automotive', 'robotics'),
            'CIV': ('civil', 'structure', 'concrete', 'geotechnical', 'construction'),
            'EE': ('electrical', 'ee', 'power', 'grid', 'voltage'),
            'EC': ('electronics', 'communication', 'ec', 'signal', 'antenna', 'telecom')
        }
        found_dept = None
        for dept, keywords in dept_keywords.items():
            if any(kw in text_lower for kw in keywords):
                found_dept = dept
                break
        result['department'] = found_dept

        # 4. Dates Extraction using advanced Natural Language parsing
        MONTHS_MAP = {
            'jan': 1, 'january': 1,
            'feb': 2, 'february': 2,
            'mar': 3, 'march': 3,
            'apr': 4, 'april': 4,
            'may': 5,
            'jun': 6, 'june': 6,
            'jul': 7, 'july': 7,
            'aug': 8, 'august': 8,
            'sep': 9, 'september': 9,
            'oct': 10, 'october': 10,
            'nov': 11, 'november': 11,
            'dec': 12, 'december': 12
        }
        
        start_date = None
        end_date = None
        
        # A. Range match: e.g. "05–06 June 2026" or "05th-06th June, 2026" or "5 to 6 June 2026"
        range_pattern = r'(\d{1,2})(?:st|nd|rd|th)?\s*[-\u2013\u2014]+\s*(\d{1,2})(?:st|nd|rd|th)?\s+(January|February|March|April|May|June|July|August|September|October|November|December|Jan|Feb|Mar|Apr|Jun|Jul|Aug|Sep|Oct|Nov|Dec),?\s+(\d{4})'
        range_match = re.search(range_pattern, text, re.IGNORECASE)
        if range_match:
            d1, d2, m_name, y = range_match.groups()
            m = MONTHS_MAP.get(m_name.lower())
            if m:
                start_date = f"{int(y):04d}-{m:02d}-{int(d1):02d}"
                end_date = f"{int(y):04d}-{m:02d}-{int(d2):02d}"
        
        if not start_date:
            # B. Single dates collection
            single_pattern_1 = r'(\d{1,2})(?:st|nd|rd|th)?\s+(?:of\s+)?(January|February|March|April|May|June|July|August|September|October|November|December|Jan|Feb|Mar|Apr|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+(\d{4})'
            single_pattern_2 = r'(January|February|March|April|May|June|July|August|September|October|November|December|Jan|Feb|Mar|Apr|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+(\d{1,2})(?:st|nd|rd|th)?(?:,\s*|\s+)(\d{4})'
            
            found_dates = []
            
            for match in re.finditer(single_pattern_1, text, re.IGNORECASE):
                d, m_name, y = match.groups()
                m = MONTHS_MAP.get(m_name.lower())
                if m:
                    found_dates.append((int(y), m, int(d)))
                    
            for match in re.finditer(single_pattern_2, text, re.IGNORECASE):
                m_name, d, y = match.groups()
                m = MONTHS_MAP.get(m_name.lower())
                if m:
                    found_dates.append((int(y), m, int(d)))
            
            # C. Standard date regex fallback (YYYY-MM-DD, DD-MM-YYYY, DD/MM/YYYY)
            date_patterns = [
                r'(\d{4}-\d{2}-\d{2})',
                r'(\d{2}-\d{2}-\d{4})',
                r'(\d{2}/\d{2}/\d{4})'
            ]
            for pattern in date_patterns:
                for m in re.findall(pattern, text):
                    try:
                        if '-' in m:
                            parts = m.split('-')
                            if len(parts[0]) == 4:
                                dt = datetime.strptime(m, '%Y-%m-%d').date()
                            else:
                                dt = datetime.strptime(m, '%d-%m-%d').date()
                        else:
                            dt = datetime.strptime(m, '%d/%m/%Y').date()
                        found_dates.append((dt.year, dt.month, dt.day))
                    except ValueError:
                        pass
                        
            # Sort unique parsed dates
            unique_dates = sorted(list(set(found_dates)))
            formatted_dates = [f"{y:04d}-{m:02d}-{d:02d}" for y, m, d in unique_dates]
            
            if len(formatted_dates) >= 2:
                start_date = formatted_dates[0]
                end_date = formatted_dates[-1]
            elif len(formatted_dates) == 1:
                if any(kw in text_lower for kw in ('deadline', 'end', 'due', 'until', 'close', 'last date')):
                    end_date = formatted_dates[0]
                else:
                    start_date = formatted_dates[0]

        result['start_date'] = start_date
        result['end_date'] = end_date

        # 5. Summary Generation (Salutation-aware, smart truncate)
        sentences = re.split(r'(?<=[.!?])\s+', text)
        valid_sentences = []
        
        salutation_pattern = re.compile(
            r'^\s*(?:dear|respected|hello|hi|warm\s+greetings|greetings|to,)\b|'
            r'\b(?:thanks\s+and\s+regards|warm\s+regards|best\s+regards|regards|sincerely|yours\s+sincerely)\b',
            re.IGNORECASE
        )
        
        for s in sentences:
            s_clean = s.strip()
            if not s_clean:
                continue
            if salutation_pattern.search(s_clean):
                continue
            if len(s_clean) < 40:
                continue
            valid_sentences.append(s_clean)
            
        if len(valid_sentences) >= 2:
            summary = ' '.join(valid_sentences[:2])
        elif valid_sentences:
            summary = valid_sentences[0]
        else:
            summary = "Notice shared by the Principal."
            
        # Clean word-boundary truncation
        if len(summary) > 200:
            truncated = summary[:200]
            last_space = truncated.rfind(' ')
            if last_space > 170:
                summary = truncated[:last_space] + "..."
            else:
                summary = truncated + "..."
                
        result['summary'] = summary

        return result
