# Project Allocator

Analyze team member profiles against project requirements to optimize work stream assignments and identify skill gaps.

## What It Does

Drop resumes/profiles and project specs into folders, run the tool, and get an HTML report with:
- **Skills heatmap**: Visual matrix of team-to-work-stream fit scores
- **Recommended assignments**: Best-fit team members for each work stream
- **Gap analysis**: Uncovered and single-point-of-failure skills
- **Team overview**: Skills inventory and experience summary

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Add your API key
echo "ANTHROPIC_API_KEY=your-key-here" > .env

# Add team documents to team/ folder
# Add project spec to project/ folder

# Run analysis
python profiler.py
```

## Folder Structure

```
team/           # Drop team member documents here (PDF, DOCX, TXT)
project/        # Drop project specification here
output/         # Generated reports appear here
```

## Sample Output

The tool generates an interactive HTML report with:
- Color-coded skills matrix (0-100 match scores)
- Recommended assignments per work stream
- Skill gap visualization
- Team capability summary

## Requirements

- Python 3.10+
- Anthropic API key (Claude)

## Future Plans

- Web UI version
- LinkedIn integration
- Multi-project comparison
- PowerPoint export for client delivery
