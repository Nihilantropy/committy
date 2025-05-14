"""Git diff utilities for Committy."""

import logging
import os
import subprocess
from typing import List, Optional

# Configure logger
logger = logging.getLogger(__name__)


def get_diff() -> str:
    """Get git diff of staged changes.
    
    Returns:
        Git diff text of staged changes
    
    Raises:
        RuntimeError: If git command fails or no git repository is found
    """
    try:
        # Check if we're in a git repository
        if not is_git_repository():
            raise RuntimeError("Not a git repository")
        
        # Get staged changes
        diff_text = _run_git_command(["diff", "--cached"])
        
        if not diff_text:
            # No staged changes - don't log this as an error, it's a normal condition
            logger.info("No staged changes found")  # Change from warning to info
            raise RuntimeError("No staged changes found")
            
        return diff_text
    except Exception as e:
        # Don't log the error here, let the caller handle it
        # This prevents duplicate error messages
        if "No staged changes found" in str(e):
            # Just re-raise without logging
            raise
        else:
            # For other errors, log but don't show traceback
            logger.error(f"Error getting git diff: {e}")
            raise RuntimeError(f"Failed to get git diff: {str(e)}")


def get_unstaged_diff() -> str:
    """Get git diff of unstaged changes.
    
    Returns:
        Git diff text of unstaged changes
    
    Raises:
        RuntimeError: If git command fails or no git repository is found
    """
    try:
        # Check if we're in a git repository
        if not is_git_repository():
            raise RuntimeError("Not a git repository")
        
        # Get unstaged changes
        diff_text = _run_git_command(["diff"])
        
        if not diff_text:
            # No unstaged changes
            logger.warning("No unstaged changes found")
            raise RuntimeError("No unstaged changes found")
            
        return diff_text
    except Exception as e:
        logger.error(f"Error getting unstaged git diff: {e}", exc_info=True)
        raise RuntimeError(f"Failed to get unstaged git diff: {str(e)}")


def get_changed_files() -> List[str]:
    """Get list of staged files.
    
    Returns:
        List of staged file paths
    
    Raises:
        RuntimeError: If git command fails or no git repository is found
    """
    try:
        # Check if we're in a git repository
        if not is_git_repository():
            raise RuntimeError("Not a git repository")
        
        # Get list of staged files
        output = _run_git_command(["diff", "--cached", "--name-only"])
        
        if not output:
            # No staged files
            logger.warning("No staged files found")
            return []
            
        return output.strip().split("\n")
    except Exception as e:
        logger.error(f"Error getting changed files: {e}", exc_info=True)
        raise RuntimeError(f"Failed to get changed files: {str(e)}")


def commit(message: str) -> bool:
    """Create a git commit with the specified message.
    
    Args:
        message: Commit message
    
    Returns:
        True if commit was successful, False otherwise
    """
    try:
        # Check if we're in a git repository
        if not is_git_repository():
            logger.error("Not a git repository")
            return False
        
        # Create commit
        _run_git_command(["commit", "-m", message])
        
        logger.info("Commit successful")
        return True
    except Exception as e:
        logger.error(f"Error creating commit: {e}", exc_info=True)
        return False


def is_git_repository(path: Optional[str] = None) -> bool:
    """Check if path is a git repository.
    
    Args:
        path: Path to check, defaults to current directory
    
    Returns:
        True if path is a git repository, False otherwise
    """
    try:
        # Set working directory if provided
        cwd = path or os.getcwd()
        
        # Run git rev-parse to check if we're in a git repository
        subprocess.run(
            ["git", "rev-parse", "--is-inside-work-tree"],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=cwd
        )
        
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def _run_git_command(args: List[str]) -> str:
    """Run a git command and return the output.
    
    Args:
        args: Command arguments
    
    Returns:
        Command output
    
    Raises:
        RuntimeError: If git command fails
    """
    try:
        # Run git command
        result = subprocess.run(
            ["git"] + args,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        return result.stdout
    except subprocess.CalledProcessError as e:
        # If the command fails, raise an exception with the error output
        error_message = e.stderr.strip()
        logger.error(f"Git command failed: {error_message}")
        raise RuntimeError(f"Git command failed: {error_message}")
    except FileNotFoundError:
        # If git is not installed, raise an exception
        logger.error("Git command not found, please install git")
        raise RuntimeError("Git command not found, please install git")