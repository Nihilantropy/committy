"""Commit message generator module.

This module provides the main entry point for generating commit messages
from git diffs using LLMs and prompt engineering.
"""

import logging
from typing import Dict, Any, Optional

from autocommit.git.models import GitDiff
from autocommit.git.parser import parse_diff
from autocommit.llm.index import build_prompt_from_diff
from autocommit.llm.ollama import OllamaClient, get_default_model_config
from autocommit.llm.prompts import (
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
        max_context_tokens: int = 4000
    ):
        """Initialize the commit message generator.
        
        Args:
            model_config: Model configuration dictionary. If None, uses default.
            max_context_tokens: Maximum tokens to include in the context.
        """
        self.model_config = model_config or get_default_model_config()
        self.ollama_client = OllamaClient()
        self.max_context_tokens = max_context_tokens
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
        try:
            logger.debug("Generating commit message")
            message = self.ollama_client.generate(prompt, self.model_config)
            return message.strip()
        except Exception as e:
            logger.error(f"Error generating message: {e}")
            return f"Error: {str(e)}"


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