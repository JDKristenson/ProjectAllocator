"""Match team members to work streams based on skills and experience."""

from dataclasses import dataclass, field
from extractors.profile_extractor import TeamMemberProfile
from extractors.spec_extractor import ProjectSpec, WorkStream


@dataclass
class MatchResult:
    """Result of matching a team member to a work stream."""
    team_member: str
    work_stream: str
    score: int  # 0-100
    matching_skills: list[str] = field(default_factory=list)
    missing_skills: list[str] = field(default_factory=list)
    rationale: str = ""

    def to_dict(self) -> dict:
        return {
            "team_member": self.team_member,
            "work_stream": self.work_stream,
            "score": self.score,
            "matching_skills": self.matching_skills,
            "missing_skills": self.missing_skills,
            "rationale": self.rationale
        }


def normalize_skill(skill: str) -> str:
    """Normalize a skill string for comparison."""
    return skill.lower().strip()


def skills_match(skill1: str, skill2: str) -> bool:
    """Check if two skills match (fuzzy matching)."""
    s1 = normalize_skill(skill1)
    s2 = normalize_skill(skill2)

    # Exact match
    if s1 == s2:
        return True

    # One contains the other
    if s1 in s2 or s2 in s1:
        return True

    # Common variations
    variations = {
        "python": ["python3", "python 3", "python programming"],
        "javascript": ["js", "node", "nodejs", "node.js"],
        "project management": ["pm", "pmp", "project manager"],
        "stakeholder management": ["stakeholder engagement", "client management"],
        "data analysis": ["data analytics", "analytics", "data analyst"],
        "excel": ["ms excel", "microsoft excel", "spreadsheets"],
        "powerpoint": ["ppt", "presentations", "ms powerpoint"],
        "communication": ["communications", "written communication", "verbal communication"],
        "leadership": ["team leadership", "people leadership", "lead"],
        "strategy": ["strategic planning", "strategic thinking", "strategist"],
    }

    for base, alts in variations.items():
        all_forms = [base] + alts
        if s1 in all_forms and s2 in all_forms:
            return True

    return False


def calculate_match_score(profile: TeamMemberProfile, work_stream: WorkStream) -> MatchResult:
    """
    Calculate how well a team member matches a work stream.

    Args:
        profile: Team member's profile
        work_stream: Work stream to match against

    Returns:
        MatchResult with score and details
    """
    required = work_stream.required_skills
    if not required:
        # No specific skills required; everyone scores medium
        return MatchResult(
            team_member=profile.name,
            work_stream=work_stream.name,
            score=50,
            matching_skills=[],
            missing_skills=[],
            rationale="No specific skills defined for this work stream"
        )

    # Find matching skills
    matching = []
    all_member_skills = profile.skills + profile.strengths

    for req_skill in required:
        for member_skill in all_member_skills:
            if skills_match(req_skill, member_skill):
                matching.append(req_skill)
                break

    # Find missing skills
    missing = [s for s in required if s not in matching]

    # Calculate score
    if required:
        base_score = int((len(matching) / len(required)) * 100)
    else:
        base_score = 50

    # Bonus for experience
    exp_bonus = min(profile.experience_years, 10)  # Max 10 bonus points

    # Bonus for industry overlap (would need industry in work_stream, skip for now)

    final_score = min(base_score + exp_bonus, 100)

    # Generate rationale
    if final_score >= 80:
        rationale = f"Strong match: {len(matching)}/{len(required)} required skills"
    elif final_score >= 60:
        rationale = f"Good match: {len(matching)}/{len(required)} required skills"
    elif final_score >= 40:
        rationale = f"Partial match: {len(matching)}/{len(required)} required skills"
    else:
        rationale = f"Limited match: {len(matching)}/{len(required)} required skills"

    return MatchResult(
        team_member=profile.name,
        work_stream=work_stream.name,
        score=final_score,
        matching_skills=matching,
        missing_skills=missing,
        rationale=rationale
    )


def calculate_match_scores(
    profiles: list[TeamMemberProfile],
    project_spec: ProjectSpec
) -> list[MatchResult]:
    """
    Calculate match scores for all team members against all work streams.

    Args:
        profiles: List of team member profiles
        project_spec: Project specification with work streams

    Returns:
        List of MatchResult objects
    """
    results = []

    for profile in profiles:
        for work_stream in project_spec.work_streams:
            result = calculate_match_score(profile, work_stream)
            results.append(result)

    return results


def get_recommended_assignments(
    match_results: list[MatchResult],
    profiles: list[TeamMemberProfile],
    project_spec: ProjectSpec
) -> dict[str, list[str]]:
    """
    Generate recommended work stream assignments.

    Returns a dict mapping work stream names to lists of recommended team members.
    """
    recommendations = {}

    for ws in project_spec.work_streams:
        # Get all matches for this work stream, sorted by score
        ws_matches = [r for r in match_results if r.work_stream == ws.name]
        ws_matches.sort(key=lambda x: x.score, reverse=True)

        # Recommend top matches (score >= 50)
        recommended = [m.team_member for m in ws_matches if m.score >= 50]

        recommendations[ws.name] = recommended

    return recommendations
