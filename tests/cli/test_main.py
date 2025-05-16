"""Tests for CLI entry point and argument parsing."""

import sys
import pytest
from unittest.mock import patch, MagicMock

from committy.cli.main import parse_args, main


class TestArgumentParsing:
    """Test the argument parsing functionality."""

    def test_parse_args_defaults(self):
        """Test parsing arguments with default values."""
        # When parsing empty arguments
        args = parse_args([])
        
        # Then default values should be set
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
    
    def test_parse_args_with_explicit_options(self):
        """Test parsing arguments with explicitly provided options."""
        # When parsing arguments with explicit options
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
            "--no-color",
            "--max-tokens=123",
            "--analyze"
        ])
        
        # Then options should be correctly parsed
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
        assert args["no_color"] is True
    
    def test_parse_args_short_options(self):
        """Test parsing short option formats."""
        # When parsing short option formats
        args = parse_args([
            "-v",
            "-d",
            "-f", "simple",
            "-m", "test-model",
            "-e",
            "-c", "test-config.yml"
        ])
        
        # Then options should be correctly parsed
        assert args["version"] is True
        assert args["dry_run"] is True
        assert args["format"] == "simple"
        assert args["model"] == "test-model"
        assert args["edit"] is True
        assert args["config"] == "test-config.yml"
    
    def test_parse_args_multiple_verbose(self):
        """Test parsing multiple verbose flags for increasing verbosity levels."""
        # When parsing multiple verbose flags
        args = parse_args(["--verbose", "--verbose", "--verbose"])
        
        # Then verbose count should increment correctly
        assert args["verbose"] == 3


class TestMainFunction:
    """Test the main entry point function."""
    
    @patch("committy.cli.main.parse_args")
    @patch("committy.cli.main.handle_command")
    def test_main_successful_execution(self, mock_handle_command, mock_parse_args):
        """Test main function with successful execution."""
        # Given mocked dependencies
        mock_parse_args.return_value = {"test": "args"}
        mock_handle_command.return_value = 0
        
        # When calling main
        result = main()
        
        # Then args should be parsed and command should be handled
        mock_parse_args.assert_called_once_with(sys.argv[1:])
        mock_handle_command.assert_called_once_with({"test": "args"})
        assert result == 0
    
    @patch("committy.cli.main.parse_args")
    @patch("committy.cli.main.handle_command")
    def test_main_with_custom_args(self, mock_handle_command, mock_parse_args):
        """Test main function with custom arguments."""
        # Given mocked dependencies
        mock_parse_args.return_value = {"version": True}
        mock_handle_command.return_value = 0
        
        # When calling main with custom args
        result = main(["--version"])
        
        # Then args should be parsed with the provided args
        mock_parse_args.assert_called_once_with(["--version"])
        mock_handle_command.assert_called_once_with({"version": True})
        assert result == 0
    
    @patch("committy.cli.main.parse_args")
    @patch("committy.cli.main.handle_command")
    def test_main_with_error_from_handle_command(self, mock_handle_command, mock_parse_args):
        """Test main function when handle_command returns an error code."""
        # Given handle_command returns an error
        mock_parse_args.return_value = {"test": "args"}
        mock_handle_command.return_value = 1
        
        # When calling main
        result = main()
        
        # Then the error code should be propagated
        assert result == 1
    
    @patch("committy.cli.main.parse_args")
    @patch("committy.cli.main.handle_command")
    def test_main_with_exception(self, mock_handle_command, mock_parse_args):
        """Test main function when an exception occurs."""
        # Given handle_command raises an exception
        mock_parse_args.return_value = {"test": "args"}
        mock_handle_command.side_effect = Exception("Test error")
        
        # When calling main
        result = main()
        
        # Then an error code should be returned
        assert result == 1