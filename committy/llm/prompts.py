"""Prompt templates for commit message generation."""

import logging
from typing import Optional, Dict

# Configure logger
logger = logging.getLogger(__name__)

# Simple template for small models
SMALL_MODEL_TEMPLATE = """# Commit Message Generator
Analyze this git diff and create a concise commit message.

## Git Diff
{diff}

## Instructions
- Write a commit message in format: <type>(<scope>): <description>
- Type must be one of: feat, fix, docs, style, refactor, perf, test, build, ci, chore
- Only describe the actual code changes in the diff
- Use imperative present tense: "add" not "added"
- Focus on facts visible in the code, not assumptions
- Keep it specific and concise
"""

# More detailed template for larger models
LARGE_MODEL_TEMPLATE = """# Commit Message Generator
Analyze this git diff and create a high-quality commit message following the Conventional Commits format.

## Git Diff
{diff}

## Instructions
1. Use the format: <type>(<scope>): <description>
   - Type: feat, fix, docs, style, refactor, perf, test, build, ci, chore
   - Scope: component or module being changed
   - Description: concise summary in imperative form

2. Include a body that explains:
   - What was changed and why
   - Technical details visible in the code
   - Impact of the changes

3. Guidelines:
   - Only describe actual changes visible in the diff
   - Use imperative, present tense ("add", not "added")
   - Be technically precise and specific
   - Mention file paths, function names, or components when relevant
   - Focus on facts, not assumptions
"""

# Specialized templates for different change types
SPECIALIZED_TEMPLATES = {
    "feat": """# Feature Addition Prompt
Analyze this diff for a new feature addition. Generate a commit message that clearly describes what the feature enables.

{context}

## Feature Addition Patterns
- New functions, methods, or classes
- New API endpoints
- New UI components
- New configuration options

## Output Format
feat(scope): description

[optional body with explanation of the feature]

[optional footer]
""",
    "fix": """# Bug Fix Prompt
Analyze this diff for a bug fix. Generate a commit message that explains what was fixed.

{context}

## Bug Fix Patterns
- Fixed conditional logic
- Added null checks
- Corrected parameter values
- Updated error handling

## Output Format
fix(scope): description

[optional body explaining the bug and fix]

[optional footer]
""",
    "refactor": """# Refactoring Prompt
Analyze this diff for code refactoring. Generate a commit message that explains the improvements made.

{context}

## Refactoring Patterns
- Renamed variables/functions for clarity
- Extracted methods
- Improved code structure
- Simplified logic

## Output Format
refactor(scope): description

[optional body explaining the improvements]

[optional footer]
""",
    "docs": """# Documentation Change Prompt
Analyze this diff for documentation changes. Generate a commit message that explains what was documented.

{context}

## Documentation Change Patterns
- Added or updated comments
- Modified README or docs files
- Updated examples
- Added usage instructions

## Output Format
docs(scope): description

[optional body explaining the documentation changes]

[optional footer]
"""
}

# Enhanced general template
ENHANCED_TEMPLATE = """# Git Diff Analysis
You are an expert developer analyzing this git diff to create a conventional commit message.

{context}

## Git Diff Content
As an experienced developer, analyze the above diff to identify the most significant changes.

## Instructions
Create a commit message following the Conventional Commits format:
1. Type: feat, fix, docs, style, refactor, perf, test, build, ci, chore
2. Optional scope in parentheses (module or component affected)
3. Description in imperative mood, lowercase, no trailing period
4. Optional body with more details on separate lines
5. Optional footer for breaking changes or issue references

## Output Format
type(scope): description

[optional body]

[optional footer]
"""

