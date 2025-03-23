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
    
    def process(self, options: Dict[str, Any]) -> Tuple[bool, str]:
        """Process git diff and generate commit message.
        
        Args:
            options: Dictionary of options for processing
                - diff_text: Git diff text (optional)
                - change_type: Type of change (optional)
                - format_type: Format for commit message (optional)
                - model: LLM model to use (optional)
            
        Returns:
            Tuple of (success, result)
                - success: True if processing was successful
                - result: Generated commit message or error message
        """
        try:
            # Extract options
            diff_text = options.get("diff_text")
            change_type = options.get("change_type")
            format_type = options.get("format_type", self.config.get("format", "conventional"))
            model_name = options.get("model", self.config.get("model"))
            
            # Get the diff text if not provided
            if not diff_text:
                diff_text = self.get_diff_from_git()
                if not diff_text:
                    return False, "No staged changes found"
            
            logger.info("Processing git diff")
            logger.debug(f"Change type: {change_type}, Format: {format_type}, Model: {model_name}")
            
            # Analyze diff to determine change type if not provided
            if not change_type:
                change_type = self.analyze_changes(diff_text)
                logger.info(f"Detected change type: {change_type}")
            
            # Generate commit message
            message = self.generate_message(diff_text, change_type, format_type, model_name)
            
            return True, message
            
        except Exception as e:
            logger.error(f"Error processing git diff: {e}", exc_info=True)
            return False, f"Error: {str(e)}"
    
    def get_diff_from_git(self) -> str:
        """Get diff from git staged changes.
        
        Returns:
            Git diff text
        """
        try:
            # Import here to avoid circular imports
            from committy.git.diff import get_diff
            return get_diff()
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
            
            # Use prompt detection from existing code
            from committy.llm.prompts import detect_likely_change_type
            from committy.llm.index import build_prompt_from_diff
            
            # Build context and detect change type
            context = build_prompt_from_diff(git_diff.as_dict())
            change_type = detect_likely_change_type(context)
            
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
        try:
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
        except Exception as e:
            logger.error(f"Error generating commit message: {e}", exc_info=True)
            # Fallback to a basic message if LLM fails
            return self.fallback_message(diff_text, change_type)
    
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
) -> Tuple[bool, str]:
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
        Tuple of (success, result)
    """
    engine = Engine(config_path=config_path)
    options = {
        "diff_text": diff_text,
        "change_type": change_type,
        "format_type": format_type,
        "model": model_name
    }
    return engine.process(options)