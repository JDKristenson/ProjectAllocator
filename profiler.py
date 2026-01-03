#!/usr/bin/env python3
"""
TeamProfiler - Analyze team profiles against project requirements.

Usage:
    python profiler.py
    python profiler.py --team ./my_team --project ./my_project
    python profiler.py --output ./reports/analysis.html
"""

import argparse
import sys
import webbrowser
from pathlib import Path
from datetime import datetime

from dotenv import load_dotenv
import os

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from anthropic import Anthropic

from parsers import parse_pdf, parse_docx, parse_text
from extractors import extract_profile, extract_project_spec
from analysis import calculate_match_scores, analyze_gaps
from report import generate_report


def parse_document(file_path: Path) -> str:
    """Parse a document based on its extension."""
    suffix = file_path.suffix.lower()

    if suffix == '.pdf':
        return parse_pdf(file_path)
    elif suffix == '.docx':
        return parse_docx(file_path)
    elif suffix in ['.txt', '.md', '.markdown']:
        return parse_text(file_path)
    else:
        # Try as text
        return parse_text(file_path)


def find_documents(folder: Path) -> list[Path]:
    """Find all supported documents in a folder."""
    supported = {'.pdf', '.docx', '.txt', '.md', '.markdown'}
    docs = []

    for file in folder.iterdir():
        if file.is_file() and file.suffix.lower() in supported:
            docs.append(file)

    return sorted(docs)


def main():
    parser = argparse.ArgumentParser(
        description="Analyze team profiles against project requirements"
    )
    parser.add_argument(
        '--team', '-t',
        type=Path,
        default=Path(__file__).parent / 'team',
        help='Folder containing team member documents (default: ./team)'
    )
    parser.add_argument(
        '--project', '-p',
        type=Path,
        default=Path(__file__).parent / 'project',
        help='Folder containing project specification (default: ./project)'
    )
    parser.add_argument(
        '--output', '-o',
        type=Path,
        default=None,
        help='Output file path (default: ./output/team_analysis.html)'
    )
    parser.add_argument(
        '--no-open',
        action='store_true',
        help='Do not open the report in browser after generation'
    )

    args = parser.parse_args()

    # Load environment
    load_dotenv()
    api_key = os.getenv('ANTHROPIC_API_KEY')

    if not api_key:
        print("Error: ANTHROPIC_API_KEY not found in environment or .env file")
        print("Create a .env file with: ANTHROPIC_API_KEY=your-key-here")
        sys.exit(1)

    # Initialize Anthropic client
    client = Anthropic(api_key=api_key)

    # Check folders exist
    if not args.team.exists():
        print(f"Error: Team folder not found: {args.team}")
        print("Create the folder and add resume/profile documents.")
        sys.exit(1)

    if not args.project.exists():
        print(f"Error: Project folder not found: {args.project}")
        print("Create the folder and add project specification document(s).")
        sys.exit(1)

    # Find documents
    team_docs = find_documents(args.team)
    project_docs = find_documents(args.project)

    if not team_docs:
        print(f"Error: No documents found in {args.team}")
        print("Add PDF, DOCX, or TXT files with team member profiles.")
        sys.exit(1)

    if not project_docs:
        print(f"Error: No documents found in {args.project}")
        print("Add a PDF, DOCX, or TXT file with the project specification.")
        sys.exit(1)

    print(f"\n{'='*60}")
    print("TeamProfiler - Team Analysis Tool")
    print(f"{'='*60}\n")

    # Process team documents
    print(f"Found {len(team_docs)} team member document(s)")
    profiles = []

    for doc in team_docs:
        print(f"  Processing: {doc.name}...", end=" ", flush=True)
        try:
            text = parse_document(doc)
            profile = extract_profile(text, doc.name, client)
            profiles.append(profile)
            print(f"OK ({profile.name})")
        except Exception as e:
            print(f"FAILED ({e})")

    if not profiles:
        print("\nError: No profiles could be extracted.")
        sys.exit(1)

    # Process project specification (use first document or combine multiple)
    print(f"\nFound {len(project_docs)} project document(s)")

    # Combine all project docs into one spec
    combined_text = ""
    for doc in project_docs:
        print(f"  Processing: {doc.name}...", end=" ", flush=True)
        try:
            text = parse_document(doc)
            combined_text += f"\n\n--- From {doc.name} ---\n\n{text}"
            print("OK")
        except Exception as e:
            print(f"FAILED ({e})")

    if not combined_text.strip():
        print("\nError: Could not read project specification.")
        sys.exit(1)

    print("\nExtracting project requirements...", end=" ", flush=True)
    project_spec = extract_project_spec(combined_text, "combined", client)
    print(f"OK ({project_spec.project_name})")

    # Run analysis
    print("\nAnalyzing matches...", end=" ", flush=True)
    match_results = calculate_match_scores(profiles, project_spec)
    print("OK")

    print("Analyzing gaps...", end=" ", flush=True)
    gap_analysis = analyze_gaps(profiles, project_spec)
    print("OK")

    # Generate report
    if args.output:
        output_path = args.output
    else:
        output_path = Path(__file__).parent / 'output' / 'team_analysis.html'

    print(f"\nGenerating report...", end=" ", flush=True)
    report_path = generate_report(
        profiles=profiles,
        project_spec=project_spec,
        match_results=match_results,
        gap_analysis=gap_analysis,
        output_path=output_path
    )
    print("OK")

    print(f"\n{'='*60}")
    print(f"Report saved: {report_path}")
    print(f"{'='*60}\n")

    # Open in browser
    if not args.no_open:
        print("Opening in browser...")
        webbrowser.open(f'file://{report_path.absolute()}')

    # Summary
    print("\nSummary:")
    print(f"  Team members analyzed: {len(profiles)}")
    print(f"  Work streams identified: {len(project_spec.work_streams)}")
    print(f"  Uncovered skills: {len(gap_analysis.uncovered_skills)}")
    print(f"  Partially covered: {len(gap_analysis.partially_covered)}")


if __name__ == '__main__':
    main()
