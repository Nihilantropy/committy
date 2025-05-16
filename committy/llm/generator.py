"""Commit message generator module.

This module provides the main entry point for generating commit messages
from git diffs using LLMs and prompt engineering.
"""

import logging
import time
from typing import Dict, Any, Optional

from committy.git.parser import parse_diff
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
        retry_delay: int = 2,
        use_file_based_processing: bool = True
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
        self.use_file_based_processing = use_file_based_processing
        logger.info(f"Initialized generator with model: {self.model_config['model']}")
        if self.use_file_based_processing:
            logger.info("File-based processing enabled")

    def generate_from_diff(
        self,
        diff_text,
        change_type=None,
        use_specialized_template=True
    ):
        """Generate a commit message from a git diff.
        
        Args:
            diff_text: Git diff text
            change_type: Optional change type
            use_specialized_template: Whether to use specialized templates
                
        Returns:
            Generated commit message
        """
        # Log information about the diff
        logger.info(f"Generating commit message for diff of length {len(diff_text)}")
        
        # Parse the diff
        git_diff = parse_diff(diff_text)
        
        # Check if we should use file-based processing
        should_use_file_based = (
            self.use_file_based_processing and 
            len(git_diff.files) > 1
        )
        
        if should_use_file_based:
            logger.info(f"Using file-based processing for {len(git_diff.files)} files")
            return self._process_files_sequentially(git_diff, change_type, use_specialized_template)
        else:
            # Use the original method for small diffs or single files
            logger.info("Using traditional processing (single file or file-based processing disabled)")
            
            # Generate a simple prompt
            prompt = generate_prompt(diff_text, self.model_config.get("model", ""))
            
            # Generate commit message
            raw_message = self._generate_message(prompt)
            
            # Enhance and return the message
            return enhance_commit_message(raw_message)

    def _process_files_sequentially(
        self,
        git_diff,
        change_type=None,
        use_specialized_template=True
    ):
        """Process each file in the git diff sequentially.
        
        This builds an understanding of the changes one file at a time,
        generating a cohesive commit message that combines insights from all files.
        
        Args:
            git_diff: Parsed GitDiff object
            change_type: Optional change type
            use_specialized_template: Whether to use specialized templates
                
        Returns:
            Generated commit message
        """
        try:
            # Create summary info about the overall diff
            summary = self._create_diff_summary(git_diff)
            logger.debug(f"Diff summary: {summary}")
            
            # Initialize context tracker
            context = {
                "summary": summary,
                "processed_files": [],
                "insights": []
            }
            
            # Process each file
            for i, file in enumerate(git_diff.files):
                logger.info(f"Processing file {i+1}/{len(git_diff.files)}: {file.path}")
                
                # Generate analysis for this file
                file_insight = self._analyze_file(file, context)
                
                # Update the context with this file's analysis
                context["processed_files"].append(file.path)
                context["insights"].append({
                    "path": file.path,
                    "insight": file_insight
                })
                
                logger.debug(f"Generated insight for {file.path}: {file_insight[:100]}...")
            
            # Generate the final commit message
            final_message = self._synthesize_commit_message(context, change_type, use_specialized_template)
            logger.info("Generated final commit message from file-based analysis")
            
            return final_message
        except Exception as e:
            logger.error(f"Error in file-based processing: {e}", exc_info=True)
            # Fall back to traditional processing
            logger.info("Falling back to traditional processing")
            prompt = generate_prompt(self._reconstruct_diff_text(git_diff), self.model_config.get("model", ""))
            raw_message = self._generate_message(prompt)
            return enhance_commit_message(raw_message)

    def _create_diff_summary(self, git_diff):
        """Create a summary of the entire diff.
        
        Args:
            git_diff: Parsed GitDiff object
            
        Returns:
            Summary string
        """
        return f"""
    Diff Summary:
    - Changed Files: {len(git_diff.files)}
    - Additions: {git_diff.summary.total_additions}
    - Deletions: {git_diff.summary.total_deletions}
    - Languages: {', '.join(git_diff.summary.languages)}
    """

    def _analyze_file(self, file, context):
        """Analyze a single file in the diff.
        
        Args:
            file: FileChange object
            context: Current context dictionary
            
        Returns:
            Insight string for this file
        """
        # Create a prompt focused on this file
        prompt = self._create_file_analysis_prompt(file, context)
        
        # Generate insight
        insight = self._generate_message(prompt)
        
        return insight

    def _create_file_analysis_prompt(self, file, context):
        """Create a prompt for analyzing a specific file.
        
        Args:
            file: FileChange object
            context: Current context dictionary
            
        Returns:
            Prompt string
        """
        summary = context["summary"]
        processed_files = context["processed_files"]
        
        # Build file context
        file_context = f"""
    # File Analysis Task
    Analyze this specific file from a git diff and describe what changed.

    ## File: {file.path}
    Type: {file.language}
    Change: {file.change_type}
    Added lines: {file.additions}
    Removed lines: {file.deletions}

    ## Overall Context
    {summary}

    ## Diff Content
    ```diff
    {file.diff_content}
    ```
    """
        
        # Add previous file contexts if available
        if processed_files:
            file_context += "\n## Already Processed Files\n"
            for path in processed_files:
                file_context += f"- {path}\n"
        
        # Add instructions
        file_context += """
    ## Instructions
    1. Describe what changed in this specific file
    2. Explain why these changes were likely made
    3. Focus on the most significant changes
    4. Be concise but informative
    """
        
        return file_context

    def _synthesize_commit_message(self, context, change_type=None, use_specialized_template=True):
        """Synthesize a final commit message from the file insights.
        
        Args:
            context: Context dictionary with file insights
            change_type: Optional change type
            use_specialized_template: Whether to use specialized templates
            
        Returns:
            Final commit message
        """
        # Create synthesis prompt
        synthesis_prompt = self._create_synthesis_prompt(context, change_type)
        
        # Generate final message
        raw_message = self._generate_message(synthesis_prompt)
        
        # Enhance and return
        return enhance_commit_message(raw_message)

    def _create_synthesis_prompt(self, context, change_type=None):
        """Create a prompt for synthesizing file insights into a commit message.
        
        Args:
            context: Context dictionary with file insights
            change_type: Optional change type
            
        Returns:
            Synthesis prompt
        """
        summary = context["summary"]
        insights = context["insights"]
        
        # Build the synthesis prompt
        prompt = f"""
    # Commit Message Generation Task
    Create a commit message that describes all the changes across multiple files.

    ## Overall Changes
    {summary}

    ## File-specific Changes
    """
        
        # Add insights for each file
        for insight in insights:
            prompt += f"\n### {insight['path']}\n{insight['insight']}\n"
        
        # Add instructions for commit format
        prompt += """
    ## Instructions
    1. Generate a commit message in the Conventional Commits format:
    <type>(<scope>): <description>

    [optional body]

    [optional footer]

    2. The type should be one of: feat, fix, docs, style, refactor, perf, test, build, ci, chore
    """
        
        # Add change type if provided
        if change_type:
            prompt += f"\n   Use '{change_type}' as the type."
        else:
            prompt += "\n   Choose the most appropriate type based on the changes."
        
        # Add more formatting instructions
        prompt += """
    3. The scope should reflect the primary component or area changed.
    4. The description should be concise and in imperative mood ("add", not "added").
    5. Add a body with more details about the changes if necessary.
    6. Keep the message professional and focused on the substance of the changes.
    """
        
        return prompt

    def _reconstruct_diff_text(self, git_diff):
        """Reconstruct the full diff text from a GitDiff object.
        
        Used as a fallback if file-based processing fails.
        
        Args:
            git_diff: Parsed GitDiff object
            
        Returns:
            Reconstructed diff text
        """
        diff_parts = []
        for file in git_diff.files:
            diff_parts.append(f"diff --git a/{file.path} b/{file.path}")
            if file.change_type == "added":
                diff_parts.append(f"new file mode 100644")
            elif file.change_type == "deleted":
                diff_parts.append(f"deleted file mode 100644")
            diff_parts.append(f"--- a/{file.path}")
            diff_parts.append(f"+++ b/{file.path}")
            diff_parts.append(file.diff_content)
        
        return "\n".join(diff_parts)

    def _generate_message(self, prompt: str) -> str:
        """Generate a commit message using the LLM.
        
        Args:
            prompt: Prompt string
            
        Returns:
            Generated commit message
            
        Raises:
            RuntimeError: If message generation fails
        """
        attempts = 0
        
        while attempts < self.max_retries:
            try:
                logger.debug("Generating commit message")
                message = self.ollama_client.generate(prompt, self.model_config)
                
                # Check if the message is empty
                if not message.strip():
                    raise ValueError("Model returned an empty response, please try again or use a different model")
                    
                return message.strip()
            except ConnectionError as e:
                raise RuntimeError(str(e))
            except Exception as e:
                attempts += 1
                logger.warning(
                    f"Error generating message (attempt {attempts}/{self.max_retries}): {e}"
                )
                
                if attempts < self.max_retries:
                    # Wait before retrying
                    time.sleep(self.retry_delay)
        
        # If we reach here, all retries failed
        logger.error(f"Failed to generate message after {self.max_retries} attempts.")
        raise RuntimeError("Failed to generate commit message.")

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