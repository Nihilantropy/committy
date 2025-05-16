"""Git diff utilities for Committy."""

import logging
import os
import subprocess
from typing import List, Optional

# Configure logger
logger = logging.getLogger(__name__)


def get_all_changes() -> str:
    """Get all changes (staged and unstaged) from git.
    
    Returns:
        Git diff text including both staged and unstaged changes
        
    Raises:
        RuntimeError: If git command fails or no changes are found
    """
    try:
        # Check if we're in a git repository
        if not is_git_repository():
            raise RuntimeError("Not a git repository")
        
        # First try to get staged changes
        staged_changes = ""
        try:
            staged_changes = _run_git_command([
                "diff", 
                "--staged", 
                "--patch", 
                "--unified=3", 
                "--no-color"
            ])
            logger.debug("Found staged changes")
        except Exception:
            logger.debug("No staged changes found")
        
        # Then try to get unstaged changes
        unstaged_changes = ""
        try:
            unstaged_changes = _run_git_command([
                "diff", 
                "--patch", 
                "--unified=3", 
                "--no-color"
            ])
            logger.debug("Found unstaged changes")
        except Exception:
            logger.debug("No unstaged changes found")
        
        # Combine changes (staged first, then unstaged)
        all_changes = ""
        if staged_changes:
            all_changes += staged_changes
        if unstaged_changes:
            # Add a separator if we already have staged changes
            if all_changes:
                all_changes += "\n\n"
            all_changes += unstaged_changes
        
        # Check if we have any changes
        if not all_changes:
            logger.info("No changes found (staged or unstaged)")
            raise RuntimeError("No changes found")
            
        return all_changes
    except RuntimeError:
        # Re-raise specific runtime errors
        raise
    except Exception as e:
        logger.error(f"Error getting git changes: {e}")
        raise RuntimeError(f"Failed to get git changes: {str(e)}")


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
        diff_text = _run_git_command([
            "diff", 
            "--patch", 
            "--unified=3", 
            "--no-color"
        ])
        
        if not diff_text:
            # No unstaged changes
            logger.warning("No unstaged changes found")
            raise RuntimeError("No unstaged changes found")
            
        return diff_text
    except Exception as e:
        logger.error(f"Error getting unstaged git diff: {e}", exc_info=True)
        raise RuntimeError(f"Failed to get unstaged git diff: {str(e)}")

def stage_all() -> bool:
    """Stage all changes.
    
    Returns:
        True if staging was successful, False otherwise
    """
    try:
        # Check if we're in a git repository
        if not is_git_repository():
            logger.error("Not a git repository")
            return False
        
        # Stage all changes
        _run_git_command(["add", "-A"])
        
        logger.info("All changes staged")
        return True
    except Exception as e:
        logger.error(f"Error staging changes: {e}", exc_info=True)
        return False

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
    
def push() -> bool:
    """Push committed changes to the remote repository.
    
    Returns:
        True if push was successful, False otherwise
    """
    try:
        # Check if we're in a git repository
        if not is_git_repository():
            logger.error("Not a git repository")
            return False
        
        # Get current branch
        current_branch = _run_git_command(["branch", "--show-current"]).strip()
        
        # Push to remote
        _run_git_command(["push", "origin", current_branch])
        
        logger.info(f"Successfully pushed to branch {current_branch}")
        return True
    except Exception as e:
        logger.error(f"Error pushing changes: {e}", exc_info=True)
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