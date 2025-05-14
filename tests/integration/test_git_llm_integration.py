"""Integration tests for Git and LLM components."""

import os
import tempfile
import pytest
from unittest.mock import patch, MagicMock

from committy.git.parser import parse_diff
from committy.llm.index import build_prompt_from_diff
from committy.llm.prompts import get_prompt_for_diff, detect_likely_change_type
from committy.llm.generator import CommitMessageGenerator


class TestGitLlmIntegration:
    """Integration tests for Git and LLM components."""
    
    def test_diff_to_prompt_pipeline(self):
        """Test the flow from diff parsing to prompt generation."""
        # Load a test diff from test fixtures
        fixture_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "fixtures",
            "feature_addition.diff"
        )
        
        with open(fixture_path, "r") as f:
            diff_text = f.read()
        
        # Parse the diff
        git_diff = parse_diff(diff_text)
        
        # Verify basic diff parsing
        assert len(git_diff.files) == 3
        assert any(file.path == "src/components/UserDashboard.js" for file in git_diff.files)
        assert any(file.path == "src/api/users.js" for file in git_diff.files)
        assert any(file.path == "src/components/index.js" for file in git_diff.files)
        
        # Build context from diff
        diff_data = git_diff.as_dict()
        context = build_prompt_from_diff(diff_data)
        
        # Verify context contains key components
        assert "Git Diff Analysis" in context
        assert "Changed Files" in context or "Diff Content" in context
        
        # Detect change type
        change_type = detect_likely_change_type(context)
        
        # Verify correct change type detection for feature addition
        assert change_type in ["feat", "fix"]
        
        # Get prompt for the detected change type
        prompt = get_prompt_for_diff(context, change_type)
        
        # Verify prompt structure based on change type
        if change_type == "feat":
            assert "Feature Addition" in prompt
        elif change_type == "fix":
            assert "Bug Fix" in prompt
        else:
            assert False, f"Unexpected change type detected: {change_type}"
    
    def test_diff_to_message_with_mock_llm(self):
        """Test the complete pipeline from diff to message with a mock LLM."""
        # Load a test diff
        fixture_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "fixtures",
            "bug_fix.diff"
        )
        
        with open(fixture_path, "r") as f:
            diff_text = f.read()
        
        # Create generator with mocked Ollama client
        generator = CommitMessageGenerator()
        
        # Mock the _generate_message method to return a fixed response
        with patch.object(
            generator, 
            "_generate_message", 
            return_value="fix(auth): improve input validation"
        ):
            # Generate a commit message
            message = generator.generate_from_diff(diff_text)
            
            # Verify the output format matches expectations
            assert message.startswith("fix(auth):")
            assert "validation" in message.lower()
    
    def test_expected_fixtures_consistency(self):
        """Test that our test fixtures and expected outputs are consistent."""
        # This tests ensures our test fixtures are well-formed and consistent
        fixtures_dir = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "fixtures"
        )
        
        for fixture_type in ["feature_addition", "bug_fix"]:
            diff_path = os.path.join(fixtures_dir, f"{fixture_type}.diff")
            expected_path = os.path.join(fixtures_dir, f"{fixture_type}.expected.txt")
            
            # Verify both files exist
            assert os.path.exists(diff_path), f"Missing diff file: {diff_path}"
            assert os.path.exists(expected_path), f"Missing expected file: {expected_path}"
            
            # Load files
            with open(diff_path, "r") as f:
                diff_text = f.read()
                
            with open(expected_path, "r") as f:
                expected_text = f.read()
            
            # Verify diff is parseable
            git_diff = parse_diff(diff_text)
            assert git_diff is not None
            assert len(git_diff.files) > 0
            
            # Verify expected message is in correct format
            if fixture_type == "feature_addition":
                assert "feat" in expected_text.lower()
            elif fixture_type == "bug_fix":
                assert "fix" in expected_text.lower()
    
    @pytest.mark.parametrize("fixture_name", ["feature_addition", "bug_fix"])
    def test_end_to_end_with_mocks(self, fixture_name):
        """Test end-to-end flow from diff to commit message for different fixtures."""
        fixtures_dir = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "fixtures"
        )
        
        # Load the diff
        diff_path = os.path.join(fixtures_dir, f"{fixture_name}.diff")
        with open(diff_path, "r") as f:
            diff_text = f.read()
        
        # Load expected message
        expected_path = os.path.join(fixtures_dir, f"{fixture_name}.expected.txt")
        with open(expected_path, "r") as f:
            expected_text = f.read().strip()
        
        # Create a generator with mocked Ollama client
        generator = CommitMessageGenerator()
        generator.ollama_client = MagicMock()
        
        # Mock the _generate_message method to return the expected message
        with patch.object(generator, "_generate_message", return_value=expected_text):
            # Generate a commit message
            message = generator.generate_from_diff(diff_text)
            
            # Verify it matches expectations
            assert message == expected_text
            
            # Verify the pipeline was called with appropriate diff data
            assert generator.ollama_client.generate.call_count == 0  # We mocked _generate_message