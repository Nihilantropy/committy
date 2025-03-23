"""Prompt templates for commit message generation.

This module provides templates and strategies for constructing effective
prompts for generating commit messages from git diffs.
"""

import logging
from typing import Dict, List, Optional, Any, Union

# Configure logger
logger = logging.getLogger(__name__)

# Base prompt template for conventional commits
CONVENTIONAL_COMMIT_TEMPLATE = """# Git Diff Analysis Task
You are analyzing a git diff to generate a commit message that follows the Conventional Commits specification. 

## Context
{context}

## Conventional Commits Format
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]

## Guidelines
1. Types: feat (new feature), fix (bug fix), docs (documentation), style (formatting), refactor (code restructuring), perf (performance), test (tests), build (build system), ci (CI/CD), chore (maintenance)
2. Scope: Component affected (e.g., auth, api, ui)
3. Description: Short summary in imperative mood ("add" not "added" or "adds")
4. Body: Detailed explanation of the changes, motivation, and context
5. Footer: Reference issues (e.g., "Fixes #123") or breaking changes

## Analysis:
Analyze the changes and determine:
- Primary change type (what kind of change is this?)
- Scope (which part of the codebase is affected?)
- Key changes to highlight in description
- Details to include in body
- Any references to issues or breaking changes

## Output:
Generate a conventional commit message with all required components.
"""

# Enhanced prompt template for conventional commits with added context
ENHANCED_COMMIT_TEMPLATE = """# Git Diff Analysis Task
You are an expert developer analyzing git diffs to generate clear, precise commit messages.
Your goal is to produce a high-quality commit message following the Conventional Commits specification.

## Git Diff Content
{context}

## Understanding this Git Diff
- First determine what kind of change this is (fix, feature, refactor, etc.)
- Identify which components or modules are affected (for the scope)
- Look for patterns in the changes (new functions, bug fixes, style changes)
- Note any test additions/modifications or documentation updates
- Identify breaking changes or sensitive modifications

## Conventional Commits Format
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]

## Guidelines for Quality Commit Messages
1. Types:
   - feat: A new feature
   - fix: A bug fix
   - docs: Documentation changes
   - style: Changes that don't affect code meaning (formatting, etc.)
   - refactor: Code changes that neither fix bugs nor add features
   - perf: Performance improvements
   - test: Adding or correcting tests
   - build: Changes to build system or dependencies
   - ci: Changes to CI configuration files
   - chore: Other changes that don't modify src or test files

2. Scope:
   - Use component name, module, or affected area
   - Use lowercase, hyphen-separated words if needed
   - Keep it brief but descriptive
   - Examples: api, auth, core, ui, navigation, database

3. Description:
   - Use imperative, present tense ("add", not "added" or "adds")
   - Don't capitalize first letter
   - No period at the end
   - Clear and concise, maximum 72 characters
   - Describe what the change does, not how it does it

4. Body:
   - Explain the motivation for the change
   - Compare with previous behavior
   - Use present tense
   - Include relevant background information
   - Format as paragraphs or bullet points

5. Footer:
   - Reference issues: "Fixes #123" or "Resolves #456"
   - Breaking changes: "BREAKING CHANGE: <description>"
   - Multiple footers allowed, one per line

## Your Commit Message Output:
Analyze the diff carefully and generate a complete, conventional commit message. Be concise but informative.
"""

# Template for refactoring commits
REFACTOR_COMMIT_TEMPLATE = """# Git Diff Analysis for Refactoring Changes
You are analyzing a git diff for a refactoring change. Refactoring means changing code structure without changing functionality.

## Git Diff Content
{context}

## Refactoring Patterns to Look For
- Method extraction or consolidation
- Class or module reorganization
- Variable or function renaming
- Code movement between files
- Simplification of complex expressions
- Interface changes
- Decomposition of large functions
- Removal of code duplication

## Conventional Commits Format for Refactoring
refactor[optional scope]: <description>

[explanation of changes and motivation]

[optional footer with issues or breaking changes]

## Guidelines for Refactoring Commits
1. Always use type "refactor"
2. Be specific about what was refactored in the description
3. Explain the motivation and benefits in the body
4. Note if the refactoring:
   - Improves readability
   - Enhances maintainability
   - Makes code more testable
   - Prepares for future changes
5. Mention if there are any performance implications (positive or negative)
6. Be explicit about breaking changes if any interfaces were modified

## Output:
Generate a high-quality commit message for this refactoring change.
"""

