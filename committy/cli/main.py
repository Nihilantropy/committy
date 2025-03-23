"""Command-line interface for Committy."""

import argparse
import logging
import os
import shutil
import sys
import time
from pathlib import Path
from typing import List, Optional, Dict, Any, Tuple

from rich.console import Console
from rich.logging import RichHandler
from rich.panel import Panel
from rich.syntax import Syntax
from rich.theme import Theme
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn

from committy.core.engine import process_diff, Engine
from committy.utils.config import load_config, get_default_config_path, create_default_config
from committy import __version__

# Configure logger
logger = logging.getLogger(__name__)

# Create console for rich output
custom_theme = Theme({
    "info": "bold cyan",
    "warning": "bold yellow",
    "error": "bold red",
    "success": "bold green",
    "header": "bold magenta",
    "commit": "green",
    "diff": "blue",
})
console = Console(theme=custom_theme)


def setup_logging(verbosity: int = 0):
    """Set up logging configuration.
    
    Args:
        verbosity: Verbosity level (0=INFO, 1=DEBUG, 2=DEBUG+verbose libs)
    """
    # Determine log level based on verbosity
    if verbosity >= 2:
        log_level = logging.DEBUG
        lib_log_level = logging.DEBUG
    elif verbosity >= 1:
        log_level = logging.DEBUG
        lib_log_level = logging.INFO
    else:
        log_level = logging.INFO
        lib_log_level = logging.WARNING
    
    # Configure root logger with rich handler
    logging.basicConfig(
        level=log_level,
        format="%(message)s",
        datefmt="[%X]",
        handlers=[RichHandler(
            rich_tracebacks=True,
            tracebacks_show_locals=verbosity >= 2,
            show_time=False,
            show_path=verbosity >= 1,
        )]
    )
    
    # Set specific loggers to higher levels to reduce noise
    logging.getLogger("urllib3").setLevel(lib_log_level)
    logging.getLogger("requests").setLevel(lib_log_level)
    logging.getLogger("llama_index").setLevel(lib_log_level)
    
    logger.debug(f"Logging initialized with verbosity level {verbosity}")


def parse_args(args: List[str]) -> Dict[str, Any]:
    """Parse command-line arguments.
    
    Args:
        args: List of command line arguments
        
    Returns:
        Dictionary of parsed arguments
    """
    parser = argparse.ArgumentParser(
        description="Committy - AI-powered git commit message generator",
        epilog="Example: committy --dry-run --model=phi3:mini",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    # Primary command options
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
        help="Specify commit message format (default: conventional)"
    )
    parser.add_argument(
        "--model", "-m", type=str,
        help="Specify the LLM model to use (default: from config)"
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
        "--verbose", action="count", default=0,
        help="Increase output verbosity (can be used multiple times)"
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
    parser.add_argument(
        "--analyze", action="store_true",
        help="Analyze changes without generating a commit message"
    )
    parser.add_argument(
        "--no-color", action="store_true",
        help="Disable colored output"
    )
    
    # Parse arguments
    parsed_args = parser.parse_args(args)
    
    # Convert to dictionary
    return vars(parsed_args)


def display_version():
    """Display version information."""
    console.print(f"[header]Committy[/] [bold]v{__version__}[/]")
    console.print("AI-powered git commit message generator")
    console.print("https://github.com/claudio/committy")


def display_diff_analysis(diff_text: str):
    """Display analysis of the diff.
    
    Args:
        diff_text: Git diff text
    """
    from committy.llm.generator import analyze_diff
    from committy.git.parser import parse_diff
    
    try:
        # Get the analysis
        console.print("[info]Analyzing diff...[/]")
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            TimeElapsedColumn(),
            console=console,
            transient=True
        ) as progress:
            task = progress.add_task("[cyan]Processing...", total=None)
            analysis = analyze_diff(diff_text)
            progress.update(task, completed=True)
        
        # Print summary
        git_diff = parse_diff(diff_text)
        
        console.print("\n[bold]Diff Analysis:[/]")
        console.print(Panel.fit(
            f"Files changed: {analysis['files_changed']}\n"
            f"Additions: {analysis['additions']}\n"
            f"Deletions: {analysis['deletions']}\n"
            f"Languages: {', '.join(analysis['languages'])}\n"
            f"Likely change type: {analysis['likely_change_type'] or 'unknown'}"
        ))
        
        # Display file types
        if analysis['file_types']:
            console.print("\n[bold]File Types:[/]")
            for ext, count in analysis['file_types'].items():
                console.print(f"  • {ext}: {count} file{'s' if count > 1 else ''}")
        
        # Show changed files
        if git_diff.files:
            console.print("\n[bold]Changed Files:[/]")
            for file in git_diff.files:
                change_color = {
                    "added": "green",
                    "modified": "yellow",
                    "deleted": "red"
                }.get(file.change_type, "white")
                
                console.print(
                    f"  • [{change_color}]{file.change_type}[/] {file.path} "
                    f"(+{file.additions}, -{file.deletions})"
                )
        
    except Exception as e:
        logger.error(f"Error analyzing diff: {e}", exc_info=True)
        console.print(f"[error]Error analyzing diff: {e}[/]")


