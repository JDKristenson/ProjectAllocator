"""Generate HTML report with visualizations."""

import json
from pathlib import Path
from datetime import datetime
from jinja2 import Environment, FileSystemLoader
import plotly.graph_objects as go
import plotly.express as px

from extractors.profile_extractor import TeamMemberProfile
from extractors.spec_extractor import ProjectSpec
from analysis.matcher import MatchResult, get_recommended_assignments
from analysis.gap_analyzer import GapAnalysis


# Linear-inspired dark theme
DARK_BG = '#0f1011'
DARK_BORDER = '#26272b'
TEXT_MUTED = '#6b6f82'
TEXT_SECONDARY = '#A1A7C1'
TEXT_PRIMARY = '#f7f8f8'
ACCENT = '#5E6AD2'


def create_skills_heatmap(
    match_results: list[MatchResult],
    profiles: list[TeamMemberProfile],
    project_spec: ProjectSpec
) -> str:
    """Create a heatmap showing team member vs work stream match scores."""
    team_members = [p.name for p in profiles]
    work_streams = [ws.name for ws in project_spec.work_streams]

    # Create score matrix
    scores = []
    for member in team_members:
        row = []
        for ws in work_streams:
            result = next(
                (r for r in match_results if r.team_member == member and r.work_stream == ws),
                None
            )
            row.append(result.score if result else 0)
        scores.append(row)

    # Custom colorscale matching Linear aesthetic
    colorscale = [
        [0.0, '#2a1f1f'],
        [0.3, '#3d2828'],
        [0.5, '#4a3a20'],
        [0.7, '#3a4a2a'],
        [1.0, '#1f3d2a']
    ]

    fig = go.Figure(data=go.Heatmap(
        z=scores,
        x=work_streams,
        y=team_members,
        colorscale=colorscale,
        zmin=0,
        zmax=100,
        text=[[str(s) for s in row] for row in scores],
        texttemplate="%{text}",
        textfont=dict(size=13, color='#f7f8f8'),
        hovertemplate="<b>%{y}</b><br>%{x}<br>Score: %{z}<extra></extra>",
        colorbar=dict(
            tickfont=dict(color='#6b6f82'),
            title=dict(text='Score', font=dict(color='#A1A7C1'))
        )
    ))

    fig.update_layout(
        paper_bgcolor=DARK_BG,
        plot_bgcolor=DARK_BG,
        font=dict(family='-apple-system, BlinkMacSystemFont, Inter, sans-serif', size=12, color=TEXT_SECONDARY),
        title=None,
        height=max(300, len(team_members) * 60 + 80),
        margin=dict(l=140, r=60, t=20, b=60),
        xaxis=dict(gridcolor=DARK_BORDER, linecolor=DARK_BORDER, tickfont=dict(color=TEXT_MUTED), tickangle=-35),
        yaxis=dict(gridcolor=DARK_BORDER, linecolor=DARK_BORDER, tickfont=dict(color=TEXT_MUTED), autorange='reversed')
    )

    return fig.to_html(full_html=False, include_plotlyjs='cdn')


def create_gap_chart(gap_analysis: GapAnalysis) -> str:
    """Create a bar chart showing skill coverage levels."""
    coverage_counts = {
        "Uncovered": len(gap_analysis.uncovered_skills),
        "Partial": len(gap_analysis.partially_covered),
        "Well Covered": len(gap_analysis.well_covered)
    }

    # Linear-inspired colors
    colors = ['#f87171', '#fbbf24', '#4ade80']

    fig = go.Figure(data=[
        go.Bar(
            x=list(coverage_counts.keys()),
            y=list(coverage_counts.values()),
            marker_color=colors,
            text=list(coverage_counts.values()),
            textposition='outside',
            textfont=dict(color='#f7f8f8', size=14),
            marker=dict(
                line=dict(width=0)
            )
        )
    ])

    fig.update_layout(
        paper_bgcolor=DARK_BG,
        plot_bgcolor=DARK_BG,
        font=dict(family='-apple-system, BlinkMacSystemFont, Inter, sans-serif', size=12, color=TEXT_SECONDARY),
        title=None,
        height=280,
        showlegend=False,
        bargap=0.4,
        xaxis=dict(gridcolor=DARK_BORDER, linecolor=DARK_BORDER, tickfont=dict(color=TEXT_MUTED)),
        yaxis=dict(gridcolor=DARK_BORDER, linecolor=DARK_BORDER, tickfont=dict(color=TEXT_MUTED))
    )

    return fig.to_html(full_html=False, include_plotlyjs=False)


def create_team_skills_chart(profiles: list[TeamMemberProfile]) -> str:
    """Create a horizontal bar chart showing skills per team member."""
    data = []
    for profile in profiles:
        data.append({
            "name": profile.name,
            "skills": len(profile.skills),
            "experience": profile.experience_years
        })

    fig = go.Figure()

    fig.add_trace(go.Bar(
        y=[d["name"] for d in data],
        x=[d["skills"] for d in data],
        orientation='h',
        marker_color='#5E6AD2',
        text=[d["skills"] for d in data],
        textposition='outside',
        textfont=dict(color='#f7f8f8', size=12),
        marker=dict(line=dict(width=0))
    ))

    fig.update_layout(
        paper_bgcolor=DARK_BG,
        plot_bgcolor=DARK_BG,
        font=dict(family='-apple-system, BlinkMacSystemFont, Inter, sans-serif', size=12, color=TEXT_SECONDARY),
        title=None,
        height=max(200, len(profiles) * 50 + 60),
        showlegend=False,
        margin=dict(l=120, r=40, t=20, b=20),
        xaxis=dict(gridcolor=DARK_BORDER, linecolor=DARK_BORDER, tickfont=dict(color=TEXT_MUTED)),
        yaxis=dict(gridcolor=DARK_BORDER, linecolor=DARK_BORDER, tickfont=dict(color=TEXT_MUTED), autorange='reversed'),
        bargap=0.3
    )

    return fig.to_html(full_html=False, include_plotlyjs=False)


def generate_report(
    profiles: list[TeamMemberProfile],
    project_spec: ProjectSpec,
    match_results: list[MatchResult],
    gap_analysis: GapAnalysis,
    output_path: Path
) -> Path:
    """
    Generate the HTML report.

    Args:
        profiles: Team member profiles
        project_spec: Project specification
        match_results: Matching results
        gap_analysis: Gap analysis results
        output_path: Where to save the report

    Returns:
        Path to the generated report
    """
    # Generate charts
    heatmap_html = create_skills_heatmap(match_results, profiles, project_spec)
    gap_chart_html = create_gap_chart(gap_analysis)
    skills_chart_html = create_team_skills_chart(profiles)

    # Get recommendations
    recommendations = get_recommended_assignments(match_results, profiles, project_spec)

    # Prepare template data
    template_data = {
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "project": project_spec.to_dict(),
        "team_members": [p.to_dict() for p in profiles],
        "match_results": [m.to_dict() for m in match_results],
        "gap_analysis": gap_analysis.to_dict(),
        "recommendations": recommendations,
        "heatmap_html": heatmap_html,
        "gap_chart_html": gap_chart_html,
        "skills_chart_html": skills_chart_html,
    }

    # Load and render template
    template_dir = Path(__file__).parent / "templates"
    env = Environment(loader=FileSystemLoader(template_dir))
    template = env.get_template("report.html")

    html_content = template.render(**template_data)

    # Write output
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(html_content)

    return output_path