# Template for bug fix commits
BUGFIX_COMMIT_TEMPLATE = """# Git Diff Analysis for Bug Fix Changes
You are analyzing a git diff for a bug fix. Your task is to identify the nature of the bug and how it was fixed.

## Git Diff Content
{context}

## Bug Fix Patterns to Look For
- Condition corrections (if statements, loops)
- Null/undefined checks
- Boundary condition handling
- Exception/error handling additions
- Race condition fixes
- Type corrections
- Method call updates
- Data validation improvements

## Conventional Commits Format for Bug Fixes
fix[optional scope]: <description>

[explanation of the bug and fix]

[optional footer with "Fixes #issue" reference]

## Guidelines for Bug Fix Commits
1. Always use type "fix"
2. Describe what was fixed, not the symptoms
3. In the body, include:
   - What was causing the bug
   - How it was fixed
   - How to verify the fix works
4. Reference the issue number if available
5. Be specific about the affected component in the scope
6. Note any potential side effects of the fix

## Output:
Generate a high-quality commit message for this bug fix.
"""

# Template for feature addition commits
FEATURE_COMMIT_TEMPLATE = """# Git Diff Analysis for Feature Addition
You are analyzing a git diff for a new feature addition. Your task is to identify the nature of the feature and how it was implemented.

## Git Diff Content
{context}

## Feature Addition Patterns to Look For
- New functions, methods, or classes
- New API endpoints
- New UI components
- New configuration options
- New file types or formats supported
- New dependencies added
- New test coverage for new functionality
- Documentation for new features

## Conventional Commits Format for Features
feat[optional scope]: <description>

[explanation of the feature and its usage]

[optional footer with references or breaking changes]

## Guidelines for Feature Commits
1. Always use type "feat"
2. Describe what the feature enables, not how it works
3. In the body, include:
   - Purpose of the feature
   - How it can be used
   - Any configuration or setup required
   - Limitations or known issues
4. Use scope to indicate the affected component or module
5. Note breaking changes if the feature changes existing behavior
6. Reference related issues or requirements

## Output:
Generate a high-quality commit message for this feature addition.
"""

# Template for documentation changes
DOCUMENTATION_COMMIT_TEMPLATE = """# Git Diff Analysis for Documentation Changes
You are analyzing a git diff for documentation changes. Your task is to identify what documentation was added, updated, or removed.

## Git Diff Content
{context}

## Documentation Change Patterns to Look For
- README updates
- Code comments additions or improvements
- API documentation changes
- Example additions or updates
- Installation or setup instruction changes
- Usage guide modifications
- License or contributor guideline changes
- Diagrams or visual aid additions

## Conventional Commits Format for Documentation
docs[optional scope]: <description>

[explanation of the documentation changes]

[optional footer]

## Guidelines for Documentation Commits
1. Always use type "docs"
2. Describe what documentation was changed
3. In the body, include:
   - Reason for documentation changes
   - Summary of what was added, updated, or removed
   - Any related issues or feedback addressed
4. Use scope to indicate the component being documented
5. Be specific about the type of documentation (API docs, examples, etc.)

## Output:
Generate a high-quality commit message for these documentation changes.
"""

# Map of change types to specialized templates
SPECIALIZED_TEMPLATES = {
    "refactor": REFACTOR_COMMIT_TEMPLATE,
    "fix": BUGFIX_COMMIT_TEMPLATE,
    "feat": FEATURE_COMMIT_TEMPLATE,
    "docs": DOCUMENTATION_COMMIT_TEMPLATE,
}

def get_prompt_for_diff(context: str, change_type: Optional[str] = None) -> str:
    """Get appropriate prompt template for the given diff context and change type.
    
    Args:
        context: Extracted context from git diff
        change_type: Optional type of change if known (refactor, fix, feat, docs)
        
    Returns:
        Formatted prompt string
    """
    # If we have a known change type and a specialized template, use it
    if change_type and change_type in SPECIALIZED_TEMPLATES:
        template = SPECIALIZED_TEMPLATES[change_type]
        logger.debug(f"Using specialized template for change type: {change_type}")
    else:
        # Default to the enhanced template
        template = ENHANCED_COMMIT_TEMPLATE
        logger.debug("Using enhanced conventional commit template")
    
    # Format the template with the context
    return template.format(context=context)


