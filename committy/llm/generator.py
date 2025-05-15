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
    enhance_commit_message,
    generate_prompt
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
            change_type: Optional change type (not used in simplified version)
            use_specialized_template: Whether to use specialized templates (not used in simplified version)
            
        Returns:
            Generated commit message
        """
        # Log information about the diff
        logger.info(
            f"Generating commit message for diff of length {len(diff_text)}"
        )
        
        # Get model name for template selection
        model_name = self.model_config.get("model", "")
        
        # Generate a simple prompt
        prompt = generate_prompt(diff_text, model_name)
        
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
    
    def _build_prompt(
        self,
        context: str,
        change_type: Optional[str] = None,
        model_name: Optional[str] = None,
        use_specialized_template: bool = True
    ) -> str:
        """Build an optimized prompt for the LLM.
        
        Args:
            context: Diff context
            change_type: Optional change type
            model_name: Model name for size-based optimization
            use_specialized_template: Whether to use specialized templates
            
        Returns:
            Optimized prompt for the LLM
        """
        # Detect change type if not provided and specialized templates are requested
        if change_type is None and use_specialized_template:
            change_type = detect_likely_change_type(context)
            logger.info(f"Detected change type: {change_type or 'unknown'}")
        
        # Use specialized templates only if requested and change type is available
        if not use_specialized_template:
            change_type = None
            
        # Generate the optimized prompt using our new function
        # This will automatically handle model size and template selection
        prompt = generate_commit_prompt(context, change_type, model_name)
        
        logger.debug(f"Generated prompt for model {model_name or 'default'} with change type {change_type or 'generic'}")
        return prompt
    
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
                
                # Check if the message is empty
                if not message.strip():
                    raise ValueError("Model returned an empty response, please try again or use a different model")
                    
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
    
    # [rest of the class methods remain unchanged]


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