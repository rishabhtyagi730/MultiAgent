"""
Core data models and structures for the Smart Backlog Assistant.
Includes validation and type definitions for all backlog components.
"""

from dataclasses import dataclass, asdict
from typing import List, Optional
from enum import Enum
import json


class PriorityLevel(str, Enum):
    """Priority levels for backlog items."""
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


@dataclass
class AcceptanceCriteria:
    """Individual acceptance criterion."""
    criterion: str
    
    def validate(self) -> bool:
        """Validate criterion is specific and testable."""
        return len(self.criterion.strip()) > 10 and \
               any(keyword in self.criterion.lower() 
                   for keyword in ['when', 'then', 'should', 'must', 'can'])
    
    def to_dict(self):
        return asdict(self)


@dataclass
class UserStory:
    """Represents a single user story with all details."""
    id: str
    title: str
    description: str
    acceptance_criteria: List[str]  # List of criterion strings
    priority: str  # PriorityLevel enum value
    epic: str
    estimated_effort: Optional[str] = None
    dependencies: Optional[List[str]] = None
    
    def validate(self) -> tuple[bool, List[str]]:
        """Validate user story completeness and quality."""
        errors = []
        
        # Check required fields
        if not self.title or len(self.title.strip()) < 5:
            errors.append("Title must be at least 5 characters")
        
        if not self.description or len(self.description.strip()) < 20:
            errors.append("Description must be at least 20 characters")
        
        if not self.acceptance_criteria or len(self.acceptance_criteria) < 2:
            errors.append("Must have at least 2 acceptance criteria")
        
        if self.priority not in [p.value for p in PriorityLevel]:
            errors.append(f"Priority must be one of: {[p.value for p in PriorityLevel]}")
        
        if not self.epic or len(self.epic.strip()) < 3:
            errors.append("Epic must be specified and at least 3 characters")
        
        return len(errors) == 0, errors
    
    def to_dict(self):
        """Convert story to dictionary for JSON serialization."""
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'acceptance_criteria': self.acceptance_criteria,
            'priority': self.priority,
            'epic': self.epic,
            'estimated_effort': self.estimated_effort,
            'dependencies': self.dependencies or []
        }


@dataclass
class BacklogOutput:
    """Container for complete backlog generation output."""
    summary: str
    key_requirements: List[str]
    stories: List[UserStory]
    epics: List[str]
    generated_at: str
    model_used: str
    
    def validate(self) -> tuple[bool, List[str]]:
        """Validate entire backlog output."""
        errors = []
        
        if not self.summary or len(self.summary.strip()) < 10:
            errors.append("Summary must be at least 10 characters")
        
        if not self.stories or len(self.stories) == 0:
            errors.append("Must generate at least one user story")
        
        # Validate each story
        for i, story in enumerate(self.stories):
            is_valid, story_errors = story.validate()
            if not is_valid:
                errors.extend([f"Story {i} ({story.id}): {err}" for err in story_errors])
        
        return len(errors) == 0, errors
    
    def to_dict(self):
        """Convert entire output to dictionary."""
        return {
            'summary': self.summary,
            'key_requirements': self.key_requirements,
            'stories': [story.to_dict() for story in self.stories],
            'epics': self.epics,
            'generated_at': self.generated_at,
            'model_used': self.model_used,
            'story_count': len(self.stories)
        }
    
    def to_json(self, indent: int = 2) -> str:
        """Convert to formatted JSON string."""
        return json.dumps(self.to_dict(), indent=indent)
    
    def to_markdown(self) -> str:
        """Convert to markdown for readability."""
        lines = []
        
        # Header
        lines.append("# Backlog Summary\n")
        lines.append(f"{self.summary}\n")
        
        # Key requirements
        lines.append("## Key Requirements\n")
        for req in self.key_requirements:
            lines.append(f"- {req}")
        lines.append("")
        
        # Epics
        lines.append("## Epics\n")
        for epic in self.epics:
            lines.append(f"- {epic}")
        lines.append("")
        
        # Stories by epic
        lines.append("## User Stories\n")
        for epic in self.epics:
            epic_stories = [s for s in self.stories if s.epic == epic]
            if epic_stories:
                lines.append(f"### {epic}\n")
                for story in epic_stories:
                    lines.append(f"**[{story.priority}] {story.title}** (ID: {story.id})\n")
                    lines.append(f"{story.description}\n")
                    lines.append("**Acceptance Criteria:**\n")
                    for criteria in story.acceptance_criteria:
                        lines.append(f"- [ ] {criteria}")
                    lines.append("")
        
        lines.append(f"\n*Generated: {self.generated_at}*\n")
        lines.append(f"*Model: {self.model_used}*")
        
        return "\n".join(lines)
