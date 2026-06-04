# Smart Backlog Assistant - Usage Guide

## Quick Start

### 1. Setup

```bash
# Navigate to project directory
cd smart_backlog_assistant

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Setup environment
cp .env.example .env
# Edit .env and add your Anthropic API key
```

### 2. Basic Usage

```bash
# Process meeting notes
python backlog_generator.py \
  --input samples/standup_notes.txt \
  --output-json results/backlog.json \
  --output-markdown results/backlog.md

# Process feature request
python backlog_generator.py \
  --input samples/feature_request.json \
  --mode balanced \
  --verbose

# Fast generation without validation
python backlog_generator.py \
  --input samples/requirements.txt \
  --mode fast \
  --no-validate
```

### 3. Run Tests

```bash
# Run all tests
pytest test_generator.py -v

# Run specific test class
pytest test_generator.py::TestUserStory -v

# Run with coverage
pytest test_generator.py --cov=. --cov-report=html
```

## Command-Line Options

```
--input FILE              Input file (txt or json) - REQUIRED
--output-json FILE        Save JSON output (default: backlog_output.json)
--output-markdown FILE    Save Markdown output (default: backlog_output.md)
--mode {fast,balanced,detailed}
                          Generation mode (default: balanced)
--no-validate             Skip story validation step
--model MODEL             Claude model to use
--verbose                 Enable detailed logging
```

## Generation Modes

### Fast Mode
- Generates 3-5 user stories
- No validation or priority analysis
- Best for quick iterations
- Lowest API cost
- ~30-40 seconds

### Balanced Mode (Default)
- Generates 5-6 user stories
- Validates stories for quality
- No priority analysis
- Good balance of speed and quality
- ~60-90 seconds

### Detailed Mode
- Generates 6-8 user stories
- Full validation and improvement
- Priority analysis and optimization
- Highest quality output
- ~120-150 seconds

## Input Formats

### Text File (.txt)
Plain text meeting notes or requirements. Examples:

```
Daily Standup - June 4, 2026

Completed:
- Fixed login bug
- Updated documentation

In Progress:
- Implementing OAuth 2.0
- Performance optimization

Blockers:
- Security audit findings need review
```

### JSON File (.json)
Structured input with multiple fields:

```json
{
  "title": "Feature Request: Dark Mode",
  "priority": "HIGH",
  "description": "Users want dark theme support...",
  "requirements": [...],
  "acceptance_criteria": [...]
}
```

## Output Formats

### JSON Output
Machine-readable format with structured stories:

```json
{
  "summary": "Authentication system modernization",
  "key_requirements": [...],
  "stories": [
    {
      "id": "STORY-001",
      "title": "As a user, I want...",
      "description": "...",
      "acceptance_criteria": [...],
      "priority": "HIGH",
      "epic": "Authentication"
    }
  ],
  "epics": [...],
  "generated_at": "2026-06-04T22:15:00",
  "model_used": "claude-3-5-sonnet-20241022"
}
```

### Markdown Output
Human-readable format for sharing with team:

```markdown
# Backlog Summary

Authentication system modernization

## Key Requirements
- Requirement 1
- Requirement 2

## Epics
- Authentication
- Security

## User Stories
### Authentication
**[HIGH] Fix OAuth vulnerability** (ID: STORY-001)

Detailed description...

**Acceptance Criteria:**
- [ ] OAuth integration working
- [ ] Security tests pass
```

## Real-World Workflow

### Scenario 1: Post-Standup Backlog

```bash
# 1. Save standup notes to file
echo "[Standup notes here]" > standup_2026_06_04.txt

# 2. Generate backlog
python backlog_generator.py \
  --input standup_2026_06_04.txt \
  --output-json backlog_2026_06_04.json \
  --output-markdown backlog_2026_06_04.md \
  --mode balanced

# 3. Review outputs
cat backlog_2026_06_04.md

# 4. Import to Jira/Linear using JSON
cat backlog_2026_06_04.json | jq .
```

### Scenario 2: Feature Request Processing

```bash
# 1. Save customer feature request
cp customer_request.json input_feature.json

# 2. Generate detailed backlog
python backlog_generator.py \
  --input input_feature.json \
  --mode detailed \
  --output-json feature_backlog.json \
  --verbose

# 3. Review with team and commit to version control
git add feature_backlog.json
git commit -m "Add backlog for dark mode feature request"
```

## Understanding the Output

### User Story Quality

✅ **Good Story:**
```
As a user, I want to reset my password so that I can regain access if I forget my credentials

Acceptance Criteria:
- When user clicks "Forgot Password", email is sent to registered address
- Reset link expires after 24 hours
- New password meets complexity requirements (12+ chars, mixed case, numbers)
```

❌ **Poor Story:**
```
User password reset

Acceptance Criteria:
- Works
- Is secure
```

### Priority Interpretation

- **CRITICAL**: Blocks other work or affects users immediately (P0)
- **HIGH**: Important for upcoming release (P1)
- **MEDIUM**: Good to have, reasonable effort (P2)
- **LOW**: Nice to have, lower impact (P3)

## Troubleshooting

### Issue: "API key not found"

```bash
# Make sure .env file exists and has API key
ls -la .env
grep ANTHROPIC_API_KEY .env

# Or set via environment
export ANTHROPIC_API_KEY="sk-ant-..."
```

### Issue: "Invalid JSON response"

The system attempts JSON recovery, but if it fails:

```bash
# Try again with verbose logging
python backlog_generator.py --input file.txt --verbose

# Check logs
tail -f backlog_generator.log
```

### Issue: "Rate limited"

The system has built-in retry logic:

```bash
# Exponential backoff is automatic
# Just re-run the command if it fails
python backlog_generator.py --input file.txt
```

### Issue: "Stories not detailed enough"

```bash
# Use detailed mode for more comprehensive output
python backlog_generator.py --input file.txt --mode detailed
```

## Tips and Best Practices

### Input Tips

1. **Be specific**: Include concrete details in requirements
   - ✅ "Users report 4+ second search times"
   - ❌ "Search is slow"

2. **Include context**: Explain why changes are needed
   - ✅ "47 customers requesting dark mode for evening use"
   - ❌ "Add dark mode"

3. **List priorities**: Help AI understand importance
   - ✅ "CRITICAL: Fix OAuth vulnerability (affects 15% of users)"
   - ❌ "OAuth issue"

### Generation Tips

1. **Match mode to need**:
   - Planning meeting → detailed
   - Quick iteration → fast
   - Production planning → balanced

2. **Validate output**: Always review AI output before using
   - Check story coherence
   - Verify priorities make sense
   - Adjust acceptance criteria as needed

3. **Use markdown output for sharing**: More readable than JSON

### Integration Tips

1. **Store outputs in version control**:
   ```bash
   git add backlog_*.json backlog_*.md
   ```

2. **Create a workflow**:
   - Capture requirements → Generate backlog → Review → Commit

3. **Track over time**: Compare backlog snapshots to see evolution

## Performance Notes

- Fast mode: ~30-40 seconds, ~2000 input tokens
- Balanced mode: ~60-90 seconds, ~3500 input tokens
- Detailed mode: ~120-150 seconds, ~5000 input tokens

## Cost Estimation

Using Claude 3.5 Sonnet:
- Fast mode: ~$0.0005-0.001 per run
- Balanced mode: ~0.001-0.002 per run
- Detailed mode: ~0.002-0.003 per run

## Support and Issues

For bugs or feature requests, see the main README.md
