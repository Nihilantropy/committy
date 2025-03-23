"""Command-line interface for Committy."""

import argparse
import logging
import os
import sys
from typing import List, Optional, Dict, Any

from committy.core.engine import process_diff, Engine
from committy.utils.config import load_config, get_default_config_path

# Configure logger
logger = logging.getLogger(__name__)


def setup_logging(verbose: bool = False):
    """Set up logging configuration.
    
    Args:
        verbose: Whether to enable verbose logging
    """
    log_level = logging.DEBUG if verbose else logging.INFO
    
    # Configure root logger
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(stream=sys.stdout)
        ]
    )
    
    # Set specific loggers to higher levels to reduce noise
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("requests").setLevel(logging.WARNING)


def parse_args(args: List[str]) -> Dict[str, Any]:
    """Parse command-line arguments.
    
    Args:
        args: List of command line arguments
        
    Returns:
        Dictionary of parsed arguments
    """
    parser = argparse.ArgumentParser(
        description="Committy - AI-powered git commit message generator"
    )
    
    # Primary command options
    parser.add_argument(
        "--help", "-h", action="store_true",
        help="Display help information"
    )
    parser.add_argument(
        "--version", "-v", action="store_true",
        help="Display version information"
    )
    parser.add_argument(
        "--dry-run", "-d", action="store_true",
        help="Generate a commit message without committing"
    )
    parser.add_argument(
        "--format", "-f", type=str, default="conventional",
        choices=["conventional", "angular", "simple"],
        help="Specify commit message format"
    )
    parser.add_argument(
        "--model", "-m", type=str,
        help="Specify the LLM model to use"
    )
    parser.add_argument(
        "--edit", "-e", action="store_true",
        help="Open the generated message in an editor before committing"
    )
    parser.add_argument(
        "--config", "-c", type=str,
        help="Specify config file location"
    )
    parser.add_argument(
        "--init-config", action="store_true",
        help="Generate default configuration file"
    )
    parser.add_argument(
        "--verbose", action="store_true",
        help="Increase output verbosity"
    )
    parser.add_argument(
        "--no-confirm", action="store_true",
        help="Skip confirmation step"
    )
    parser.add_argument(
        "--with-scope", action="store_true",
        help="Force inclusion of scope in commit message"
    )
    parser.add_argument(
        "--max-tokens", type=int,
        help="Limit the LLM output token count"
    )
    
    # Parse arguments
    parsed_args = parser.parse_args(args)
    
    # Convert to dictionary
    return vars(parsed_args)


def display_version():
    """Display version information."""
    from committy import __version__
    print(f"Committy v{__version__}")
    print("AI-powered git commit message generator")
    print("https://github.com/claudio/committy")


def prompt_confirmation(message: str) -> bool:
    """Prompt user for confirmation.
    
    Args:
        message: Commit message to confirm
        
    Returns:
        True if user confirms, False otherwise
    """
    print("\nGenerated commit message:")
    print("------------------------")
    print(message)
    print("------------------------")
    
    try:
        response = input("\nConfirm commit with this message? [Y/n/e(dit)]: ").strip().lower()
        if response == "" or response == "y":
            return True
        elif response == "e":
            # Open in editor
            edited_message = open_editor(message)
            if edited_message.strip():
                print("\nUpdated commit message:")
                print("------------------------")
                print(edited_message)
                print("------------------------")
                
                # Confirm edited message
                edit_response = input("\nCommit with this edited message? [Y/n]: ").strip().lower()
                if edit_response == "" or edit_response == "y":
                    return True
        
        return False
    except (KeyboardInterrupt, EOFError):
        print("\nOperation cancelled by user")
        return False


def open_editor(text: str) -> str:
    """Open text in the user's default editor.
    
    Args:
        text: Text to edit
        
    Returns:
        Edited text
    """
    import tempfile
    import subprocess
    
    editor = os.environ.get("EDITOR", "vim")
    
    with tempfile.NamedTemporaryFile(suffix=".txt", mode="w+", delete=False) as tf:
        tf.write(text)
        tf.flush()
        tempfile_path = tf.name
    
    try:
        subprocess.call([editor, tempfile_path])
        
        with open(tempfile_path, "r") as tf:
            edited_text = tf.read()
        
        return edited_text
    finally:
        os.unlink(tempfile_path)


def handle_command(parsed_args: Dict[str, Any]) -> int:
    """Handle the main command based on parsed arguments.
    
    Args:
        parsed_args: Dictionary of parsed arguments
        
    Returns:
        Exit code (0 for success, non-zero for error)
    """
    # Setup logging
    setup_logging(parsed_args.get("verbose", False))
    
    # Handle version display
    if parsed_args.get("version"):
        display_version()
        return 0
    
    # Handle config initialization
    if parsed_args.get("init_config"):
        from committy.utils.config import create_default_config
        config_path = parsed_args.get("config") or get_default_config_path()
        if create_default_config(config_path):
            print(f"Default configuration created at: {config_path}")
            return 0
        else:
            print(f"Error: Failed to create configuration at: {config_path}")
            return 1
    
    # Process git diff and generate commit message
    try:
        # Create engine options
        options = {
            "diff_text": None,  # Will be obtained from git
            "change_type": None,  # Will be detected
            "format_type": parsed_args.get("format", "conventional"),
            "model": parsed_args.get("model")
        }
        
        print("Analyzing changes... ⏳")
        
        # Process the diff
        success, result = process_diff(
            config_path=parsed_args.get("config")
        )
        
        if not success:
            print(f"Error: {result}")
            return 1
        
        # Dry run mode just prints the message
        if parsed_args.get("dry_run"):
            print("\nGenerated commit message:")
            print("------------------------")
            print(result)
            print("------------------------")
            return 0
        
        # Prompt for confirmation unless --no-confirm
        if not parsed_args.get("no_confirm") and not prompt_confirmation(result):
            print("Commit cancelled")
            return 0
        
        # Execute the commit
        engine = Engine(config_path=parsed_args.get("config"))
        if engine.execute_commit(result):
            print("Commit successful!")
            return 0
        else:
            print("Error: Failed to execute commit")
            return 1
        
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=parsed_args.get("verbose", False))
        print(f"Error: {str(e)}")
        return 1


def main(args: Optional[List[str]] = None) -> int:
    """Run the Committy CLI application.
    
    Args:
        args: Command line arguments (defaults to sys.argv[1:])
        
    Returns:
        Exit code (0 for success, non-zero for error)
    """
    try:
        if args is None:
            args = sys.argv[1:]
        
        parsed_args = parse_args(args)
        return handle_command(parsed_args)
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return 1


if __name__ == "__main__":
    sys.exit(main())