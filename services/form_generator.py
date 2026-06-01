"""
GTU-ITR R&D & IIC Portal - Smart Heuristic Form Generator Service
"""
import re

class FormGenerator:
    """Auto-detects context keywords in a post and returns recommended custom registration form fields."""

    @staticmethod
    def generate_fields(post):
        """
        Analyze post title and summary to generate custom fields.
        Returns a list of field definition dicts:
        [
            {"id": "field_id", "label": "Field Label", "type": "text|email|tel|number|select|textarea", "required": True/False, "options": [...], "is_default": False}
        ]
        """
        title = (post.title or "").lower()
        summary = (post.summary or "").lower()
        content = (post.full_content or "").lower()
        text = f"{title} {summary} {content}"

        custom_fields = []

        # 1. Placement / Job / Career recruitment keywords
        if any(w in text for w in ["placement", "job", "career", "recruit", "interview", "hiring", "company", "tcs"]):
            custom_fields.append({
                "id": "current_cgpa",
                "label": "Current CGPA (out of 10)",
                "type": "number",
                "required": True,
                "is_default": False
            })
            custom_fields.append({
                "id": "resume_link",
                "label": "Resume Link (GDrive / Dropbox)",
                "type": "text",
                "required": True,
                "is_default": False
            })
            custom_fields.append({
                "id": "branch",
                "label": "Branch / Specialization",
                "type": "select",
                "options": ["Computer Engineering", "Information Technology", "Mechanical Engineering", "Civil Engineering", "Electrical Engineering", "Electronics & Communication"],
                "required": True,
                "is_default": False
            })

        # 2. Hackathon / Project / Competition keywords
        elif any(w in text for w in ["hackathon", "project", "competition", "innovat", "code", "dev", "contest"]):
            custom_fields.append({
                "id": "team_name",
                "label": "Team Name (if registering as team)",
                "type": "text",
                "required": False,
                "is_default": False
            })
            custom_fields.append({
                "id": "github_link",
                "label": "GitHub Profile Link",
                "type": "text",
                "required": False,
                "is_default": False
            })
            custom_fields.append({
                "id": "prior_experience",
                "label": "Programming Languages / Tech Stack Experience",
                "type": "text",
                "required": True,
                "is_default": False
            })

        # 3. Seminar / Workshop / Guest lecture / Bootcamp keywords
        elif any(w in text for w in ["workshop", "seminar", "lecture", "bootcamp", "talk", "training", "expert"]):
            custom_fields.append({
                "id": "branch",
                "label": "Department / Branch",
                "type": "select",
                "options": ["Computer Engineering", "Information Technology", "Mechanical Engineering", "Civil Engineering", "Electrical Engineering", "Electronics & Communication"],
                "required": True,
                "is_default": False
            })
            custom_fields.append({
                "id": "expectations",
                "label": "What do you expect to learn from this workshop?",
                "type": "textarea",
                "required": False,
                "is_default": False
            })

        # Fallback default suggested custom fields if no matches
        if not custom_fields:
            custom_fields.append({
                "id": "branch",
                "label": "Department / Branch",
                "type": "select",
                "options": ["Computer Engineering", "Information Technology", "Mechanical Engineering", "Civil Engineering", "Electrical Engineering", "Electronics & Communication"],
                "required": True,
                "is_default": False
            })
            custom_fields.append({
                "id": "prior_knowledge",
                "label": "Any prior knowledge/experience? (Brief)",
                "type": "text",
                "required": False,
                "is_default": False
            })

        return custom_fields
