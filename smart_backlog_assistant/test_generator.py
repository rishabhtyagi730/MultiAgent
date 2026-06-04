"""
Test suite for Smart Backlog Assistant.
Includes unit tests and integration tests with realistic scenarios.
"""

import json
import pytest
from datetime import datetime
from pathlib import Path
import tempfile

from models import UserStory, BacklogOutput, PriorityLevel, AcceptanceCriteria
from ai_service import AIService
from backlog_generator import BacklogGenerator


class TestUserStory:
    """Tests for UserStory model."""
    
    def test_valid_story_creation(self):
        """Test creating a valid user story."""
        story = UserStory(
            id="STORY-001",
            title="As a user, I want to reset my password",
            description="Users need ability to reset forgotten passwords securely",
            acceptance_criteria=[
                "When user clicks 'Forgot Password', email is sent",
                "Reset link expires after 24 hours",
                "New password must meet security requirements"
            ],
            priority="HIGH",
            epic="Authentication"
        )
        
        is_valid, errors = story.validate()
        assert is_valid, f"Story validation failed: {errors}"
        assert story.id == "STORY-001"
        assert story.priority == "HIGH"
    
    def test_story_validation_fails_short_title(self):
        """Test validation fails with short title."""
        story = UserStory(
            id="STORY-001",
            title="Reset",
            description="User needs password reset",
            acceptance_criteria=["Can reset password"],
            priority="HIGH",
            epic="Auth"
        )
        
        is_valid, errors = story.validate()
        assert not is_valid
        assert any("Title" in error for error in errors)
    
    def test_story_to_dict(self):
        """Test story conversion to dictionary."""
        story = UserStory(
            id="STORY-001",
            title="As a developer, I want API documentation",
            description="Clear API docs for integration",
            acceptance_criteria=["Docs cover all endpoints", "Examples provided"],
            priority="MEDIUM",
            epic="Documentation"
        )
        
        story_dict = story.to_dict()
        assert story_dict["id"] == "STORY-001"
        assert story_dict["priority"] == "MEDIUM"
        assert len(story_dict["acceptance_criteria"]) == 2


class TestBacklogOutput:
    """Tests for BacklogOutput model."""
    
    def test_backlog_output_creation(self):
        """Test creating backlog output."""
        stories = [
            UserStory(
                id="STORY-001",
                title="As a user, I want single sign-on",
                description="Enable SSO for enterprise users",
                acceptance_criteria=[
                    "SAML 2.0 integration working",
                    "Users can log in via SSO",
                    "Session timeout enforced"
                ],
                priority="HIGH",
                epic="Authentication"
            )
        ]
        
        output = BacklogOutput(
            summary="Authentication system modernization",
            key_requirements=["SSO integration", "OAuth fixes"],
            stories=stories,
            epics=["Authentication"],
            generated_at=datetime.now().isoformat(),
            model_used="claude-3-5-sonnet-20241022"
        )
        
        is_valid, errors = output.validate()
        assert is_valid, f"Output validation failed: {errors}"
        assert len(output.stories) == 1
        assert output.epics == ["Authentication"]
    
    def test_backlog_to_json(self):
        """Test backlog conversion to JSON."""
        stories = [
            UserStory(
                id="STORY-001",
                title="As a user, I want to login",
                description="Basic authentication",
                acceptance_criteria=["Can enter credentials", "Redirects on success"],
                priority="CRITICAL",
                epic="Auth"
            )
        ]
        
        output = BacklogOutput(
            summary="Build authentication",
            key_requirements=["Secure login"],
            stories=stories,
            epics=["Auth"],
            generated_at=datetime.now().isoformat(),
            model_used="test-model"
        )
        
        json_str = output.to_json()
        parsed = json.loads(json_str)
        
        assert parsed["summary"] == "Build authentication"
        assert len(parsed["stories"]) == 1
        assert parsed["model_used"] == "test-model"
    
    def test_backlog_to_markdown(self):
        """Test backlog conversion to markdown."""
        stories = [
            UserStory(
                id="STORY-001",
                title="Add dark mode",
                description="Users want dark theme support",
                acceptance_criteria=[
                    "Dark mode toggle in settings",
                    "All pages support dark theme",
                    "Preference persists across sessions"
                ],
                priority="MEDIUM",
                epic="UI"
            )
        ]
        
        output = BacklogOutput(
            summary="UI/UX Improvements",
            key_requirements=["Dark mode support"],
            stories=stories,
            epics=["UI"],
            generated_at=datetime.now().isoformat(),
            model_used="test-model"
        )
        
        markdown = output.to_markdown()
        
        assert "# Backlog Summary" in markdown
        assert "Dark mode" in markdown
        assert "MEDIUM" in markdown
        assert "UI/UX Improvements" in markdown


