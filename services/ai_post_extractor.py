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
        Now includes intelligent content formatting for unstructured text.
        """
        # First, clean and format the full content
        formatted_content = cls._format_full_content(text)

        result = {
            'activity_heading': '',
            'source': 'COMPANY',
            'summary': '',
            'start_date': None,
            'end_date': None,
            'department': None,
            'full_content': formatted_content or text
        }

        if not text or not text.strip():
            return result

        text_lower = text.lower()

        # 1. Heading Extraction
        heading = ""

        # Try multi-line symposium/conference title patterns first
        # e.g. "INTERNATIONAL SYMPOSIUM\nADVANCEMENTS IN COMPOSITES, SPECIALITY FIBRES..."
        event_type_pattern = re.compile(
            r'(?:INTERNATIONAL|NATIONAL|REGIONAL|ANNUAL|GLOBAL)?\s*'
            r'(SYMPOSIUM|CONFERENCE|WORKSHOP|SEMINAR|SUMMIT|HACKATHON|CONCLAVE)'
            r'\s*[\n\r]+\s*(.+?)(?:\n|\d{1,2}\s*[-–—])',
            re.IGNORECASE | re.DOTALL
        )
        event_match = event_type_pattern.search(text)
        if event_match:
            event_type = event_match.group(1).strip()
            title_part = event_match.group(2).strip()
            # Clean up the title
            title_part = re.sub(r'\s+', ' ', title_part).strip()
            if len(title_part) > 10:
                heading = f"International {event_type.title()}: {title_part}"

        # Try to find conference/workshop quotes
        if not heading:
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
            if len(s_clean) < 50:
                continue
            # Skip ALL-CAPS lines (they are headers/section titles)
            if s_clean.upper() == s_clean and len(s_clean) > 5:
                continue
            # Skip lines that are mostly date/venue info
            if re.search(r'\d{1,2}\s*[-–—]\s*\d{1,2}', s_clean):
                continue
            # Skip fragments starting with venue/location words
            if re.match(r'^(?:AUDITORIUM|HALL|VENUE|ROOM)\b',
                        s_clean, re.IGNORECASE):
                continue
            valid_sentences.append(s_clean)
            
        if len(valid_sentences) >= 2:
            summary = ' '.join(valid_sentences[:2])
        elif valid_sentences:
            summary = valid_sentences[0]
        else:
            summary = "Notice shared by the Principal."
            
        # Clean up the summary: join broken line wraps
        summary = re.sub(r'\s+', ' ', summary).strip()
            
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

    # ------------------------------------------------------------------
    # Intelligent Content Formatter
    # ------------------------------------------------------------------

    @classmethod
    def _format_full_content(cls, raw_text: str) -> str:
        """Intelligently restructure raw unstructured text from conference
        flyers, symposium notices, and multi-column PDFs into clean,
        well-organized, readable content.

        This replaces the need for a GPU-based AI model by using advanced
        pattern recognition and section detection heuristics.
        """
        if not raw_text or not raw_text.strip():
            return raw_text

        import re

        # Step 1: Deduplicate — split into lines and detect repeated sections
        all_lines = [ln.strip() for ln in raw_text.split('\n') if ln.strip()]

        # Detect the half-way duplicate by looking for the title repeating
        dedup_lines = []
        first_title_idx = -1
        second_title_idx = -1
        for i, line in enumerate(all_lines):
            line_up = line.upper()
            if ('SYMPOSIUM' in line_up or 'CONFERENCE' in line_up or
                'WORKSHOP' in line_up or 'SEMINAR' in line_up or
                    'SUMMIT' in line_up or 'HACKATHON' in line_up):
                if first_title_idx == -1:
                    first_title_idx = i
                elif i > first_title_idx + 5:
                    # Check if lines after this match the beginning
                    # (duplicate section detected)
                    match_count = 0
                    for j in range(min(5, len(all_lines) - i)):
                        if (i + j < len(all_lines) and
                                first_title_idx + j < len(all_lines)):
                            if (all_lines[i + j].lower() ==
                                    all_lines[first_title_idx + j].lower()):
                                match_count += 1
                    if match_count >= 3:
                        second_title_idx = i
                        break

        if second_title_idx > 0:
            # Keep only the first occurrence, but also grab any unique
            # trailing content after the duplicate section
            first_section = all_lines[:second_title_idx]
            second_section = all_lines[second_title_idx:]

            # Find lines in the second section that are NOT in the first
            first_set = set(ln.lower().strip() for ln in first_section)
            extra_lines = []
            for ln in second_section:
                if ln.lower().strip() not in first_set and ln.strip():
                    extra_lines.append(ln)

            dedup_lines = first_section + extra_lines
        else:
            dedup_lines = all_lines

        deduped = '\n'.join(dedup_lines)

        # Step 2: Detect if this is an event/symposium type document
        text_lower = deduped.lower()
        is_event = any(kw in text_lower for kw in (
            'symposium', 'conference', 'workshop', 'seminar', 'summit',
            'hackathon', 'conclave', 'webinar', 'congress'
        ))

        if not is_event:
            return cls._basic_format(deduped)

        # Step 3: Extract structured sections for event documents

        # 3a. Event Title — look for the event type keyword + next line
        event_title = ''
        event_type_match = re.search(
            r'(?:INTERNATIONAL|NATIONAL|REGIONAL|ANNUAL|GLOBAL)?\s*'
            r'(SYMPOSIUM|CONFERENCE|WORKSHOP|SEMINAR|SUMMIT|HACKATHON|CONCLAVE)',
            deduped, re.IGNORECASE
        )
        if event_type_match:
            # The title is usually on the next line(s) after the event type
            after_pos = event_type_match.end()
            remaining = deduped[after_pos:after_pos + 300]
            # Get lines until we hit a date or known delimiter
            title_lines = []
            for ln in remaining.split('\n'):
                ln = ln.strip()
                if not ln:
                    continue
                # Stop at date patterns or venue markers
                if re.match(r'\d{1,2}\s*[-–—]', ln):
                    break
                if '|' in ln and re.search(r'\d{4}', ln):
                    break
                title_lines.append(ln)
                if len(title_lines) >= 2:
                    break
            if title_lines:
                event_type_str = event_type_match.group(0).strip()
                title_text = ' '.join(title_lines)
                event_title = f"{event_type_str}: {title_text}"
            else:
                event_title = event_type_match.group(0).strip()

        # 3b. Date & Venue
        date_venue = ''
        date_venue_match = re.search(
            r'(\d{1,2}\s*[-–—]\s*\d{1,2}\s+'
            r'(?:January|February|March|April|May|June|July|August|'
            r'September|October|November|December|Jan|Feb|Mar|Apr|'
            r'Jun|Jul|Aug|Sep|Oct|Nov|Dec),?\s*\d{4})',
            deduped, re.IGNORECASE
        )
        if date_venue_match:
            date_str = date_venue_match.group(1).strip()
            after_date = deduped[date_venue_match.end():
                                  date_venue_match.end() + 200]
            venue_match = re.search(r'[|,]\s*(.+?)(?:\n|$)', after_date)
            if venue_match:
                venue = venue_match.group(1).strip()
                date_venue = f"{date_str} | {venue}"
            else:
                date_venue = date_str

        # 3c. Theme
        theme = ''
        theme_match = re.search(
            r'[Tt]heme\s*:\s*(.+?)(?:\n|$)', deduped)
        if theme_match:
            theme = theme_match.group(1).strip()

        # 3d. Description — extract coherent sentences from the text
        description = ''
        # Find the main descriptive paragraph by looking for sentences
        # that contain lowercase words (not ALL-CAPS section headers)
        # Stop at known section markers
        section_markers = re.compile(
            r'key\s+focus|who\s+should|for\s+inquir|contact|'
            r'registration|delegates|networking|250\+',
            re.IGNORECASE
        )
        desc_sentences = []
        for ln in dedup_lines:
            # Skip ALL-CAPS lines (headers), very short lines, date lines
            if ln.upper() == ln and len(ln) > 5:
                continue
            if len(ln) < 40:
                continue
            if re.match(r'\d{1,2}\s*[-–—]', ln):
                continue
            if ln.startswith('Theme:'):
                continue
            # Stop at section markers
            if section_markers.search(ln):
                break
            # Skip lines that contain emails or phone numbers
            if re.search(r'@|\+91|\d{5}\s*\d{5}', ln):
                continue
            # This looks like a content sentence
            desc_sentences.append(ln)

        if desc_sentences:
            # Join broken sentences
            raw_desc = ' '.join(desc_sentences)
            # Clean up double spaces
            raw_desc = re.sub(r'\s+', ' ', raw_desc).strip()
            description = raw_desc

        # 3e. Key Focus Areas — scan for ALL-CAPS "X & Y" patterns
        # In multi-column flyers, focus areas appear as ALL-CAPS lines
        # with "&" (e.g., "AEROSPACE & DEFENCE", "ELECTRIC MOBILITY & EVS")
        # They may be interleaved with audience items, so scan all lines
        _SKIP_PATTERNS = (
            'KEY FOCUS', 'WHO SHOULD',
            'INTERNATIONAL', 'SYMPOSIUM', 'CONFERENCE',
            'ADVANCEMENTS', 'SPECIALITY', 'COMPOSITES',
        )
        # Patterns that might be appended from adjacent columns
        _SPLIT_SUFFIXES = re.compile(
            r'\s+(?:FOR\s+INQUIR\w*|CONTACT|REGISTRATION|WHO\s+SHOULD)',
            re.IGNORECASE
        )
        focus_areas = []
        for ln in dedup_lines:
            ln = ln.strip()
            if not (ln.upper() == ln and '&' in ln and len(ln) > 10):
                continue
            if any(skip in ln.upper() for skip in _SKIP_PATTERNS):
                continue
            # Split off appended section headers from adjacent columns
            split_match = _SPLIT_SUFFIXES.search(ln)
            if split_match:
                ln = ln[:split_match.start()].strip()
            # Clean trailing fragments like "&" on its own
            cleaned = ln.strip().rstrip('&').strip()
            if cleaned and len(cleaned) > 8:
                focus_areas.append(cleaned.title())

        # 3f. Target Audience
        audience = []
        who_section_start = re.search(
            r'who\s+should\s+attend', text_lower)
        if who_section_start:
            after_who = deduped[who_section_start.end():]
            # Collect attendee types — mixed-case lines that look like
            # role descriptions
            for ln in after_who.split('\n'):
                ln = ln.strip()
                if not ln:
                    continue
                if re.search(r'for\s+inquir|contact|key\s+focus',
                             ln, re.IGNORECASE):
                    break
                # Skip ALL-CAPS focus area items
                if ln.upper() == ln and '&' in ln:
                    continue
                # Skip phone numbers and emails
                if re.search(r'@|\+91|\d{5}', ln):
                    continue
                # Skip known non-audience lines
                if any(skip in ln.upper() for skip in
                       ('JYOTI', 'TASKAR', 'SUSTAINABILITY')):
                    continue
                # Lines with roles/titles
                clean_ln = re.sub(r'\s+', ' ', ln).strip()
                if clean_ln and len(clean_ln) > 5 and len(clean_ln) < 60:
                    audience.append(clean_ln)

        # 3g. Contact Information
        contacts = []
        phones = list(set(re.findall(
            r'(\+91\s*\d{5}\s*\d{5})', deduped)))
        emails = list(set(re.findall(
            r'[\w.+-]+@[\w-]+\.[\w.]+', deduped)))

        # Find contact names — look for proper-case names (2-3 words)
        # that appear near phone or email lines
        _NON_NAME_WORDS = {'manufacturers', 'industry', 'leaders',
                           'academia', 'startups', 'innovators',
                           'material', 'technology', 'solution',
                           'providers', 'organizations', 'drones',
                           'sustainability', 'cities', 'smart'}
        for i, ln in enumerate(dedup_lines):
            ln_stripped = ln.strip()
            # Must be 2-3 proper words, all starting with uppercase
            words = ln_stripped.split()
            if not (2 <= len(words) <= 3):
                continue
            if not all(w[0].isupper() for w in words):
                continue
            # Filter out known non-name words
            if any(w.lower() in _NON_NAME_WORDS for w in words):
                continue
            if len(ln_stripped) < 5 or len(ln_stripped) > 35:
                continue
            # Check if nearby lines (prev/next 2) have phone/email
            nearby = ' '.join(
                dedup_lines[max(0, i - 1):min(len(dedup_lines), i + 3)])
            if re.search(r'@|\+91|\d{5}\s*\d{5}', nearby):
                contacts.append(ln_stripped)

        # Step 4: Build the formatted output
        output_parts = []

        if event_title:
            output_parts.append(f"\U0001f4cc {event_title}")
            output_parts.append('')

        if date_venue:
            output_parts.append(f"\U0001f4c5 Date & Venue: {date_venue}")
            output_parts.append('')

        if theme:
            output_parts.append(
                f"\U0001f3af Theme: {theme}")
            output_parts.append('')

        if description:
            output_parts.append(
                '\u2501' * 40)
            output_parts.append(
                '\U0001f4dd ABOUT THE EVENT')
            output_parts.append(
                '\u2501' * 40)
            output_parts.append('')
            # Word-wrap description at ~80 chars for readability
            words = description.split()
            line = ''
            for word in words:
                if len(line) + len(word) + 1 > 80:
                    output_parts.append(line)
                    line = word
                else:
                    line = f"{line} {word}" if line else word
            if line:
                output_parts.append(line)

        if focus_areas:
            output_parts.append('')
            output_parts.append('\u2501' * 40)
            output_parts.append(
                '\U0001f52c KEY FOCUS AREAS')
            output_parts.append('\u2501' * 40)
            for area in focus_areas:
                output_parts.append(f"  \u2022 {area}")

        if audience:
            output_parts.append('')
            output_parts.append('\u2501' * 40)
            output_parts.append(
                '\U0001f465 WHO SHOULD ATTEND')
            output_parts.append('\u2501' * 40)
            for item in audience:
                output_parts.append(f"  \u2022 {item}")

        if contacts or phones or emails:
            output_parts.append('')
            output_parts.append('\u2501' * 40)
            output_parts.append(
                '\U0001f4de CONTACT INFORMATION')
            output_parts.append('\u2501' * 40)
            for name in contacts:
                output_parts.append(f"  Contact: {name}")
            for phone in phones:
                output_parts.append(
                    f"  Phone: {phone.strip()}")
            for email in emails:
                output_parts.append(f"  Email: {email}")

        # If we extracted meaningful sections, return formatted output
        if len(output_parts) > 3:
            return '\n'.join(output_parts)

        # Otherwise, return basic formatted version
        return cls._basic_format(deduped)

    @classmethod
    def _basic_format(cls, text: str) -> str:
        """Basic text formatting: fix broken lines, remove excess
        whitespace, and deduplicate lines."""
        import re

        if not text:
            return text

        lines = text.split('\n')
        cleaned = []
        seen_lines = set()
        for line in lines:
            stripped = line.strip()
            if stripped:
                key = stripped.lower()
                if key not in seen_lines:
                    seen_lines.add(key)
                    cleaned.append(stripped)
            elif cleaned and cleaned[-1] != '':
                cleaned.append('')

        # Remove trailing empty lines
        while cleaned and cleaned[-1] == '':
            cleaned.pop()

        return '\n'.join(cleaned)
