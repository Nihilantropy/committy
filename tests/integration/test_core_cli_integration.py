"""Integration tests for core engine and CLI components."""

import os
import tempfile
import pytest
from unittest.mock import patch, MagicMock

from committy.core.engine import Engine, process_diff
from committy.cli.main import handle_command, main


class TestCoreCLIIntegration:
    """Integration tests for core engine and CLI components."""
    
    @patch("committy.git.diff.get_diff")
    @patch("committy.core.engine.generate_commit_message")
    def test_cli_to_engine_pipeline(self, mock_generate, mock_get_diff):
        """Test the integrated flow from CLI to core engine."""
        # Setup mocks
        mock_get_diff.return_value = "test diff"
        mock_generate.return_value = "feat(test): add new feature"
        
        # Run the CLI handler with dry run mode
        result = handle_command({
            "dry_run": True,
            "format": "conventional",
            "model": "test-model",
            "verbose": 0
        })
        
        # Verify result
        assert result == 0
        
        # Verify methods were called
        assert mock_get_diff.call_count > 0
        mock_generate.assert_called_once()
        assert "test diff" in str(mock_generate.call_args)
    
    @patch("committy.cli.main.process_diff")
    @patch("committy.cli.main.Engine")
    @patch("committy.git.diff.get_diff")
    @patch("committy.cli.main.prompt_confirmation")
    def test_cli_confirmation_workflow(
        self, mock_prompt, mock_get_diff, mock_engine_class, mock_process
    ):
        """Test the CLI confirmation workflow with the engine."""
        # Setup mocks
        mock_get_diff.return_value = "test diff"
        mock_process.return_value = (True, "feat(test): add new feature")
        mock_prompt.return_value = (True, "feat(test): add new feature with edit")
        
        mock_engine = MagicMock()
        mock_engine.execute_commit.return_value = True
        mock_engine_class.return_value = mock_engine
        
        # Run the CLI handler
        result = handle_command({})
        
        # Verify result
        assert result == 0
        
        # Verify methods were called
        mock_get_diff.assert_called_once()
        mock_process.assert_called_once()
        mock_prompt.assert_called_once()
        
        # Verify the confirmation process happened
        mock_engine.execute_commit.assert_called_once_with("feat(test): add new feature with edit")
    
    @patch("committy.cli.main.process_diff")
    @patch("committy.cli.main.Engine")
    @patch("committy.git.diff.get_diff")
    def test_cli_no_confirm_workflow(self, mock_get_diff, mock_engine_class, mock_process):
        """Test the CLI workflow with no confirmation."""
        # Setup mocks
        mock_get_diff.return_value = "test diff"
        mock_process.return_value = (True, "feat(test): add new feature")
        
        mock_engine = MagicMock()
        mock_engine.execute_commit.return_value = True
        mock_engine_class.return_value = mock_engine
        
        # Run the CLI handler with no_confirm
        result = handle_command({"no_confirm": True})
        
        # Verify result
        assert result == 0
        
        # Verify methods were called
        mock_get_diff.assert_called_once()
        mock_process.assert_called_once()
        
        # Verify the engine executed the commit directly
        mock_engine.execute_commit.assert_called_once_with("feat(test): add new feature")
    
    @patch("committy.cli.main.handle_command")
    def test_main_to_handler_integration(self, mock_handler):
        """Test integration between main and handler."""
        # Setup mock
        mock_handler.return_value = 0
        
        # Call main with arguments
        result = main(["--dry-run", "--model=test-model"])
        
        # Verify handler was called with parsed args
        mock_handler.assert_called_once()
        call_args = mock_handler.call_args[0][0]
        assert call_args["dry_run"] is True
        assert call_args["model"] == "test-model"
        
        # Verify main returned the handler result
        assert result == 0
    
    @patch("committy.cli.main.open_editor")
    @patch("committy.cli.main.process_diff")
    @patch("committy.git.diff.get_diff")
    def test_cli_edit_workflow(self, mock_get_diff, mock_process, mock_editor):
        """Test the CLI workflow with edit flag."""
        # Setup mocks
        mock_get_diff.return_value = "test diff"
        mock_process.return_value = (True, "feat(test): add new feature")
        mock_editor.return_value = "feat(test): edited message"
        
        # Run the CLI handler with edit flag and no_confirm
        with patch("committy.cli.main.Engine") as mock_engine_class:
            mock_engine = MagicMock()
            mock_engine.execute_commit.return_value = True
            mock_engine_class.return_value = mock_engine
            
            result = handle_command({
                "edit": True,
                "no_confirm": True
            })
        
        # Verify result
        assert result == 0
        
        # Verify editor was called
        mock_editor.assert_called_once_with("feat(test): add new feature")
        
        # Verify edited message was used
        mock_engine.execute_commit.assert_called_once_with("feat(test): edited message")
    
def test_engine_process_diff_integration():
    """Test process_diff integration within the Engine class."""
    # Create a temporary config file
    with tempfile.NamedTemporaryFile(mode="w", delete=False) as tmp:
        tmp.write("model: test-model\nformat: conventional\n")
        config_path = tmp.name
    
    try:
        # Create a patch for the Engine class
        with patch("committy.core.engine.Engine") as mock_engine_class:
            # Setup the mock
            mock_engine = MagicMock()
            mock_engine.process.return_value = (True, "feat(test): add new feature")
            mock_engine_class.return_value = mock_engine
            
            # Call process_diff
            from committy.core.engine import process_diff
            success, result = process_diff(config_path=config_path)
            
            # Verify result
            assert success is True
            assert result == "feat(test): add new feature"
            
            # Verify Engine was initialized with correct config
            mock_engine_class.assert_called_once_with(config_path=config_path)
            
            # Verify process was called with expected options
            mock_engine.process.assert_called_once()
    finally:
        # Clean up
        os.unlink(config_path)