"""
OpenAI API integration and AI service layer.
Handles all interactions with OpenAI's GPT API with error handling and retries.
"""

import openai
import json
import logging
import time
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class AIService:
    """Wrapper around OpenAI API with error handling and prompt management."""
    
    def __init__(
        self, 
        api_key: Optional[str] = None,
        model: str = "gpt-4-turbo",
        max_retries: int = 3,
        timeout_seconds: int = 30
    ):
        """
        Initialize AI service.
        
        Args:
            api_key: OpenAI API key (uses env var if not provided)
            model: Model ID to use (default: gpt-4-turbo)
            max_retries: Max retries for API calls
            timeout_seconds: Request timeout
        """
        self.client = openai.OpenAI(api_key=api_key)
        self.model = model
        self.max_retries = max_retries
        self.timeout_seconds = timeout_seconds
        self.usage_stats = {
            "total_calls": 0,
            "successful_calls": 0,
            "failed_calls": 0,
            "total_input_tokens": 0,
            "total_output_tokens": 0
        }
        logger.info(f"AIService initialized with model: {model}")
    
    def generate_backlog(
        self,
        input_text: str,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.7
    ) -> Dict[str, Any]:
        """
        Generate backlog items using OpenAI GPT.
        
        Args:
            input_text: Raw meeting notes or requirements
            system_prompt: System context for GPT
            user_prompt: User message with formatting instructions
            temperature: Creativity level (0.0-1.0)
        
        Returns:
            Parsed JSON response with backlog data
        """
        logger.info(f"Starting backlog generation. Input length: {len(input_text)} chars")
        
        try:
            # Call OpenAI with retry logic
            response = self._call_openai_with_retry(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=temperature,
                max_tokens=4096
            )
            
            # Parse and validate JSON response
            result = self._parse_json_response(response)
            logger.info(f"Successfully generated {len(result.get('stories', []))} stories")
            
            return result
            
        except Exception as e:
            logger.error(f"Backlog generation failed: {str(e)}")
            raise
    
    def _call_openai_with_retry(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 4096
    ) -> str:
        """
        Call OpenAI API with exponential backoff retry logic.
        
        Args:
            system_prompt: System context
            user_prompt: User message
            temperature: Creativity parameter
            max_tokens: Maximum response length
        
        Returns:
            Raw API response text
        """
        last_error = None
        
        for attempt in range(self.max_retries):
            try:
                self.usage_stats["total_calls"] += 1
                
                # Log the API call (truncated)
                logger.debug(f"API call attempt {attempt + 1}/{self.max_retries}")
                logger.debug(f"System prompt: {system_prompt[:100]}...")
                logger.debug(f"User prompt: {user_prompt[:100]}...")
                
                # Make API call to OpenAI
                response = self.client.chat.completions.create(
                    model=self.model,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ]
                )
                
                # Track successful call and token usage
                self.usage_stats["successful_calls"] += 1
                self.usage_stats["total_input_tokens"] += response.usage.prompt_tokens
                self.usage_stats["total_output_tokens"] += response.usage.completion_tokens
                
                logger.info(
                    f"API call successful. "
                    f"Input tokens: {response.usage.prompt_tokens}, "
                    f"Output tokens: {response.usage.completion_tokens}"
                )
                
                return response.choices[0].message.content
                
            except openai.RateLimitError as e:
                last_error = e
                wait_time = (2 ** attempt) + (attempt * 0.5)  # Exponential backoff
                logger.warning(
                    f"Rate limited. Waiting {wait_time}s before retry {attempt + 1}"
                )
                time.sleep(wait_time)
                
            except openai.APIError as e:
                last_error = e
                logger.error(f"API error on attempt {attempt + 1}: {str(e)}")
                if attempt < self.max_retries - 1:
                    wait_time = 2 ** attempt
                    logger.info(f"Retrying in {wait_time}s...")
                    time.sleep(wait_time)
        
        self.usage_stats["failed_calls"] += 1
        raise RuntimeError(
            f"Failed to get response after {self.max_retries} attempts. "
            f"Last error: {str(last_error)}"
        )
    
    def _parse_json_response(self, response_text: str) -> Dict[str, Any]:
        """
        Parse JSON from OpenAI response with fallback handling.
        
        Args:
            response_text: Raw response from OpenAI
        
        Returns:
            Parsed JSON dictionary
        
        Raises:
            ValueError: If JSON parsing fails
        """
        # Try direct JSON parsing
        try:
            return json.loads(response_text)
        except json.JSONDecodeError:
            logger.warning("Direct JSON parsing failed, attempting extraction...")
        
        # Try extracting JSON from markdown code blocks
        try:
            if "```json" in response_text:
                json_start = response_text.find("```json") + 7
                json_end = response_text.find("```", json_start)
                json_text = response_text[json_start:json_end].strip()
                return json.loads(json_text)
            
            elif "```" in response_text:
                json_start = response_text.find("```") + 3
                json_end = response_text.find("```", json_start)
                json_text = response_text[json_start:json_end].strip()
                return json.loads(json_text)
        except (json.JSONDecodeError, ValueError) as e:
            logger.warning(f"Markdown extraction failed: {str(e)}")
        
        # Last resort: try to find JSON object boundaries
        try:
            json_start = response_text.find("{")
            json_end = response_text.rfind("}") + 1
            if json_start >= 0 and json_end > json_start:
                json_text = response_text[json_start:json_end]
                return json.loads(json_text)
        except (json.JSONDecodeError, ValueError) as e:
            logger.error(f"JSON extraction failed: {str(e)}")
        
        raise ValueError(
            f"Could not parse JSON from response. Response length: {len(response_text)}"
        )
    
    def extract_requirements(
        self,
        input_text: str,
        system_prompt: str,
        extraction_prompt: str
    ) -> Dict[str, Any]:
        """
        Extract requirements from input text using OpenAI.
        
        Args:
            input_text: Raw input text
            system_prompt: System context
            extraction_prompt: Extraction instructions
        
        Returns:
            Extracted requirements dictionary
        """
        logger.info("Starting requirement extraction")
        
        try:
            response = self._call_openai_with_retry(
                system_prompt=system_prompt,
                user_prompt=extraction_prompt,
                temperature=0.5,  # Lower temp for consistency
                max_tokens=2048
            )
            
            result = self._parse_json_response(response)
            logger.info(f"Extracted {len(result.get('explicit_requirements', []))} requirements")
            
            return result
            
        except Exception as e:
            logger.error(f"Requirement extraction failed: {str(e)}")
            raise
    
    def validate_stories(
        self,
        stories_json: str,
        system_prompt: str,
        validation_prompt: str
    ) -> Dict[str, Any]:
        """
        Validate and improve user stories using OpenAI.
        
        Args:
            stories_json: JSON string of stories to validate
            system_prompt: System context
            validation_prompt: Validation instructions
        
        Returns:
            Validation results with improved stories
        """
        logger.info("Starting story validation")
        
        try:
            response = self._call_openai_with_retry(
                system_prompt=system_prompt,
                user_prompt=validation_prompt,
                temperature=0.5,
                max_tokens=4096
            )
            
            result = self._parse_json_response(response)
            quality_score = result.get("quality_score", "unknown")
            logger.info(f"Validation complete. Quality score: {quality_score}")
            
            return result
            
        except Exception as e:
            logger.error(f"Story validation failed: {str(e)}")
            raise
    
    def get_usage_stats(self) -> Dict[str, Any]:
        """Get statistics on API usage."""
        return {
            **self.usage_stats,
            "timestamp": datetime.now().isoformat(),
            "model": self.model
        }
    
    def reset_usage_stats(self):
        """Reset usage statistics."""
        self.usage_stats = {
            "total_calls": 0,
            "successful_calls": 0,
            "failed_calls": 0,
            "total_input_tokens": 0,
            "total_output_tokens": 0
        }
        logger.info("Usage stats reset")