def generate_prompt(diff_text: str, model_name: Optional[str] = None) -> str:
    """Generate a simple, effective prompt for commit message generation.
    
    Args:
        diff_text: The git diff text
        model_name: Name of the model (to determine template)
        
    Returns:
        Formatted prompt string
    """
    # Determine if we should use the small model template
    use_small_template = False
    if model_name:
        small_model_indicators = [
            "mini", "small", "tiny", "3b", "5b", "7b", "phi3:mini", "gemma-2b"
        ]
        use_small_template = any(indicator in model_name.lower() for indicator in small_model_indicators)
    
    # Select template based on model size
    template = SMALL_MODEL_TEMPLATE if use_small_template else LARGE_MODEL_TEMPLATE
    logger.debug(f"Using {'small' if use_small_template else 'large'} model template")
    
    # Format the template with the diff
    return template.format(diff=diff_text)


def get_prompt_for_diff(context: str, change_type: Optional[str] = None) -> str:
    """Get a specialized prompt for a specific change type.
    
    Args:
        context: Diff context
        change_type: Optional change type
            
    Returns:
        Prompt string optimized for the change type
    """
    # Use specialized template if change type is provided and exists
    if change_type and change_type in SPECIALIZED_TEMPLATES:
        template = SPECIALIZED_TEMPLATES[change_type]
        logger.debug(f"Using specialized template for {change_type}")
        return template.format(context=context)
    
    # Fall back to enhanced template
    logger.debug("Using enhanced general template")
    return ENHANCED_TEMPLATE.format(context=context)


def enhance_commit_message(message: str) -> str:
    """Simple post-processing to improve the commit message.
    
    Args:
        message: Raw generated commit message
        
    Returns:
        Enhanced commit message
    """
    # Remove leading/trailing whitespace
    message = message.strip()
    
    # If message has multiple parts separated by blank lines
    parts = message.split("\n\n", 1)
    
    # Process the header (first line)
    if parts:
        header = parts[0].strip()
        
        # Ensure no period at the end of the header
        if header.endswith("."):
            header = header[:-1]
        
        # Fix square brackets instead of parentheses
        if "[" in header and "]" in header:
            import re
            header = re.sub(r"\[(.*?)\]", r"(\1)", header)
        
        # Ensure description starts with lowercase
        colon_parts = header.split(":", 1)
        if len(colon_parts) > 1 and colon_parts[1].strip():
            first_word = colon_parts[1].strip().split(" ", 1)[0]
            if first_word and first_word[0].isupper():
                colon_parts[1] = " " + first_word.lower() + colon_parts[1].strip()[len(first_word):]
                header = ":".join(colon_parts)
        
        parts[0] = header
    
    # Reassemble the message
    return "\n\n".join(parts)


def detect_likely_change_type(diff_text: str) -> Optional[str]:
    """Detect the likely change type based on the diff content.
    
    Args:
        diff_text: Git diff text or context containing the diff
        
    Returns:
        Detected change type or None if could not be determined
    """
    # Convert to lowercase for case-insensitive matching
    diff_lower = diff_text.lower()
    
    # Define patterns for different change types
    patterns = {
        "feat": ["new file", "feature", "add", "implement", "create"],
        "fix": ["fix", "bug", "issue", "error", "crash", "resolve", "problem"],
        "docs": ["documentation", "docs", "readme", "comment", "guide"],
        "style": ["style", "format", "whitespace", "indent", "lint"],
        "refactor": ["refactor", "restructure", "rewrite", "clean", "simplify", "improve code"],
        "perf": ["performance", "optimize", "speed", "efficient", "fast"],
        "test": ["test", "spec", "assert", "mock", "stub"],
        "build": ["build", "package", "dependency", "version", "upgrade"],
        "ci": ["ci", "pipeline", "workflow", "github action", "travis", "jenkins"],
        "chore": ["chore", "maintenance", "housekeeping", "metadata"]
    }
    
    # Count pattern matches for each type
    type_scores = {change_type: 0 for change_type in patterns}
    
    for change_type, keywords in patterns.items():
        for keyword in keywords:
            type_scores[change_type] += diff_lower.count(keyword)
    
    # Find type with highest score, if any have score > 0
    max_score = 0
    detected_type = None
    
    for change_type, score in type_scores.items():
        if score > max_score:
            max_score = score
            detected_type = change_type
    
    # Only return a type if we have a reasonable confidence
    return detected_type if max_score > 0 else None