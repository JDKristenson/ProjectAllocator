"""Extract structured profile data from resumes and LinkedIn exports using Claude API."""

import json
from dataclasses import dataclass, field
from anthropic import Anthropic


@dataclass
class TeamMemberProfile:
    """Structured representation of a team member's profile."""
    name: str
    source_file: str
    skills: list[str] = field(default_factory=list)
    experience_years: int = 0
    strengths: list[str] = field(default_factory=list)
    industries: list[str] = field(default_factory=list)
    notable_achievements: list[str] = field(default_factory=list)
    current_role: str = ""
    education: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "source_file": self.source_file,
            "skills": self.skills,
            "experience_years": self.experience_years,
            "strengths": self.strengths,
            "industries": self.industries,
            "notable_achievements": self.notable_achievements,
            "current_role": self.current_role,
            "education": self.education
        }


PROFILE_EXTRACTION_PROMPT = """Analyze this resume or professional profile and extract structured information.

<document>
{document_text}
</document>

Extract the following information in JSON format:
{{
    "name": "Full name of the person",
    "skills": ["List of technical and professional skills mentioned"],
    "experience_years": <estimated total years of professional experience as integer>,
    "strengths": ["Key strengths, leadership qualities, or differentiators"],
    "industries": ["Industries they have worked in"],
    "notable_achievements": ["Significant accomplishments or projects"],
    "current_role": "Their most recent or current job title",
    "education": ["Degrees, certifications, or relevant training"]
}}

Be thorough in extracting skills - include both technical skills (Python, Excel, etc.) and soft skills (stakeholder management, team leadership, etc.).

For experience_years, estimate based on work history dates. If unclear, make a reasonable estimate.

Return ONLY the JSON object, no additional text."""


def extract_profile(document_text: str, source_file: str, client: Anthropic) -> TeamMemberProfile:
    """
    Extract a structured profile from document text using Claude.

    Args:
        document_text: The raw text content from the document
        source_file: Name of the source file (for reference)
        client: Anthropic client instance

    Returns:
        TeamMemberProfile with extracted information
    """
    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=2000,
        messages=[
            {
                "role": "user",
                "content": PROFILE_EXTRACTION_PROMPT.format(document_text=document_text)
            }
        ]
    )

    response_text = message.content[0].text

    # Parse the JSON response
    try:
        # Handle potential markdown code blocks
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0]
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0]

        data = json.loads(response_text.strip())
    except json.JSONDecodeError:
        # Fallback: create minimal profile
        data = {
            "name": "Unknown",
            "skills": [],
            "experience_years": 0,
            "strengths": [],
            "industries": [],
            "notable_achievements": [],
            "current_role": "",
            "education": []
        }

    return TeamMemberProfile(
        name=data.get("name", "Unknown"),
        source_file=source_file,
        skills=data.get("skills", []),
        experience_years=data.get("experience_years", 0),
        strengths=data.get("strengths", []),
        industries=data.get("industries", []),
        notable_achievements=data.get("notable_achievements", []),
        current_role=data.get("current_role", ""),
        education=data.get("education", [])
    )
