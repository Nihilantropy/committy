"""Tests for the Core Engine module."""

import pytest
from unittest.mock import patch, MagicMock

from committy.core.engine import Engine, process_diff


class TestEngine:
    """Tests for the Engine class."""
    
    @patch("committy.core.engine.load_config")
    def test_init(self, mock_load_config):
        """Test engine initialization."""
        # Setup mock
        mock_load_config.return_value = {"model": "test-model"}
        
        # Create engine
        engine = Engine(config_path="test_config.yml")
        
        # Verify config was loaded
        mock_load_config.assert_called_once_with("test_config.yml")
        assert engine.config == {"model": "test-model"}
    
    @patch("committy.core.engine.parse_diff")
    @patch("committy.llm.prompts.detect_likely_change_type")
    @patch("committy.llm.index.build_prompt_from_diff")
    def test_analyze_changes(self, mock_build_prompt, mock_detect, mock_parse_diff):
        """Test analyzing changes to determine commit type."""
        # Setup mocks
        mock_parse_diff.return_value.as_dict.return_value = {"test": "data"}
        mock_build_prompt.return_value = "test context"
        mock_detect.return_value = "feat"
        
        # Create engine
        engine = Engine()
        
        # Test analyze_changes
        result = engine.analyze_changes("test diff text")
        
        # Verify correct method calls
        mock_parse_diff.assert_called_once_with("test diff text")
        mock_build_prompt.assert_called_once_with({"test": "data"})
        mock_detect.assert_called_once_with("test context")
        
        # Verify result
        assert result == "feat"
    
    @patch("committy.core.engine.generate_commit_message")
    def test_generate_message(self, mock_generate):
        """Test message generation from diff text."""
        # Setup mock
        mock_generate.return_value = "test message"
        
        # Create engine
        engine = Engine()
        
        # Test with minimal args
        result = engine.generate_message("test diff")
        
        # Verify correct method calls
        mock_generate.assert_called_once()
        assert mock_generate.call_args[1]["diff_text"] == "test diff"
        assert mock_generate.call_args[1]["change_type"] is None
        
        # Test with all args
        mock_generate.reset_mock()
        result = engine.generate_message(
            "test diff",
            change_type="fix",
            format_type="simple",
            model_name="test-model"
        )
        
        # Verify correct method calls with all args
        mock_generate.assert_called_once()
        assert mock_generate.call_args[1]["diff_text"] == "test diff"
        assert mock_generate.call_args[1]["change_type"] == "fix"
        assert mock_generate.call_args[1]["model_config"]["model"] == "test-model"
    
    @patch("committy.git.diff.get_diff")
    @patch("committy.core.engine.Engine.analyze_changes")
    @patch("committy.core.engine.Engine.generate_message")
    def test_process(self, mock_generate, mock_analyze, mock_get_diff):
        """Test the process method."""
        # Setup mocks
        mock_get_diff.return_value = "test diff"
        mock_analyze.return_value = "feat"
        mock_generate.return_value = "test message"
        
        # Create engine
        engine = Engine()
        
        # Test with minimal options
        success, result = engine.process({})
        
        # Verify correct method calls
        mock_get_diff.assert_called_once()
        mock_analyze.assert_called_once_with("test diff")
        mock_generate.assert_called_once()
        
        # Verify result
        assert success is True
        assert result == "test message"
        
        # Test with provided diff
        mock_get_diff.reset_mock()
        mock_analyze.reset_mock()
        mock_generate.reset_mock()
        
        options = {
            "diff_text": "provided diff",
            "change_type": "fix",
            "format_type": "simple",
            "model": "test-model"
        }
        
        success, result = engine.process(options)
        
        # Verify correct method calls
        mock_get_diff.assert_not_called()
        mock_analyze.assert_not_called()  # change_type was provided
        mock_generate.assert_called_once_with(
            "provided diff", "fix", "simple", "test-model"
        )
        
        # Verify result
        assert success is True
        assert result == "test message"
    
    @patch("committy.git.diff.get_diff")
    def test_process_no_staged_changes(self, mock_get_diff):
        """Test process method when no staged changes found."""
        # Setup mock to raise an error
        mock_get_diff.side_effect = RuntimeError("No staged changes found")
        
        # Create engine
        engine = Engine()
        
        # Test process with no diff
        success, result = engine.process({})
        
        # Verify result
        assert success is False
        assert "No staged changes found" in result
    
    @patch("committy.core.engine.generate_commit_message")
    def test_generate_message_error(self, mock_generate):
        """Test error handling in generate_message."""
        # Setup mock to raise error
        mock_generate.side_effect = Exception("LLM error")
        
        # Create engine
        engine = Engine()
        
        # Patch the fallback_message method
        with patch.object(engine, "fallback_message", return_value="fallback message"):
            result = engine.generate_message("test diff")
        
        # Verify fallback was used
        assert result == "fallback message"
    
    @patch("committy.core.engine.parse_diff")
    def test_fallback_message(self, mock_parse_diff):
        """Test fallback message generation."""
        # Setup mock
        mock_diff = MagicMock()
        mock_diff.summary.languages = ["Python"]
        mock_diff.summary.total_additions = 10
        mock_diff.summary.total_deletions = 5
        mock_diff.files = [MagicMock(), MagicMock()]
        mock_parse_diff.return_value = mock_diff
        
        # Create engine
        engine = Engine()
        
        # Test with change type
        result = engine.fallback_message("test diff", "fix")
        
        # Verify result format
        assert result.startswith("fix(python):")
        assert "2 files changed" in result
        assert "+10" in result
        assert "-5" in result
        
        # Test with no change type
        result = engine.fallback_message("test diff")
        
        # Verify result format (default to chore)
        assert result.startswith("chore(python):")
        
        # Test with unknown language
        mock_diff.summary.languages = []
        result = engine.fallback_message("test diff")
        
        # Verify result uses general scope
        assert "chore(general):" in result
    
    @patch("committy.git.diff.commit")
    def test_execute_commit(self, mock_commit):
        """Test executing a git commit."""
        # Setup mock
        mock_commit.return_value = True
        
        # Create engine
        engine = Engine()
        
        # Test successful commit
        result = engine.execute_commit("test message")
        
        # Verify commit was called
        mock_commit.assert_called_once_with("test message")
        assert result is True
        
        # Test failed commit
        mock_commit.return_value = False
        result = engine.execute_commit("test message")
        assert result is False
    
    def test_handle_error(self):
        """Test handling different error types."""
        # Create engine
        engine = Engine()
        
        # Test Ollama connection error
        error = Exception("Could not connect to Ollama")
        result = engine.handle_error(error)
        assert "Could not connect to Ollama service" in result
        assert "See docs/OLLAMA_SETUP.md" in result
        
        # Test model not found error
        error = Exception("Model not found")
        result = engine.handle_error(error)
        assert "Error: The specified model is not available" in result
        
        # Test no staged changes error
        error = Exception("No staged changes found")
        result = engine.handle_error(error)
        assert "Error: No staged changes found" in result
        assert "git add <files>" in result
        
        # Test generic error
        error = Exception("Generic error")
        result = engine.handle_error(error)
        assert "Error: Generic error" in result


@patch("committy.core.engine.Engine")
def test_process_diff_convenience_function(mock_engine_class):
    """Test the process_diff convenience function."""
    # Setup mock
    mock_engine = MagicMock()
    mock_engine.process.return_value = (True, "test message")
    mock_engine_class.return_value = mock_engine
    
    # Call the function
    success, result = process_diff(
        diff_text="test diff",
        change_type="fix",
        format_type="simple",
        model_name="test-model",
        config_path="test_config.yml"
    )
    
    # Verify engine was created with correct config
    mock_engine_class.assert_called_once_with(config_path="test_config.yml")
    
    # Verify process was called with correct options
    mock_engine.process.assert_called_once()
    options = mock_engine.process.call_args[0][0]
    assert options["diff_text"] == "test diff"
    assert options["change_type"] == "fix"
    assert options["format_type"] == "simple"
    assert options["model"] == "test-model"
    
    # Verify result
    assert success is True
    assert result == "test message"