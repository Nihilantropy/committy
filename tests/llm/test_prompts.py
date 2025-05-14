"""Tests for prompt templates."""

import pytest
from committy.llm.prompts import (
    get_prompt_for_diff,
    detect_likely_change_type,
    enhance_commit_message,
    SPECIALIZED_TEMPLATES
)


class TestPromptTemplates:
    """Tests for prompt templates."""
    
    def test_get_prompt_for_diff_with_known_type(self):
        """Test getting a prompt with a known change type."""
        context = "Sample diff context"
        
        # Test with each specialized template
        for change_type in SPECIALIZED_TEMPLATES:
            prompt = get_prompt_for_diff(context, change_type)
            
            # Check that the context is included
            assert context in prompt
            
            # Check that type-specific patterns are included
            if change_type == "refactor":
                assert "Refactoring Patterns" in prompt
            elif change_type == "fix":
                assert "Bug Fix Patterns" in prompt
            elif change_type == "feat":
                assert "Feature Addition Patterns" in prompt
            elif change_type == "docs":
                assert "Documentation Change Patterns" in prompt
    
    def test_get_prompt_for_diff_with_unknown_type(self):
        """Test getting a prompt with an unknown change type."""
        context = "Sample diff context"
        prompt = get_prompt_for_diff(context)
        
        # Check that the context is included
        assert context in prompt
        
        # Check that it uses the enhanced template
        assert "expert developer" in prompt
        assert "Git Diff Content" in prompt
    
    def test_get_prompt_for_diff_with_invalid_type(self):
        """Test getting a prompt with an invalid change type."""
        context = "Sample diff context"
        prompt = get_prompt_for_diff(context, "invalid_type")
        
        # Should fall back to the enhanced template
        assert "expert developer" in prompt
        assert "Git Diff Content" in prompt


class TestChangeTypeDetection:
    """Tests for change type detection."""
    
    def test_detect_fix_type(self):
        """Test detecting fix change type."""
        context = """
        # Git Diff Summary
        Total Files Changed: 1
        Total Additions: 3
        Total Deletions: 1
        
        # File: src/api/users.js
        - Fixed bug in user authentication
        - Added null check for user ID
        - Fixed error handling for invalid tokens
        """
        
        change_type = detect_likely_change_type(context)
        assert change_type == "fix"
    
    def test_detect_feature_type(self):
        """Test detecting feature change type."""
        context = """
        # Git Diff Summary
        Total Files Changed: 2
        Total Additions: 25
        Total Deletions: 0
        
        # File: src/components/NewFeature.js
        - Add new user dashboard component
        - Implement filtering options
        - Added API integration for user stats
        
        # File: src/api/dashboard.js
        - Add new endpoints for dashboard data
        """
        
        change_type = detect_likely_change_type(context)
        assert change_type in ["feat", "fix"]
    
    def test_detect_refactor_type(self):
        """Test detecting refactor change type."""
        context = """
        # Git Diff Summary
        Total Files Changed: 3
        Total Additions: 15
        Total Deletions: 12
        
        # File: src/utils/helpers.js
        - Refactored authentication logic
        - Extracted validation to separate functions
        - Simplified error handling
        
        # File: src/components/Auth.js
        - Updated to use new helper functions
        """
        
        change_type = detect_likely_change_type(context)
        assert change_type == "refactor"
    
    def test_detect_docs_type(self):
        """Test detecting docs change type."""
        context = """
        # Git Diff Summary
        Total Files Changed: 2
        Total Additions: 20
        Total Deletions: 5
        
        # File: README.md
        - Updated installation instructions
        - Added usage examples
        - Improved API documentation
        
        # File: docs/api.md
        - Added documentation for new endpoints
        """
        
        change_type = detect_likely_change_type(context)
        assert change_type == "docs"
    
    def test_detect_test_type(self):
        """Test detecting test change type."""
        context = """
        # Git Diff Summary
        Total Files Changed: 2
        Total Additions: 30
        Total Deletions: 0
        
        # File: tests/api/users.test.js
        - Added unit tests for user authentication
        - Added tests for error cases
        
        # File: tests/components/Auth.test.js
        - Added tests for Auth component
        """
        
        change_type = detect_likely_change_type(context)
        assert change_type == "test"
    
    def test_detect_with_no_clear_pattern(self):
        """Test detecting with no clear pattern."""
        context = """
        # Git Diff Summary
        Total Files Changed: 1
        Total Additions: 1
        Total Deletions: 1
        
        # File: unknown.txt
        - One line removed
        + One line added
        """
        
        change_type = detect_likely_change_type(context)
        assert change_type is None


class TestCommitMessageEnhancement:
    """Tests for commit message enhancement."""
    
    def test_enhance_commit_message_lowercase_first_letter(self):
        """Test enhancing commit message by lowercasing first letter."""
        message = "Feat(auth): Add user authentication"
        enhanced = enhance_commit_message(message)
        assert enhanced == "Feat(auth): add user authentication"
    
    def test_enhance_commit_message_remove_period(self):
        """Test enhancing commit message by removing trailing period."""
        message = "fix(api): update error handling."
        enhanced = enhance_commit_message(message)
        assert enhanced == "fix(api): update error handling"
    
    def test_enhance_commit_message_with_body(self):
        """Test enhancing commit message with body."""
        message = "Fix(auth): Fix login validation\n\nUpdated validation logic to handle special characters in passwords."
        enhanced = enhance_commit_message(message)
        assert enhanced == "Fix(auth): fix login validation\n\nUpdated validation logic to handle special characters in passwords."
    
    def test_enhance_commit_message_with_body_and_footer(self):
        """Test enhancing commit message with body and footer."""
        message = "Feat(ui): Add dark mode.\n\nImplemented dark mode toggle in user settings.\n\nCloses #123"
        enhanced = enhance_commit_message(message)
        assert enhanced == "Feat(ui): add dark mode\n\nImplemented dark mode toggle in user settings.\n\nCloses #123"
    
    def test_enhance_commit_message_already_formatted(self):
        """Test enhancing commit message that is already properly formatted."""
        message = "fix(api): update error handling\n\nImproved error messages for better debugging."
        enhanced = enhance_commit_message(message)
        assert enhanced == message