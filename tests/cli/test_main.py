"""Tests for the CLI main module."""

import os
import sys
import tempfile
import pytest
from unittest.mock import patch, MagicMock

import committy
from committy.cli.main import (
    parse_args,
    setup_logging,
    display_version,
    handle_command,
    main
)

class TestCliMain:
    """Tests for the CLI main module."""
    
    def test_parse_args_defaults(self):
        """Test parsing arguments with defaults."""
        # Test with minimal args
        args = parse_args([])
        
        # Check defaults
        assert args["version"] is False
        assert args["dry_run"] is False
        assert args["format"] == "conventional"
        assert args["model"] is None
        assert args["edit"] is False
        assert args["config"] is None
        assert args["init_config"] is False
        assert args["verbose"] == 0
        assert args["no_confirm"] is False
        assert args["with_scope"] is False
        assert args["max_tokens"] is None
        assert args["analyze"] is False
        assert args["no_color"] is False
    
    def test_parse_args_options(self):
        """Test parsing various command line options."""
        # Test with various options
        args = parse_args([
            "--version",
            "--dry-run",
            "--format=simple",
            "--model=test-model",
            "--edit",
            "--config=test-config.yml",
            "--verbose",
            "--no-confirm",
            "--with-scope",
            "--max-tokens=123",
            "--analyze"
        ])
        
        # Check that options were parsed correctly
        assert args["version"] is True
        assert args["dry_run"] is True
        assert args["format"] == "simple"
        assert args["model"] == "test-model"
        assert args["edit"] is True
        assert args["config"] == "test-config.yml"
        assert args["verbose"] == 1
        assert args["no_confirm"] is True
        assert args["with_scope"] is True
        assert args["max_tokens"] == 123
        assert args["analyze"] is True
    
    def test_parse_args_short_options(self):
        """Test parsing short options."""
        # Test with short options
        args = parse_args([
            "-v",
            "-d",
            "-f", "simple",
            "-m", "test-model",
            "-e",
            "-c", "test-config.yml"
        ])
        
        # Check that options were parsed correctly
        assert args["version"] is True
        assert args["dry_run"] is True
        assert args["format"] == "simple"
        assert args["model"] == "test-model"
        assert args["edit"] is True
        assert args["config"] == "test-config.yml"
    
    def test_parse_args_multiple_verbose(self):
        """Test parsing multiple verbose flags."""
        # Test with multiple verbose flags
        args = parse_args(["--verbose", "--verbose", "--verbose"])
        
        # Check that verbose count is correct
        assert args["verbose"] == 3
    
    @patch("logging.basicConfig")
    def test_setup_logging(self, mock_basicConfig):
        """Test setting up logging with different verbosity levels."""
        # Test with default verbosity
        setup_logging()
        
        # Check that basicConfig was called
        mock_basicConfig.assert_called_once()
        
        # Check logger levels
        assert logging.getLogger("urllib3").level == logging.WARNING
        assert logging.getLogger("requests").level == logging.WARNING
        assert logging.getLogger("llama_index").level == logging.WARNING
        
        # Reset mock
        mock_basicConfig.reset_mock()
        
        # Test with verbosity level 1
        setup_logging(1)
        
        # Check logger levels
        assert logging.getLogger("urllib3").level == logging.INFO
        assert logging.getLogger("requests").level == logging.INFO
        assert logging.getLogger("llama_index").level == logging.INFO
        
        # Reset mock
        mock_basicConfig.reset_mock()
        
        # Test with verbosity level 2
        setup_logging(2)
        
        # Check logger levels
        assert logging.getLogger("urllib3").level == logging.DEBUG
        assert logging.getLogger("requests").level == logging.DEBUG
        assert logging.getLogger("llama_index").level == logging.DEBUG
    
    @patch("committy.cli.main.console.print")
    def test_display_version(self, mock_print):
        """Test displaying version information."""
        # Call the function
        display_version()
        
        # Check that console.print was called with version info
        assert mock_print.call_count >= 2
        assert any(f"v{committy.__version__}" in str(call) for call in mock_print.call_args_list)
    
    @patch("committy.cli.main.setup_logging")
    @patch("committy.cli.main.display_version")
    def test_handle_command_version(self, mock_display_version, mock_setup_logging):
        """Test handling version command."""
        # Test with version flag
        result = handle_command({"version": True})
        
        # Check that version was displayed
        mock_display_version.assert_called_once()
        
        # Check that the function returned success
        assert result == 0
    
    @patch("committy.cli.main.setup_logging")
    @patch("committy.cli.main.create_default_config")
    @patch("committy.cli.main.get_default_config_path")
    @patch("committy.cli.main.console.print")
    def test_handle_command_init_config(
        self, mock_print, mock_get_default_path, mock_create_config, mock_setup_logging
    ):
        """Test handling init-config command."""
        # Setup mocks
        mock_get_default_path.return_value = "/default/path/config.yml"
        mock_create_config.return_value = True
        
        # Test with init_config flag
        result = handle_command({"init_config": True})
        
        # Check that config was created
        mock_get_default_path.assert_called_once()
        mock_create_config.assert_called_once_with("/default/path/config.yml")
        
        # Check that success message was printed
        assert mock_print.call_count >= 1
        
        # Check that the function returned success
        assert result == 0
        
        # Test with failed config creation
        mock_create_config.return_value = False
        
        # Reset mocks
        mock_print.reset_mock()
        
        # Call the function
        result = handle_command({"init_config": True})
        
        # Check that error message was printed
        assert mock_print.call_count >= 1
        
        # Check that the function returned error
        assert result == 1
    
    @patch("committy.cli.main.setup_logging")
    @patch("committy.cli.main.get_diff")
    @patch("committy.cli.main.display_diff_analysis")
    def test_handle_command_analyze(
        self, mock_display_analysis, mock_get_diff, mock_setup_logging
    ):
        """Test handling analyze command."""
        # Setup mocks
        mock_get_diff.return_value = "test diff"
        
        # Test with analyze flag
        result = handle_command({"analyze": True})
        
        # Check that diff was analyzed
        mock_get_diff.assert_called_once()
        mock_display_analysis.assert_called_once_with("test diff")
        
        # Check that the function returned success
        assert result == 0
    
    @patch("committy.cli.main.setup_logging")
    @patch("committy.cli.main.get_diff")
    def test_handle_command_no_changes(self, mock_get_diff, mock_setup_logging):
        """Test handling command when no changes are staged."""
        # Setup mock to raise error
        mock_get_diff.side_effect = RuntimeError("No staged changes found")
        
        # Test with default options
        result = handle_command({})
        
        # Check that the function returned error
        assert result == 1
    
    @patch("committy.cli.main.setup_logging")
    @patch("committy.cli.main.get_diff")
    @patch("committy.cli.main.process_diff")
    @patch("committy.cli.main.console")
    def test_handle_command_dry_run(
        self, mock_console, mock_process_diff, mock_get_diff, mock_setup_logging
    ):
        """Test handling dry-run command."""
        # Setup mocks
        mock_get_diff.return_value = "test diff"
        mock_process_diff.return_value = (True, "test message")
        
        # Test with dry_run flag
        result = handle_command({"dry_run": True})
        
        # Check that process_diff was called
        mock_process_diff.assert_called_once()
        
        # Check that message was printed
        assert mock_console.print.call_count >= 1
        
        # Check that the function returned success
        assert result == 0
    
    @patch("committy.cli.main.parse_args")
    @patch("committy.cli.main.handle_command")
    def test_main(self, mock_handle_command, mock_parse_args):
        """Test the main function."""
        # Setup mocks
        mock_parse_args.return_value = {"test": "args"}
        mock_handle_command.return_value = 0
        
        # Test with default args
        result = main()
        
        # Check that args were parsed and command was handled
        mock_parse_args.assert_called_once()
        mock_handle_command.assert_called_once_with({"test": "args"})
        
        # Check that the function returned success
        assert result == 0
        
        # Test with provided args
        mock_parse_args.reset_mock()
        mock_handle_command.reset_mock()
        
        result = main(["--version"])
        
        # Check that args were parsed with provided args
        mock_parse_args.assert_called_once_with(["--version"])
        
        # Test with error in handle_command
        mock_handle_command.return_value = 1
        
        result = main()
        
        # Check that the function returned error
        assert result == 1
        
        # Test with exception
        mock_handle_command.side_effect = Exception("Test error")
        
        result = main()
        
        # Check that the function returned error
        assert result == 1
    
    @patch("committy.cli.main.parse_args")
    @patch("committy.cli.main.handle_command")
    def test_main_as_script(self, mock_handle_command, mock_parse_args):
        """Test the main function when run as a script."""
        # Setup mocks
        mock_parse_args.return_value = {"test": "args"}
        mock_handle_command.return_value = 0
        
        # Save original value of __name__
        original_name = committy.cli.main.__name__
        
        try:
            # Set __name__ to "__main__"
            committy.cli.main.__name__ = "__main__"
            
            # Mock sys.exit
            with patch("sys.exit") as mock_exit:
                # Import the module again to trigger the __name__ == "__main__" block
                import importlib
                importlib.reload(committy.cli.main)
                
                # Check that sys.exit was called with the return value of main
                mock_exit.assert_called_once_with(0)
                
        finally:
            # Restore original value of __name__
            committy.cli.main.__name__ = original_name