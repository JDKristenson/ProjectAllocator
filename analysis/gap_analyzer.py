"""Analyze skill gaps between team capabilities and project requirements."""

from dataclasses import dataclass, field
from extractors.profile_extractor import TeamMemberProfile
from extractors.spec_extractor import ProjectSpec
from .matcher import normalize_skill, skills_match


@dataclass
class SkillCoverage:
    """Coverage status for a single skill."""
    skill: str
    required_by: list[str] = field(default_factory=list)  # Work stream names
    covered_by: list[str] = field(default_factory=list)  # Team member names
    coverage_level: str = "none"  # none, partial, good, strong

    def to_dict(self) -> dict:
        return {
            "skill": self.skill,
            "required_by": self.required_by,
            "covered_by": self.covered_by,
            "coverage_level": self.coverage_level
        }


@dataclass
class GapAnalysis:
    """Complete gap analysis for a project."""
    all_required_skills: list[str] = field(default_factory=list)
    skill_coverage: list[SkillCoverage] = field(default_factory=list)
    uncovered_skills: list[str] = field(default_factory=list)
    partially_covered: list[str] = field(default_factory=list)
    well_covered: list[str] = field(default_factory=list)
    team_strengths: list[str] = field(default_factory=list)  # Skills beyond requirements

    def to_dict(self) -> dict:
        return {
            "all_required_skills": self.all_required_skills,
            "skill_coverage": [sc.to_dict() for sc in self.skill_coverage],
            "uncovered_skills": self.uncovered_skills,
            "partially_covered": self.partially_covered,
            "well_covered": self.well_covered,
            "team_strengths": self.team_strengths
        }


def analyze_gaps(
    profiles: list[TeamMemberProfile],
    project_spec: ProjectSpec
) -> GapAnalysis:
    """
    Analyze skill gaps between team and project requirements.

    Args:
        profiles: List of team member profiles
        project_spec: Project specification

    Returns:
        GapAnalysis with coverage details
    """
    # Collect all required skills from work streams
    required_skills_map: dict[str, list[str]] = {}  # skill -> [work_streams]

    for ws in project_spec.work_streams:
        for skill in ws.required_skills:
            normalized = normalize_skill(skill)
            if normalized not in required_skills_map:
                required_skills_map[normalized] = []
            required_skills_map[normalized].append(ws.name)

    # Also include critical skills
    for skill in project_spec.critical_skills:
        normalized = normalize_skill(skill)
        if normalized not in required_skills_map:
            required_skills_map[normalized] = ["Critical"]

    # Collect all team skills
    team_skills_map: dict[str, list[str]] = {}  # skill -> [team_members]

    for profile in profiles:
        all_skills = profile.skills + profile.strengths
        for skill in all_skills:
            normalized = normalize_skill(skill)
            if normalized not in team_skills_map:
                team_skills_map[normalized] = []
            team_skills_map[normalized].append(profile.name)

    # Analyze coverage
    skill_coverage = []
    uncovered = []
    partial = []
    well_covered = []

    for req_skill, work_streams in required_skills_map.items():
        # Find team members who cover this skill
        covered_by = []
        for team_skill, members in team_skills_map.items():
            if skills_match(req_skill, team_skill):
                covered_by.extend(members)

        covered_by = list(set(covered_by))  # Dedupe

        # Determine coverage level
        if len(covered_by) == 0:
            level = "none"
            uncovered.append(req_skill)
        elif len(covered_by) == 1:
            level = "partial"
            partial.append(req_skill)
        elif len(covered_by) == 2:
            level = "good"
            well_covered.append(req_skill)
        else:
            level = "strong"
            well_covered.append(req_skill)

        skill_coverage.append(SkillCoverage(
            skill=req_skill,
            required_by=work_streams,
            covered_by=covered_by,
            coverage_level=level
        ))

    # Find team strengths (skills not required but available)
    team_strengths = []
    for team_skill in team_skills_map.keys():
        is_required = False
        for req_skill in required_skills_map.keys():
            if skills_match(team_skill, req_skill):
                is_required = True
                break
        if not is_required:
            team_strengths.append(team_skill)

    return GapAnalysis(
        all_required_skills=list(required_skills_map.keys()),
        skill_coverage=skill_coverage,
        uncovered_skills=uncovered,
        partially_covered=partial,
        well_covered=well_covered,
        team_strengths=team_strengths[:10]  # Limit to top 10
    )