def detect_likely_change_type(context: str) -> Optional[str]:
    """Attempt to detect the likely change type from the diff context.
    
    This is a heuristic approach to guess the change type (feat, fix, etc.)
    based on patterns in the diff content.
    
    Args:
        context: Extracted context from git diff
        
    Returns:
        Likely change type or None if uncertain
    """
    # Convert to lowercase for case-insensitive matching
    content_lower = context.lower()
    
    # Define patterns for each change type
    patterns = {
        "fix": [
            "fix", "bug", "issue", "problem", "error", "crash", "exception",
            "null", "undefined", "incorrect", "wrong", "invalid", "unexpected",
            "handle edge case", "prevent", "resolve"
        ],
        "feat": [
            "add new", "new feature", "implement", "add support for",
            "introduce", "enable", "allow", "create new", "new capability"
        ],
        "refactor": [
            "refactor", "simplify", "restructure", "reorganize", "rewrite",
            "clean", "improve", "optimize", "rename", "move code", "extract",
            "split", "consolidate", "deduplicate"
        ],
        "docs": [
            "document", "readme", "comment", "example", "usage", "guide",
            "instruction", "explain", "clarify", "documentation"
        ],
        "test": [
            "test", "spec", "unit test", "integration test", "e2e", "coverage",
            "assert", "mock", "stub", "fixture"
        ],
        "style": [
            "style", "format", "indent", "whitespace", "typo", "lint", 
            "prettier", "eslint", "formatting"
        ],
        "perf": [
            "performance", "optimize", "speed", "memory", "cpu", "runtime",
            "efficient", "faster", "reduce time", "benchmark"
        ],
        "build": [
            "build", "package", "dependency", "version", "update", "upgrade",
            "bump", "release", "webpack", "babel", "gradle", "maven"
        ],
        "ci": [
            "ci", "pipeline", "workflow", "jenkins", "github action", "travis",
            "circle", "continuous integration", "automation"
        ],
        "chore": [
            "chore", "maintenance", "cleanup", "housekeeping", "update",
            "tooling", "config", "configuration", "setup"
        ]
    }
    
    # Count matches for each type
    scores = {change_type: 0 for change_type in patterns}
    
    for change_type, keywords in patterns.items():
        for keyword in keywords:
            matches = content_lower.count(keyword)
            scores[change_type] += matches
    
    # Check file patterns
    if "test" in context.lower() and "/test" in context.lower():
        scores["test"] += 5
    
    if "readme" in context.lower() or ".md" in context.lower():
        scores["docs"] += 5
    
    # Find the type with the highest score
    max_score = max(scores.values())
    if max_score > 0:
        # Find all types with the max score
        top_types = [t for t, s in scores.items() if s == max_score]
        
        # If there's a clear winner, return it
        if len(top_types) == 1:
            return top_types[0]
    
    # If no clear pattern or tie, return None
    logger.debug("Could not determine likely change type from context")
    return None


def enhance_commit_message(message: str) -> str:
    """Enhance a generated commit message for better quality.
    
    This function applies post-processing to improve the quality of 
    generated commit messages, such as enforcing format conventions
    and fixing common issues.
    
    Args:
        message: Raw generated commit message
        
    Returns:
        Enhanced commit message
    """
    # Remove leading/trailing whitespace
    message = message.strip()
    
    # Split into components
    parts = message.split("\n\n", 2)
    
    # Process the header (first line)
    if parts:
        header = parts[0].strip()
        
        # Ensure header does not start with uppercase
        if len(header) > 0 and header[0].isalpha() and header[0].isupper():
            # Find the colon that separates type/scope from description
            colon_pos = header.find(":")
            if colon_pos > 0:
                # Only convert the description part to lowercase
                prefix = header[:colon_pos+1]
                desc = header[colon_pos+1:].strip()
                if desc and desc[0].isupper():
                    header = prefix + " " + desc[0].lower() + desc[1:]
        
        # Ensure no period at the end of the header
        if header.endswith("."):
            header = header[:-1]
        
        parts[0] = header
    
    # Reassemble the message
    enhanced_message = "\n\n".join(parts)
    
    return enhanced_message