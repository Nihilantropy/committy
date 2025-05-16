"""Core engine for Committy.

This module provides the main entry point for the Committy application,
coordinating the git diff parsing, LLM integration, and commit message generation.
"""

import logging
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Union

from committy.git.parser import parse_diff
from committy.llm.generator import generate_commit_message
from committy.utils.config import load_config

# Configure logger
logger = logging.getLogger(__name__)


class Engine:
    """Core engine for Committy.
    
    This class coordinates all the components of the application to generate
    commit messages from git diffs.
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialize the Committy engine.
        
        Args:
            config_path: Optional path to configuration file
        """
        self.config = load_config(config_path)
        logger.info("Committy engine initialized")
    
    def process(self, options: Dict[str, Any]) -> Tuple[bool, str, bool]:
        """Process git diff and generate commit message.
        
        Args:
            options: Dictionary of options for processing
                - diff_text: Git diff text (optional)
                - change_type: Type of change (optional)
                - format_type: Format for commit message (optional)
                - model: LLM model to use (optional)
            
        Returns:
            Tuple of (success, result, is_staged)
                - success: True if processing was successful
                - result: Generated commit message or error message
                - is_staged: True if changes were already staged, False if unstaged
        """
        try:
            # Extract options
            diff_text = options.get("diff_text")
            change_type = options.get("change_type")
            format_type = options.get("format_type", self.config.get("format", "conventional"))
            model_name = options.get("model", self.config.get("model"))
            is_staged = True  # Default to True if diff_text is provided
            
            # Get the diff text if not provided
            if not diff_text:
                diff_text, is_staged = self.get_diff_from_git()
                if not diff_text:
                    return False, "No changes found (staged or unstaged)", True
            
            logger.info("Processing git diff")
            logger.debug(f"Change type: {change_type}, Format: {format_type}, Model: {model_name}, Staged: {is_staged}")
            
            # Analyze diff to determine change type if not provided
            if not change_type:
                change_type = self.analyze_changes(diff_text)
            
            # Generate commit message
            message = self.generate_message(diff_text, change_type, format_type, model_name)
            
            return True, message, is_staged
            
        except Exception as e:
            logger.error(f"Error processing git diff.", exc_info=True)
            return False, f"Error: {str(e)}", True
    
    def get_diff_from_git(self) -> Tuple[str, bool]:
        """Get diff from git, first checking staged changes, then unstaged if none.
        
        Returns:
            Tuple of (git_diff_text, is_staged)
                - git_diff_text: The git diff content
                - is_staged: True if staged changes, False if unstaged
        """
        try:
            # Import here to avoid circular imports
            from committy.git.diff import get_diff, get_unstaged_diff
            
            # First try to get staged changes
            try:
                diff = get_diff()
                return diff, True  # Staged changes found
            except RuntimeError as e:
                if "No staged changes found" in str(e):
                    # No staged changes, try unstaged
                    diff = get_unstaged_diff()
                    return diff, False  # Unstaged changes found
                else:
                    # Other error, re-raise
                    raise
                    
        except Exception as e:
            logger.error(f"Error getting git diff: {e}", exc_info=True)
            raise RuntimeError(f"Failed to get git diff: {e}")
    
    def analyze_changes(self, diff_text: str) -> Optional[str]:
        """Analyze changes to determine commit type and scope.
        
        Args:
            diff_text: Git diff text
            
        Returns:
            Detected change type or None if could not be determined
        """
        try:
            # Parse the diff
            git_diff = parse_diff(diff_text)
            
            # Use the new detection function directly on the diff text
            # Simpler approach that doesn't require building complex context
            from committy.llm.prompts import detect_likely_change_type
            
            # Get the diff content as a string
            diff_content = diff_text
            
            # Detect change type
            change_type = detect_likely_change_type(diff_content)
            
            logger.debug(f"Detected change type: {change_type or 'unknown'}")
            return change_type
        except Exception as e:
            logger.warning(f"Error analyzing changes: {e}", exc_info=True)
            return None
    
    def generate_message(
        self, 
        diff_text: str, 
        change_type: Optional[str] = None,
        format_type: str = "conventional",
        model_name: Optional[str] = None
    ) -> str:
        """Generate commit message from diff text.
        
        Args:
            diff_text: Git diff text
            change_type: Optional change type
            format_type: Format type for commit message
            model_name: Optional model name
                
        Returns:
            Generated commit message
        """
        # Prepare model config if model name provided
        model_config = None
        if model_name:
            from committy.llm.ollama import get_default_model_config
            model_config = get_default_model_config()
            model_config["model"] = model_name
        
        # Generate commit message
        message = generate_commit_message(
            diff_text=diff_text,
            change_type=change_type,
            model_config=model_config,
            use_specialized_template=(format_type == "conventional")
        )
        
        return message
    
    def fallback_message(self, diff_text: str, change_type: Optional[str] = None) -> str:
        """Generate a fallback commit message when LLM fails.
        
        Args:
            diff_text: Git diff text
            change_type: Optional change type
            
        Returns:
            Basic commit message
        """
        try:
            # Parse the diff
            git_diff = parse_diff(diff_text)
            
            # Determine type
            type_str = change_type or "chore"
            
            # Find most common language for scope
            languages = git_diff.summary.languages
            if not languages:
                scope = "general"
            else:
                scope = languages[0].lower() if languages[0] != "unknown" else "code"
            
            # Build a simple message
            files_changed = len(git_diff.files)
            additions = git_diff.summary.total_additions
            deletions = git_diff.summary.total_deletions
            
            description = f"update {scope} ({files_changed} files changed, +{additions}, -{deletions})"
            
            return f"{type_str}({scope}): {description}"
        except Exception as e:
            logger.error(f"Error generating fallback message: {e}", exc_info=True)
            # Ultra basic fallback
            return "chore: update code"

    def stage_and_commit(self, message: str) -> bool:
        """Stage all changes and commit with the provided message.
        
        Args:
            message: Commit message
            
        Returns:
            True if staging and commit was successful
        """
        try:
            # Import here to avoid circular imports
            from committy.git.diff import stage_all, commit
            
            # Stage all changes
            if not stage_all():
                logger.error("Failed to stage changes")
                return False
                
            # Commit with the message
            return commit(message)
        except Exception as e:
            logger.error(f"Error staging and committing changes: {e}", exc_info=True)
            return False
    
    def execute_commit(self, message: str) -> bool:
        """Execute git commit with generated message.
        
        Args:
            message: Commit message
            
        Returns:
            True if commit was successful
        """
        try:
            # Import here to avoid circular imports
            from committy.git.diff import commit
            return commit(message)
        except Exception as e:
            logger.error(f"Error executing commit: {e}", exc_info=True)
            return False
    
    def handle_error(self, error: Exception) -> str:
        """Handle error and return user-friendly message.
        
        Args:
            error: Exception that occurred
            
        Returns:
            User-friendly error message
        """
        logger.error(f"Error: {error}", exc_info=True)
        
        # Check for specific error types
        if "Could not connect to Ollama" in str(error):
            return (
                "Error: Could not connect to Ollama service.\n"
                "Please ensure Ollama is installed and running.\n"
                "See docs/OLLAMA_SETUP.md for installation instructions."
            )
        elif "Model not found" in str(error) or "Model not available" in str(error):
            return (
                "Error: The specified model is not available in Ollama.\n"
                "Please download it first or choose a different model.\n"
                "See docs/OLLAMA_SETUP.md for more information."
            )
        elif "No staged changes found" in str(error):
            return (
                "Error: No staged changes found. Please stage your changes first:\n"
                "git add <files>"
            )
        else:
            return f"Error: {str(error)}"


def process_diff(
    diff_text: Optional[str] = None,
    change_type: Optional[str] = None,
    format_type: str = "conventional",
    model_name: Optional[str] = None,
    config_path: Optional[str] = None,
) -> Tuple[bool, str, bool]:
    """Process git diff and generate commit message.
    
    This is a convenience function that creates an Engine instance
    and uses it to process the diff.
    
    Args:
        diff_text: Git diff text
        change_type: Optional change type
        format_type: Format for commit message
        model_name: LLM model to use
        config_path: Optional path to configuration file
        
    Returns:
        Tuple of (success, result, is_staged)
    """
    engine = Engine(config_path=config_path)
    options = {
        "diff_text": diff_text,
        "change_type": change_type,
        "format_type": format_type,
        "model": model_name
    }
    return engine.process(options)