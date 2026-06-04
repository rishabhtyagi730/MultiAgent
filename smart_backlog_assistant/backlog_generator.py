"""
Main backlog generator - orchestrates the entire backlog generation workflow.
Coordinates input processing, AI generation, validation, and output formatting.
"""

import json
import logging
import sys
from datetime import datetime
from typing import Dict, Any, Optional, List
from pathlib import Path

from ai_service import AIService
from models import UserStory, BacklogOutput, PriorityLevel
from prompt_templates import (
    SYSTEM_PROMPT,
    format_generate_backlog_prompt,
    format_extract_requirements_prompt,
    format_validate_stories_prompt
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('backlog_generator.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class BacklogGenerator:
    """Main orchestrator for backlog generation workflow."""
    
    def __init__(self, api_key: Optional[str] = None, model: str = "claude-3-5-sonnet-20241022"):
        """
        Initialize backlog generator.
        
        Args:
            api_key: Anthropic API key
            model: Claude model to use
        """
        self.ai_service = AIService(api_key=api_key, model=model)
        logger.info(f"BacklogGenerator initialized with model: {model}")
    
    def process_input_file(self, file_path: str) -> str:
        """
        Read and process input file (text or JSON).
        
        Args:
            file_path: Path to input file
        
        Returns:
            Extracted text content
        """
        path = Path(file_path)
        
        if not path.exists():
            raise FileNotFoundError(f"Input file not found: {file_path}")
        
        logger.info(f"Processing input file: {file_path}")
        
        with open(path, 'r') as f:
            if path.suffix.lower() == '.json':
                # If JSON, extract text from content field
                data = json.load(f)
                content = data.get('content', data.get('text', json.dumps(data)))
                logger.info(f"Extracted content from JSON file ({len(content)} chars)")
                return content
            else:
                # Plain text file
                content = f.read()
                logger.info(f"Read text file ({len(content)} chars)")
                return content
    
    def generate_backlog(
        self,
        input_text: str,
        validate: bool = True,
        mode: str = "balanced"
    ) -> BacklogOutput:
        """
        Generate complete backlog from input text.
        
        Args:
            input_text: Meeting notes or requirements
            validate: Whether to validate and improve stories
            mode: "fast", "balanced", or "detailed"
        
        Returns:
            BacklogOutput with structured stories
        """
        logger.info(f"Starting backlog generation in {mode} mode")
        
        # Step 1: Generate initial backlog
        logger.info("Step 1: Generating backlog items...")
        user_prompt = format_generate_backlog_prompt(input_text)
        
        raw_result = self.ai_service.generate_backlog(
            input_text=input_text,
            system_prompt=SYSTEM_PROMPT,
            user_prompt=user_prompt,
            temperature=0.7
        )
        
        # Step 2: Parse and structure results
        logger.info("Step 2: Parsing and validating results...")
        stories = self._parse_stories(raw_result.get('stories', []))
        
        # Step 3: Validate if requested
        if validate and mode in ["balanced", "detailed"]:
            logger.info("Step 3: Validating stories...")
            stories = self._validate_and_improve_stories(stories)
        
        # Step 4: Construct output
        output = BacklogOutput(
            summary=raw_result.get('summary', 'Backlog generated from requirements'),
            key_requirements=raw_result.get('key_requirements', []),
            stories=stories,
            epics=list(set([s.epic for s in stories])),  # Unique epics
            generated_at=datetime.now().isoformat(),
            model_used=self.ai_service.model
        )
        
        # Validate output
        is_valid, errors = output.validate()
        if not is_valid:
            logger.warning(f"Output validation issues: {errors}")
            for error in errors:
                logger.warning(f"  - {error}")
        
        logger.info(f"Backlog generation complete. Generated {len(stories)} stories in {len(output.epics)} epics")
        return output
    
    def _parse_stories(self, stories_data: List[Dict[str, Any]]) -> List[UserStory]:
        """
        Parse raw story data into UserStory objects.
        
        Args:
            stories_data: Raw story dictionaries from AI
        
        Returns:
            List of validated UserStory objects
        """
        stories = []
        
        for i, story_dict in enumerate(stories_data):
            try:
                # Extract fields with fallbacks
                story_id = story_dict.get('id', f'STORY-{i+1:03d}')
                title = story_dict.get('title', '')
                description = story_dict.get('description', '')
                acceptance_criteria = story_dict.get('acceptance_criteria', [])
                priority = story_dict.get('priority', 'MEDIUM')
                epic = story_dict.get('epic', 'Backlog')
                
                # Ensure priority is valid
                if priority not in [p.value for p in PriorityLevel]:
                    logger.warning(f"Invalid priority '{priority}', defaulting to MEDIUM")
                    priority = 'MEDIUM'
                
                # Create story object
                story = UserStory(
                    id=story_id,
                    title=title,
                    description=description,
                    acceptance_criteria=acceptance_criteria,
                    priority=priority,
                    epic=epic,
                    estimated_effort=story_dict.get('estimated_effort')
                )
                
                # Validate
                is_valid, errors = story.validate()
                if is_valid:
                    stories.append(story)
                    logger.debug(f"Parsed story {story_id}: {title}")
                else:
                    logger.warning(f"Story {story_id} validation failed: {errors}")
                    
            except Exception as e:
                logger.error(f"Error parsing story {i}: {str(e)}")
        
        logger.info(f"Successfully parsed {len(stories)} valid stories")
        return stories
    
    def _validate_and_improve_stories(self, stories: List[UserStory]) -> List[UserStory]:
        """
        Use AI to validate and improve stories.
        
        Args:
            stories: Initial stories to validate
        
        Returns:
            Improved stories
        """
        try:
            # Prepare stories for validation
            stories_json = json.dumps(
                [s.to_dict() for s in stories],
                indent=2
            )
            
            # Call validation prompt
            validation_prompt = format_validate_stories_prompt(stories_json)
            validation_result = self.ai_service.validate_stories(
                stories_json=stories_json,
                system_prompt=SYSTEM_PROMPT,
                validation_prompt=validation_prompt
            )
            
            # Parse improved stories
            improved_stories = self._parse_stories(validation_result.get('stories', []))
            quality_score = validation_result.get('quality_score', 'unknown')
            logger.info(f"Story validation complete. Quality score: {quality_score}")
            
            return improved_stories if improved_stories else stories
            
        except Exception as e:
            logger.warning(f"Story validation failed, using original stories: {str(e)}")
            return stories
    
    def generate_from_file(
        self,
        input_file: str,
        output_json: Optional[str] = None,
        output_markdown: Optional[str] = None,
        validate: bool = True,
        mode: str = "balanced"
    ) -> BacklogOutput:
        """
        Generate backlog from input file and save outputs.
        
        Args:
            input_file: Path to input file
            output_json: Path to save JSON output (optional)
            output_markdown: Path to save Markdown output (optional)
            validate: Whether to validate stories
            mode: Generation mode
        
        Returns:
            BacklogOutput object
        """
        # Read input
        input_text = self.process_input_file(input_file)
        
        # Generate backlog
        backlog = self.generate_backlog(
            input_text=input_text,
            validate=validate,
            mode=mode
        )
        
        # Save outputs
        if output_json:
            self._save_json_output(backlog, output_json)
        
        if output_markdown:
            self._save_markdown_output(backlog, output_markdown)
        
        return backlog
    
    def _save_json_output(self, backlog: BacklogOutput, output_path: str):
        """Save backlog as JSON."""
        try:
            with open(output_path, 'w') as f:
                f.write(backlog.to_json(indent=2))
            logger.info(f"JSON output saved to: {output_path}")
        except Exception as e:
            logger.error(f"Failed to save JSON output: {str(e)}")
    
    def _save_markdown_output(self, backlog: BacklogOutput, output_path: str):
        """Save backlog as Markdown."""
        try:
            with open(output_path, 'w') as f:
                f.write(backlog.to_markdown())
            logger.info(f"Markdown output saved to: {output_path}")
        except Exception as e:
            logger.error(f"Failed to save Markdown output: {str(e)}")
    
    def get_ai_usage_stats(self) -> Dict[str, Any]:
        """Get statistics on AI API usage."""
        return self.ai_service.get_usage_stats()
    
    def print_stats(self):
        """Print AI usage statistics to console."""
        stats = self.get_ai_usage_stats()
        print("\n" + "="*50)
        print("AI API Usage Statistics")
        print("="*50)
        print(f"Total API calls: {stats['total_calls']}")
        print(f"Successful calls: {stats['successful_calls']}")
        print(f"Failed calls: {stats['failed_calls']}")
        print(f"Total input tokens: {stats['total_input_tokens']}")
        print(f"Total output tokens: {stats['total_output_tokens']}")
        print(f"Model used: {stats['model']}")
        print("="*50 + "\n")


def main():
    """Command-line interface for backlog generator."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Generate structured backlog from meeting notes or requirements"
    )
    parser.add_argument(
        "--input",
        required=True,
        help="Input file (txt or json)"
    )
    parser.add_argument(
        "--output-json",
        default="backlog_output.json",
        help="Output JSON file"
    )
    parser.add_argument(
        "--output-markdown",
        default="backlog_output.md",
        help="Output Markdown file"
    )
    parser.add_argument(
        "--mode",
        choices=["fast", "balanced", "detailed"],
        default="balanced",
        help="Generation mode"
    )
    parser.add_argument(
        "--no-validate",
        action="store_true",
        help="Skip story validation"
    )
    parser.add_argument(
        "--model",
        default="claude-3-5-sonnet-20241022",
        help="Claude model to use"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )
    
    args = parser.parse_args()
    
    # Set log level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Create generator and run
    generator = BacklogGenerator(model=args.model)
    
    try:
        backlog = generator.generate_from_file(
            input_file=args.input,
            output_json=args.output_json,
            output_markdown=args.output_markdown,
            validate=not args.no_validate,
            mode=args.mode
        )
        
        print(f"\n✅ Backlog generation successful!")
        print(f"Generated {len(backlog.stories)} stories in {len(backlog.epics)} epics")
        
        generator.print_stats()
        
    except Exception as e:
        logger.error(f"Backlog generation failed: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
