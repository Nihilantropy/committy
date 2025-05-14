"""Tests for the commit message generator."""

import pytest
from unittest.mock import patch, MagicMock

from committy.llm.generator import (
    CommitMessageGenerator,
    generate_commit_message,
    analyze_diff
)


class TestCommitMessageGenerator:
    """Tests for the CommitMessageGenerator class."""
    
    def test_init_default(self):
        """Test initialization with default values."""
        generator = CommitMessageGenerator()
        assert generator.max_context_tokens == 4000
        assert generator.max_retries == 3
        assert generator.retry_delay == 2
        assert generator.model_config is not None
        assert "model" in generator.model_config
        assert "parameters" in generator.model_config
    
    def test_init_custom(self):
        """Test initialization with custom values."""
        model_config = {"model": "test-model", "parameters": {"test": "value"}}
        generator = CommitMessageGenerator(
            model_config=model_config,
            max_context_tokens=1000,
            max_retries=5,
            retry_delay=1
        )
        
        assert generator.max_context_tokens == 1000
        assert generator.max_retries == 5
        assert generator.retry_delay == 1
        assert generator.model_config == model_config
    
    @patch("committy.llm.generator.parse_diff")
    @patch("committy.llm.generator.build_prompt_from_diff")
    @patch("committy.llm.generator.detect_likely_change_type")
    @patch("committy.llm.generator.get_prompt_for_diff")
    @patch("committy.llm.generator.CommitMessageGenerator._generate_message")
    @patch("committy.llm.generator.enhance_commit_message")
    def test_generate_from_diff(
        self,
        mock_enhance,
        mock_generate,
        mock_get_prompt,
        mock_detect,
        mock_build_context,
        mock_parse_diff
    ):
        """Test generating a commit message from diff."""
        # Setup mocks
        mock_parse_diff.return_value.as_dict.return_value = {"test": "data"}
        mock_build_context.return_value = "test context"
        mock_detect.return_value = "feat"
        mock_get_prompt.return_value = "test prompt"
        mock_generate.return_value = "test message"
        mock_enhance.return_value = "enhanced message"
        
        # Create generator with mocked Ollama client
        generator = CommitMessageGenerator()
        generator.ollama_client = MagicMock()
        
        # Test with change type
        result = generator.generate_from_diff("test diff", "fix")
        
        # Verify correct method calls
        mock_parse_diff.assert_called_once_with("test diff")
        mock_build_context.assert_called_once_with({"test": "data"}, 4000)
        mock_detect.assert_not_called()  # Should not be called when change_type is provided
        mock_get_prompt.assert_called_once_with("test context", "fix")
        mock_generate.assert_called_once_with("test prompt")
        mock_enhance.assert_called_once_with("test message")
        
        # Verify correct result
        assert result == "enhanced message"
        
        # Reset mocks
        mock_parse_diff.reset_mock()
        mock_build_context.reset_mock()
        mock_detect.reset_mock()
        mock_get_prompt.reset_mock()
        mock_generate.reset_mock()
        mock_enhance.reset_mock()
        
        # Test without change type (auto-detection)
        result = generator.generate_from_diff("test diff")
        
        # Verify correct method calls
        mock_parse_diff.assert_called_once_with("test diff")
        mock_build_context.assert_called_once_with({"test": "data"}, 4000)
        mock_detect.assert_called_once_with("test context")
        mock_get_prompt.assert_called_once_with("test context", "feat")
        mock_generate.assert_called_once_with("test prompt")
        mock_enhance.assert_called_once_with("test message")
        
        # Verify correct result
        assert result == "enhanced message"
    
    @patch("committy.llm.generator.CommitMessageGenerator.generate_from_diff")
    def test_generate_commit_message(self, mock_generate_from_diff):
        """Test generate_commit_message convenience function."""
        # Setup mock
        mock_generate_from_diff.return_value = "test message"
        
        # Test function
        result = generate_commit_message(
            "test diff",
            change_type="fix",
            model_config={"model": "test"},
            use_specialized_template=True
        )
        
        # Verify correct method calls
        mock_generate_from_diff.assert_called_once_with(
            "test diff",
            "fix",
            True
        )
        
        # Verify correct result
        assert result == "test message"
    
    @patch("committy.llm.generator.parse_diff")
    def test_analyze_diff(self, mock_parse_diff):
        """Test analyzing a diff."""
        # Setup mock
        mock_diff = MagicMock()
        mock_diff.files = [MagicMock(), MagicMock()]
        mock_diff.summary.total_additions = 10
        mock_diff.summary.total_deletions = 5
        mock_diff.summary.languages = ["Python", "JavaScript"]
        mock_parse_diff.return_value = mock_diff
        
        # Set up file types for the mock
        mock_diff.files[0].extension = ".py"
        mock_diff.files[1].extension = ".js"
        mock_diff.files[0].change_type = "modified"
        mock_diff.files[1].change_type = "added"
        
        # Create generator with mocked methods
        generator = CommitMessageGenerator()
        generator._build_context = MagicMock(return_value="test context")
        
        # Mock detect_likely_change_type
        with patch("committy.llm.generator.detect_likely_change_type", return_value="feat"):
            result = generator.analyze_diff("test diff")
        
        # Verify result structure
        assert result["files_changed"] == 2
        assert result["additions"] == 10
        assert result["deletions"] == 5
        assert "Python" in result["languages"]
        assert "JavaScript" in result["languages"]
        assert "py" in result["file_types"]
        assert "js" in result["file_types"]
        assert result["change_categories"]["modified"] == 1
        assert result["change_categories"]["added"] == 1
        assert result["likely_change_type"] == "feat"
    
    @patch("committy.llm.generator.OllamaClient.generate")
    def test_generate_message(self, mock_generate):
        """Test message generation with LLM."""
        # Setup mock
        mock_generate.return_value = "generated message"
        
        # Create generator
        generator = CommitMessageGenerator()
        
        # Test successful generation
        result = generator._generate_message("test prompt")
        assert result == "generated message"
        
        # Test retry on error
        mock_generate.side_effect = [
            Exception("Test error"),
            "generated after retry"
        ]
        
        # Patch time.sleep to avoid waiting
        with patch("time.sleep"):
            result = generator._generate_message("test prompt")
            
        assert result == "generated after retry"
        
        # Test max retries exceeded
        mock_generate.side_effect = Exception("Persistent error")
        
        # Patch time.sleep to avoid waiting
        with patch("time.sleep"):
            with pytest.raises(RuntimeError):
                generator._generate_message("test prompt")