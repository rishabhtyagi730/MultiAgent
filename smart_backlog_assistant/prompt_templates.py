"""
Prompt templates for AI interactions.
Demonstrates thoughtful prompt engineering with examples and clear instructions.
"""

# System prompt that defines Claude's role and constraints
SYSTEM_PROMPT = """You are an expert engineering manager and product strategist with 10+ years of experience 
converting unstructured requirements into well-organized, actionable backlog items.

Your expertise includes:
- Writing clear, testable user stories
- Identifying hidden requirements from context
- Prioritizing based on business impact and technical complexity
- Organizing work into coherent epics
- Creating acceptance criteria that developers can test

You always respond with valid, properly formatted JSON. You never include markdown code fences in your responses.
Your responses are technically accurate and include realistic details."""


# Main prompt for generating backlog items from raw input
GENERATE_BACKLOG_PROMPT = """Analyze the following meeting notes or requirements document and generate a structured backlog.

INPUT TEXT:
```
{input_text}
```

Your task:
1. Identify the core business requirements and goals
2. Extract specific feature requests and improvements
3. Identify any implicit security, performance, or quality requirements
4. Generate well-structured user stories
5. Organize stories into logical epics

Generate ONLY valid JSON (no markdown fences) with this exact structure:
{{
  "summary": "A 1-2 sentence summary of the overall initiative or goal",
  "key_requirements": [
    "Requirement 1: description",
    "Requirement 2: description"
  ],
  "epics": [
    "Epic 1 Name",
    "Epic 2 Name"
  ],
  "stories": [
    {{
      "id": "STORY-001",
      "title": "As a [role], I want [feature] so that [benefit]",
      "description": "Detailed explanation of what needs to be built and why",
      "acceptance_criteria": [
        "Given context, when action occurs, then result happens",
        "When condition X, then system should Y",
        "User should be able to Z"
      ],
      "priority": "HIGH",
      "epic": "Epic Name",
      "estimated_effort": "5 points"
    }}
  ]
}}

CRITICAL REQUIREMENTS:
- Generate 3-6 user stories based on input complexity
- Each story MUST have 3-4 acceptance criteria
- Priorities must be: CRITICAL, HIGH, MEDIUM, or LOW
- Stories should be independent where possible
- Use specific, testable acceptance criteria
- ID format: STORY-001, STORY-002, etc.

EXAMPLES OF GOOD ACCEPTANCE CRITERIA:
❌ Bad: "System should be fast"
✅ Good: "Login completes within 2 seconds for 95% of users on 4G connection"

❌ Bad: "User can search"
✅ Good: "When user enters search term and clicks Find, results display within 1 second"

Generate the JSON now:"""


# Prompt for analyzing priority and dependencies
ANALYZE_PRIORITY_PROMPT = """Review these user stories and refine their priorities based on:
1. Business impact (revenue, user satisfaction, retention)
2. Technical dependencies (must some stories complete first?)
3. Risk mitigation (are there security/stability risks?)
4. Complexity vs impact ratio

STORIES:
{stories_json}

Return ONLY valid JSON with updated priorities and optional dependencies field.
Format the same as input but with refined "priority" values and added "dependencies": ["STORY-002"] where applicable.

Respond with JSON only, no explanation:"""


# Prompt for validating and improving stories
VALIDATE_STORIES_PROMPT = """Review these user stories for quality and completeness.
Check that each story:
- Has a clear user role and benefit
- Acceptance criteria are specific and testable (not vague)
- Priority makes sense in context
- Is focused on one feature/capability

STORIES:
{stories_json}

For each story with issues, suggest improvements. Return JSON with:
{{
  "stories": [improved stories],
  "issues_found": ["Issue 1", "Issue 2"],
  "quality_score": 8.5
}}

Return JSON only:"""


# Prompt for extracting requirements from meeting notes
EXTRACT_REQUIREMENTS_PROMPT = """Extract all explicit and implicit requirements from these meeting notes.
Look for:
- Feature requests
- Bug reports
- Performance concerns
- Security considerations
- User experience improvements
- Technical debt or architecture improvements

NOTES:
{input_text}

Return ONLY valid JSON:
{{
  "explicit_requirements": ["Requirement 1", "Requirement 2"],
  "implicit_requirements": ["Hidden requirement based on context"],
  "risks_or_concerns": ["Potential issue to address"],
  "dependencies": ["Thing that must happen first"]
}}"""


def format_generate_backlog_prompt(input_text: str) -> str:
    """Format the main backlog generation prompt with input."""
    return GENERATE_BACKLOG_PROMPT.format(input_text=input_text)


def format_analyze_priority_prompt(stories_json: str) -> str:
    """Format the priority analysis prompt."""
    return ANALYZE_PRIORITY_PROMPT.format(stories_json=stories_json)


def format_validate_stories_prompt(stories_json: str) -> str:
    """Format the validation prompt."""
    return VALIDATE_STORIES_PROMPT.format(stories_json=stories_json)


def format_extract_requirements_prompt(input_text: str) -> str:
    """Format the requirements extraction prompt."""
    return EXTRACT_REQUIREMENTS_PROMPT.format(input_text=input_text)


# Configuration for different prompt strategies
PROMPT_CONFIG = {
    "detailed": {
        "description": "Generate comprehensive stories with detailed analysis",
        "include_validation": True,
        "include_priority_analysis": True,
        "max_stories": 8
    },
    "fast": {
        "description": "Quick story generation, minimal analysis",
        "include_validation": False,
        "include_priority_analysis": False,
        "max_stories": 5
    },
    "balanced": {
        "description": "Standard generation with essential validation",
        "include_validation": True,
        "include_priority_analysis": False,
        "max_stories": 6
    }
}