def prompt_confirmation(message: str, edit_option: bool = True) -> Tuple[bool, str]:
    """Prompt user for confirmation.
    
    Args:
        message: Commit message to confirm
        edit_option: Whether to offer edit option
        
    Returns:
        Tuple of (confirmed, possibly_edited_message)
    """
    console.print("\n[bold]Generated commit message:[/]")
    
    # Display the message with syntax highlighting
    syntax = Syntax(
        message,
        "markdown",
        theme="monokai",
        line_numbers=False,
        word_wrap=True
    )
    console.print(Panel(syntax))
    
    try:
        prompt = "\nConfirm commit with this message? "
        if edit_option:
            prompt += "[Y/n/e(dit)]: "
            valid_responses = ["", "y", "n", "e"]
        else:
            prompt += "[Y/n]: "
            valid_responses = ["", "y", "n"]
        
        response = ""
        while response not in valid_responses:
            response = console.input(prompt).strip().lower()
        
        if response == "" or response == "y":
            return True, message
        elif response == "e" and edit_option:
            # Open in editor
            edited_message = open_editor(message)
            if edited_message.strip():
                console.print("\n[bold]Updated commit message:[/]")
                syntax = Syntax(
                    edited_message,
                    "markdown",
                    theme="monokai",
                    line_numbers=False,
                    word_wrap=True
                )
                console.print(Panel(syntax))
                
                # Confirm edited message
                edit_response = console.input("\nCommit with this edited message? [Y/n]: ").strip().lower()
                if edit_response == "" or edit_response == "y":
                    return True, edited_message
        
        return False, message
    except (KeyboardInterrupt, EOFError):
        console.print("\n[warning]Operation cancelled by user[/]")
        return False, message


def open_editor(text: str) -> str:
    """Open text in the user's default editor.
    
    Args:
        text: Text to edit
        
    Returns:
        Edited text
    """
    import tempfile
    import subprocess
    
    editor = os.environ.get("EDITOR", None)
    
    # If no editor is set, try to find one
    if not editor:
        for possible_editor in ["nano", "vim", "vi", "notepad", "code"]:
            if shutil.which(possible_editor):
                editor = possible_editor
                break
    
    if not editor:
        console.print("[error]No editor found. Set the EDITOR environment variable.[/]")
        return text
    
    with tempfile.NamedTemporaryFile(suffix=".md", mode="w+", delete=False) as tf:
        tf.write(text)
        tf.flush()
        tempfile_path = tf.name
    
    try:
        console.print(f"[info]Opening editor: {editor}[/]")
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
    # Disable color if requested
    if parsed_args.get("no_color"):
        console.no_color = True
    
    # Setup logging
    setup_logging(parsed_args.get("verbose", 0))
    
    # Handle version display
    if parsed_args.get("version"):
        display_version()
        return 0
    
    # Handle config initialization
    if parsed_args.get("init_config"):
        config_path = parsed_args.get("config") or get_default_config_path()
        if create_default_config(config_path):
            console.print(f"[success]Default configuration created at: {config_path}[/]")
            return 0
        else:
            console.print(f"[error]Failed to create configuration at: {config_path}[/]")
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
        
        with console.status("[info]Analyzing changes...[/]", spinner="dots") as status:
            # Process the diff
            start_time = time.time()  # Start measuring time
            
            # Get the diff for analysis if needed
            try:
                from committy.git.diff import get_diff
                diff_text = get_diff()
            except Exception as e:
                logger.error(f"Error getting git diff: {e}", exc_info=True)
                console.print(f"[error]Error: {str(e)}[/]")
                return 1
                
            # If only analyzing, display analysis and exit
            if parsed_args.get("analyze"):
                status.stop()
                display_diff_analysis(diff_text)
                return 0
                
            # Otherwise, generate commit message
            success, result = process_diff(
                config_path=parsed_args.get("config")
            )
            
            # Stop timer
            elapsed = time.time() - start_time
            status.stop()
            
        if not success:
            console.print(f"[error]Error: {result}[/]")
            return 1
        
        # Log generation time
        logger.info(f"Commit message generated in {elapsed:.2f} seconds")
        
        # Dry run mode just prints the message
        if parsed_args.get("dry_run"):
            syntax = Syntax(
                result,
                "markdown",
                theme="monokai",
                line_numbers=False,
                word_wrap=True
            )
            console.print("\n[bold]Generated commit message (dry run):[/]")
            console.print(Panel(syntax))
            console.print(f"[info]Generation took {elapsed:.2f} seconds[/]")
            return 0
        
        # Automatically open in editor if requested
        if parsed_args.get("edit"):
            result = open_editor(result)
        
        # Prompt for confirmation unless --no-confirm
        if not parsed_args.get("no_confirm"):
            confirmed, result = prompt_confirmation(result)
            if not confirmed:
                console.print("[warning]Commit cancelled[/]")
                return 0
        
        # Execute the commit
        with console.status("[info]Committing changes...[/]", spinner="dots") as status:
            engine = Engine(config_path=parsed_args.get("config"))
            commit_success = engine.execute_commit(result)
            status.stop()
            
        if commit_success:
            console.print("[success]Commit successful![/]")
            return 0
        else:
            console.print("[error]Failed to execute commit[/]")
            return 1
        
    except KeyboardInterrupt:
        console.print("\n[warning]Operation cancelled by user[/]")
        return 1
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=parsed_args.get("verbose", 0))
        console.print(f"[error]Error: {str(e)}[/]")
        if parsed_args.get("verbose", 0) > 0:
            logger.exception("Detailed exception information:")
        else:
            console.print("[info]Run with --verbose for more details[/]")
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
        console.print(f"[error]Unexpected error: {str(e)}[/]")
        return 1


if __name__ == "__main__":
    sys.exit(main())