#!/usr/bin/env python3
"""
Quick start script to verify Smart Backlog Assistant installation and test with a sample.
Run this to ensure everything is working correctly.
"""

import sys
import os
from pathlib import Path

def print_header(text):
    """Print formatted header."""
    print("\n" + "="*60)
    print(f"  {text}")
    print("="*60)

def check_dependencies():
    """Check if all required dependencies are installed."""
    print_header("1. Checking Dependencies")
    
    dependencies = {
        'anthropic': 'Anthropic Python SDK',
        'pydantic': 'Data validation',
        'dotenv': 'Environment configuration'
    }
    
    missing = []
    for package, description in dependencies.items():
        try:
            __import__(package)
            print(f"  ✅ {package:20} - {description}")
        except ImportError:
            print(f"  ❌ {package:20} - {description} [MISSING]")
            missing.append(package)
    
    return len(missing) == 0

def check_api_key():
    """Check if API key is configured."""
    print_header("2. Checking API Configuration")
    
    api_key = os.getenv('ANTHROPIC_API_KEY')
    if api_key:
        # Show masked key
        masked = api_key[:7] + "..." + api_key[-4:] if len(api_key) > 11 else "***"
        print(f"  ✅ ANTHROPIC_API_KEY configured: {masked}")
        return True
    else:
        print(f"  ❌ ANTHROPIC_API_KEY not found")
        print(f"     Set it with: export ANTHROPIC_API_KEY='sk-ant-...'")
        print(f"     Or create .env file with: ANTHROPIC_API_KEY=sk-ant-...")
        return False

def check_files():
    """Check if all required files exist."""
    print_header("3. Checking Project Files")
    
    files = {
        'backlog_generator.py': 'Main generator',
        'ai_service.py': 'AI service',
        'models.py': 'Data models',
        'prompt_templates.py': 'Prompt templates',
        'test_generator.py': 'Test suite',
        'samples/standup_notes.txt': 'Sample input 1',
        'samples/feature_request.json': 'Sample input 2',
        'samples/requirements.txt': 'Sample input 3'
    }
    
    base_dir = Path(__file__).parent
    missing = []
    
    for file_path, description in files.items():
        full_path = base_dir / file_path
        if full_path.exists():
            print(f"  ✅ {file_path:35} - {description}")
        else:
            print(f"  ❌ {file_path:35} - {description} [MISSING]")
            missing.append(file_path)
    
    return len(missing) == 0

def test_import():
    """Test importing main modules."""
    print_header("4. Testing Module Imports")
    
    try:
        sys.path.insert(0, str(Path(__file__).parent))
        
        print("  Importing models...")
        from models import UserStory, BacklogOutput, PriorityLevel
        print("    ✅ models.py imported successfully")
        
        print("  Importing ai_service...")
        from ai_service import AIService
        print("    ✅ ai_service.py imported successfully")
        
        print("  Importing prompt_templates...")
        from prompt_templates import SYSTEM_PROMPT, format_generate_backlog_prompt
        print("    ✅ prompt_templates.py imported successfully")
        
        print("  Importing backlog_generator...")
        from backlog_generator import BacklogGenerator
        print("    ✅ backlog_generator.py imported successfully")
        
        return True
        
    except ImportError as e:
        print(f"  ❌ Import failed: {str(e)}")
        return False

def test_basic_functionality():
    """Test basic functionality without API calls."""
    print_header("5. Testing Basic Functionality")
    
    try:
        sys.path.insert(0, str(Path(__file__).parent))
        from models import UserStory, BacklogOutput
        
        # Create a test story
        print("  Creating test user story...")
        story = UserStory(
            id="TEST-001",
            title="As a user, I want to test the system",
            description="This is a test story to verify functionality",
            acceptance_criteria=["System accepts story", "Story validates correctly"],
            priority="HIGH",
            epic="Testing"
        )
        print("    ✅ User story created")
        
        # Validate story
        print("  Validating story...")
        is_valid, errors = story.validate()
        if is_valid:
            print("    ✅ Story validation passed")
        else:
            print(f"    ❌ Story validation failed: {errors}")
            return False
        
        # Convert to dict
        print("  Converting to dictionary...")
        story_dict = story.to_dict()
        assert story_dict['id'] == "TEST-001"
        print("    ✅ Dictionary conversion successful")
        
        # Create backlog
        print("  Creating backlog output...")
        output = BacklogOutput(
            summary="Test backlog",
            key_requirements=["Requirement 1"],
            stories=[story],
            epics=["Testing"],
            generated_at="2026-06-04T00:00:00",
            model_used="test"
        )
        print("    ✅ Backlog created")
        
        # Validate backlog
        print("  Validating backlog...")
        is_valid, errors = output.validate()
        if is_valid:
            print("    ✅ Backlog validation passed")
        else:
            print(f"    ❌ Backlog validation failed: {errors}")
            return False
        
        return True
        
    except Exception as e:
        print(f"  ❌ Functionality test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def print_summary(results):
    """Print summary of all checks."""
    print_header("Summary")
    
    all_passed = all(results.values())
    
    for check_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"  {status:10} - {check_name}")
    
    print()
    if all_passed:
        print("  🎉 All checks passed! Ready to use.")
        print()
        print("  Next steps:")
        print("    1. Try a sample generation:")
        print("       python backlog_generator.py --input samples/standup_notes.txt --verbose")
        print()
        print("    2. Run the test suite:")
        print("       pytest test_generator.py -v")
        print()
        print("    3. See usage guide:")
        print("       cat USAGE_GUIDE.md")
        return 0
    else:
        print("  ⚠️  Some checks failed. Please address the issues above.")
        print()
        print("  Common fixes:")
        print("    - Install dependencies: pip install -r requirements.txt")
        print("    - Set API key: export ANTHROPIC_API_KEY='sk-ant-...'")
        print("    - Check file paths: ensure you're in the smart_backlog_assistant directory")
        return 1

def main():
    """Run all checks."""
    print_header("Smart Backlog Assistant - Installation Verification")
    print("  This script verifies your installation is correct and ready to use.")
    
    results = {}
    
    # Run all checks
    results['Dependencies'] = check_dependencies()
    results['API Configuration'] = check_api_key()
    results['Project Files'] = check_files()
    results['Module Imports'] = test_import()
    results['Basic Functionality'] = test_basic_functionality()
    
    # Print summary and return appropriate exit code
    return print_summary(results)

if __name__ == '__main__':
    sys.exit(main())
