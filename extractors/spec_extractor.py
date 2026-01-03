"""Extract structured project specifications using Claude API."""

import json
from dataclasses import dataclass, field
from anthropic import Anthropic


@dataclass
class WorkStream:
    """A work stream within a project."""
    name: str
    description: str = ""
    required_skills: list[str] = field(default_factory=list)
    priority: str = "medium"  # high, medium, low

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "description": self.description,
            "required_skills": self.required_skills,
            "priority": self.priority
        }


@dataclass
class ProjectSpec:
    """Structured representation of a project specification."""
    project_name: str
    source_file: str
    description: str = ""
    work_streams: list[WorkStream] = field(default_factory=list)
    timeline: str = ""
    critical_skills: list[str] = field(default_factory=list)
    key_deliverables: list[str] = field(default_factory=list)
    stakeholders: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "project_name": self.project_name,
            "source_file": self.source_file,
            "description": self.description,
            "work_streams": [ws.to_dict() for ws in self.work_streams],
            "timeline": self.timeline,
            "critical_skills": self.critical_skills,
            "key_deliverables": self.key_deliverables,
            "stakeholders": self.stakeholders
        }


SPEC_EXTRACTION_PROMPT = """Analyze this project specification document and extract structured information.

<document>
{document_text}
</document>

Extract the following information in JSON format:
{{
    "project_name": "Name or title of the project",
    "description": "Brief description of the project objectives",
    "work_streams": [
        {{
            "name": "Name of the work stream",
            "description": "What this work stream involves",
            "required_skills": ["Skills needed for this work stream"],
            "priority": "high/medium/low"
        }}
    ],
    "timeline": "Overall project timeline if mentioned",
    "critical_skills": ["Most important skills for project success"],
    "key_deliverables": ["Main outputs or deliverables expected"],
    "stakeholders": ["Key stakeholders or client contacts mentioned"]
}}

Infer work streams from the project structure, phases, or areas of work mentioned.
If explicit work streams aren't defined, create logical groupings based on the work described.

Common work stream patterns include:
- Strategy/Planning
- Research/Analysis
- Design/Development
- Implementation/Execution
- Change Management/Training
- Communications
- Governance/PMO

Return ONLY the JSON object, no additional text."""


def extract_project_spec(document_text: str, source_file: str, client: Anthropic) -> ProjectSpec:
    """
    Extract a structured project specification from document text using Claude.

    Args:
        document_text: The raw text content from the document
        source_file: Name of the source file (for reference)
        client: Anthropic client instance

    Returns:
        ProjectSpec with extracted information
    """
    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=3000,
        messages=[
            {
                "role": "user",
                "content": SPEC_EXTRACTION_PROMPT.format(document_text=document_text)
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
        # Fallback: create minimal spec
        data = {
            "project_name": "Unknown Project",
            "description": "",
            "work_streams": [],
            "timeline": "",
            "critical_skills": [],
            "key_deliverables": [],
            "stakeholders": []
        }

    # Convert work_streams dicts to WorkStream objects
    work_streams = []
    for ws_data in data.get("work_streams", []):
        work_streams.append(WorkStream(
            name=ws_data.get("name", "Unnamed"),
            description=ws_data.get("description", ""),
            required_skills=ws_data.get("required_skills", []),
            priority=ws_data.get("priority", "medium")
        ))

    return ProjectSpec(
        project_name=data.get("project_name", "Unknown Project"),
        source_file=source_file,
        description=data.get("description", ""),
        work_streams=work_streams,
        timeline=data.get("timeline", ""),
        critical_skills=data.get("critical_skills", []),
        key_deliverables=data.get("key_deliverables", []),
        stakeholders=data.get("stakeholders", [])
    )
