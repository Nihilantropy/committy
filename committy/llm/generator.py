"""Commit message generator module.

This module provides the main entry point for generating commit messages
from git diffs using LLMs and prompt engineering.
"""

import logging
import time
from typing import Dict, Any, Optional, Tuple, List, Union

from committy.git.models import GitDiff
from committy.git.parser import parse_diff
from committy.llm.index import build_prompt_from_diff
from committy.llm.ollama import OllamaClient, get_default_model_config
from committy.llm.prompts import (
    get_prompt_for_diff,
    detect_likely_change_type,
    enhance_commit_message
)

# Configure logger
logger = logging.getLogger(__name__)


class CommitMessageGenerator:
    """Generator for commit messages."""
    
    def __init__(
        self,
        model_config: Optional[Dict[str, Any]] = None,
        max_context_tokens: int = 4000,
        max_retries: int = 3,
        retry_delay: int = 2
    ):
        """Initialize the commit message generator.
        
        Args:
            model_config: Model configuration dictionary. If None, uses default.
            max_context_tokens: Maximum tokens to include in the context.
            max_retries: Maximum number of retries for API calls.
            retry_delay: Delay between retries in seconds.
        """
        self.model_config = model_config or get_default_model_config()
        self.ollama_client = OllamaClient()
        self.max_context_tokens = max_context_tokens
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        logger.info(f"Initialized generator with model: {self.model_config['model']}")
    
    def generate_from_diff(
        self,
        diff_text: str,
        change_type: Optional[str] = None,
        use_specialized_template: bool = True
    ) -> str:
        """Generate a commit message from a git diff.
        
        Args:
            diff_text: Git diff text
            change_type: Optional change type to use for template selection
            use_specialized_template: Whether to use specialized templates
            
        Returns:
            Generated commit message
        """
        # Parse the diff
        git_diff = parse_diff(diff_text)
        diff_data = git_diff.as_dict()
        
        logger.info(
            f"Generating commit message for diff with "
            f"{len(git_diff.files)} files, "
            f"{git_diff.summary.total_additions} additions, "
            f"{git_diff.summary.total_deletions} deletions"
        )
        
        # Build context from diff data
        context = self._build_context(diff_data)
        
        # Detect change type if not provided
        if not change_type and use_specialized_template:
            change_type = detect_likely_change_type(context)
            logger.info(f"Detected change type: {change_type or 'unknown'}")
        
        # Get appropriate prompt template
        if use_specialized_template and change_type:
            prompt = get_prompt_for_diff(context, change_type)
        else:
            prompt = get_prompt_for_diff(context)
        
        # Generate commit message
        raw_message = self._generate_message(prompt)
        
        # Enhance and return the message
        return enhance_commit_message(raw_message)
    
    def _build_context(self, diff_data: Dict[str, Any]) -> str:
        """Build context from diff data.
        
        Args:
            diff_data: Dictionary with git diff information
            
        Returns:
            Context string for prompting
        """
        # Use LlamaIndex to extract context
        return build_prompt_from_diff(diff_data, self.max_context_tokens)
    
    def _generate_message(self, prompt: str) -> str:
        """Generate a commit message using the LLM.
        
        Args:
            prompt: Prompt string
            
        Returns:
            Generated commit message
        """
        attempts = 0
        last_error = None
        
        while attempts < self.max_retries:
            try:
                logger.debug("Generating commit message")
                message = self.ollama_client.generate(prompt, self.model_config)
                return message.strip()
            except Exception as e:
                last_error = e
                attempts += 1
                logger.warning(
                    f"Error generating message (attempt {attempts}/{self.max_retries}): {e}"
                )
                
                if attempts < self.max_retries:
                    # Wait before retrying
                    time.sleep(self.retry_delay)
        
        # If we reach here, all retries failed
        logger.error(f"Failed to generate message after {self.max_retries} attempts: {last_error}")
        raise RuntimeError(f"Failed to generate commit message: {last_error}")

    def analyze_diff(
        self, 
        diff_text: str
    ) -> Dict[str, Any]:
        """Analyze diff for key information.
        
        Args:
            diff_text: Git diff text
            
        Returns:
            Dictionary with analysis results
        """
        # Parse diff
        git_diff = parse_diff(diff_text)
        
        # Build basic analysis
        analysis = {
            "files_changed": len(git_diff.files),
            "additions": git_diff.summary.total_additions,
            "deletions": git_diff.summary.total_deletions,
            "languages": git_diff.summary.languages,
            "file_types": self._get_file_types(git_diff),
            "change_categories": self._categorize_changes(git_diff),
        }
        
        # Determine likely change type
        context = self._build_context(git_diff.as_dict())
        analysis["likely_change_type"] = detect_likely_change_type(context)
        
        return analysis
    
    def _get_file_types(self, git_diff: GitDiff) -> Dict[str, int]:
        """Get count of file types in the diff.
        
        Args:
            git_diff: Git diff object
            
        Returns:
            Dictionary of file type counts
        """
        file_types = {}
        
        for file in git_diff.files:
            ext = file.extension or "no_extension"
            if ext.startswith("."):
                ext = ext[1:]
            
            file_types[ext] = file_types.get(ext, 0) + 1
        
        return file_types
    
    def _categorize_changes(self, git_diff: GitDiff) -> Dict[str, int]:
        """Categorize changes in the diff.
        
        Args:
            git_diff: Git diff object
            
        Returns:
            Dictionary of change category counts
        """
        categories = {
            "added": 0,
            "modified": 0,
            "deleted": 0,
            "renamed": 0,
            "binary": 0,
        }
        
        for file in git_diff.files:
            if file.change_type in categories:
                categories[file.change_type] += 1
            
            # Check for binary files
            if "Binary file" in file.diff_content:
                categories["binary"] += 1
        
        return categories


def generate_commit_message(
    diff_text: str,
    change_type: Optional[str] = None,
    model_config: Optional[Dict[str, Any]] = None,
    use_specialized_template: bool = True
) -> str:
    """Generate a commit message from a git diff.
    
    This is a convenience function that creates a CommitMessageGenerator
    and uses it to generate a commit message.
    
    Args:
        diff_text: Git diff text
        change_type: Optional change type to use for template selection
        model_config: Optional model configuration dictionary
        use_specialized_template: Whether to use specialized templates
        
    Returns:
        Generated commit message
    """
    generator = CommitMessageGenerator(model_config)
    return generator.generate_from_diff(
        diff_text,
        change_type,
        use_specialized_template
    )


def analyze_diff(diff_text: str) -> Dict[str, Any]:
    """Analyze a git diff for key information.
    
    This is a convenience function that creates a CommitMessageGenerator
    and uses it to analyze a diff.
    
    Args:
        diff_text: Git diff text
        
    Returns:
        Dictionary with analysis results
    """
    generator = CommitMessageGenerator()
    return generator.analyze_diff(diff_text)