class TestBacklogGenerator:
    """Integration tests for BacklogGenerator."""
    
    def test_generator_initialization(self):
        """Test generator initializes correctly."""
        generator = BacklogGenerator(model="claude-3-5-sonnet-20241022")
        assert generator.ai_service is not None
        assert generator.ai_service.model == "claude-3-5-sonnet-20241022"
    
    def test_parse_stories(self):
        """Test story parsing from raw data."""
        generator = BacklogGenerator()
        
        raw_stories = [
            {
                "id": "STORY-001",
                "title": "As a user, I want notifications",
                "description": "Users need email notifications",
                "acceptance_criteria": [
                    "Email sent when mentioned",
                    "Can unsubscribe from notifications"
                ],
                "priority": "HIGH",
                "epic": "Notifications"
            }
        ]
        
        stories = generator._parse_stories(raw_stories)
        
        assert len(stories) == 1
        assert stories[0].id == "STORY-001"
        assert stories[0].priority == "HIGH"
        assert len(stories[0].acceptance_criteria) == 2
    
    def test_parse_stories_invalid_priority(self):
        """Test story parsing handles invalid priority."""
        generator = BacklogGenerator()
        
        raw_stories = [
            {
                "id": "STORY-001",
                "title": "As a user, I want something",
                "description": "User needs something important",
                "acceptance_criteria": ["Can do something", "System validates"],
                "priority": "INVALID",
                "epic": "Features"
            }
        ]
        
        stories = generator._parse_stories(raw_stories)
        
        assert len(stories) == 1
        assert stories[0].priority == "MEDIUM"  # Should default to MEDIUM
    
    def test_process_input_file_txt(self):
        """Test processing text input file."""
        generator = BacklogGenerator()
        
        # Create temp file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("This is a test requirement document\nWith multiple lines\nAbout features")
            temp_path = f.name
        
        try:
            content = generator.process_input_file(temp_path)
            assert "requirement document" in content
            assert len(content) > 0
        finally:
            Path(temp_path).unlink()
    
    def test_process_input_file_json(self):
        """Test processing JSON input file."""
        generator = BacklogGenerator()
        
        # Create temp JSON file
        data = {
            "content": "Meeting notes about authentication system",
            "date": "2026-06-04"
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(data, f)
            temp_path = f.name
        
        try:
            content = generator.process_input_file(temp_path)
            assert "authentication system" in content
        finally:
            Path(temp_path).unlink()
    
    def test_process_input_file_not_found(self):
        """Test error handling for missing file."""
        generator = BacklogGenerator()
        
        with pytest.raises(FileNotFoundError):
            generator.process_input_file("/nonexistent/path/file.txt")


class TestScenarios:
    """Test realistic scenarios."""
    
    def test_scenario_standup_notes(self):
        """Test processing standup meeting notes."""
        generator = BacklogGenerator()
        
        standup_notes = """
        Daily Standup - June 4, 2026
        
        Completed:
        - Fixed login bug for SSO users
        - Updated API documentation
        
        In Progress:
        - Implementing password reset flow
        - Performance optimization on dashboard
        
        Blockers:
        - Need security review for OAuth changes
        - Database migration scheduled for next week
        
        Priority Issues:
        - Users reporting slow search (>5 seconds)
        - Email notifications not sending for some users
        """
        
        # Verify we can parse this
        assert len(standup_notes) > 50
        assert "Priority" in standup_notes
        assert "Blockers" in standup_notes
    
    def test_scenario_feature_request(self):
        """Test processing feature request."""
        feature_request = """
        Feature Request: Dark Mode Support
        
        Description:
        Users have requested dark mode/theme support for evening use.
        
        User Research:
        - 45% of users access app in evenings
        - Competitor apps all have dark mode
        - Support tickets requesting this feature
        
        Technical Considerations:
        - Need to update all CSS
        - Store preference in user settings
        - Use system theme preference as default
        
        Acceptance Criteria:
        - Toggle in settings to switch themes
        - All UI elements properly themed
        - Preference persists across sessions
        - Performance impact < 5%
        """
        
        assert "Dark Mode" in feature_request
        assert "User Research" in feature_request
        assert len(feature_request) > 100
    
    def test_scenario_requirements_json(self):
        """Test processing structured requirements JSON."""
        requirements = {
            "project": "Authentication Modernization",
            "phase": "Q3 2026",
            "requirements": [
                {
                    "id": "REQ-001",
                    "title": "SSO Integration",
                    "priority": "HIGH"
                },
                {
                    "id": "REQ-002",
                    "title": "MFA Support",
                    "priority": "HIGH"
                }
            ]
        }
        
        assert requirements["project"] == "Authentication Modernization"
        assert len(requirements["requirements"]) == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
