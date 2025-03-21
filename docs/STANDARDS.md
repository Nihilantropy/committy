# AutoCommit Documentation Standards

This document outlines the documentation standards for the AutoCommit project to ensure consistency and clarity across all documentation.

## Code Documentation

### Docstrings

- All modules, classes, and functions must have docstrings
- Use Google-style docstrings
- Include type hints in function signatures

Example:

```python
def generate_commit_message(diff: str, format_type: str = "conventional") -> str:
    """Generate a commit message based on git diff.
    
    Args:
        diff: The git diff to analyze
        format_type: The commit message format type (default: conventional)
        
    Returns:
        A formatted commit message
        
    Raises:
        ValueError: If the diff is empty or format_type is unsupported
    """
    # Function implementation
```

### Comments

- Use comments to explain "why" rather than "what"
- Keep comments concise and up-to-date
- Comment complex or non-obvious sections of code

## Version Control

### Commit Messages

Ironically, we should follow best practices for our own commit messages while building an automated commit message generator:

- Follow the Conventional Commits specification (https://www.conventionalcommits.org/)
- Structure: `<type>[optional scope]: <description>`
- Types: feat, fix, docs, style, refactor, test, chore
- Keep the first line under 72 characters
- Use the imperative mood ("Add feature" not "Added feature")

Example:
```
feat(cli): add support for custom commit templates
```

### Pull Requests

- Reference issue numbers in PR description
- Include a summary of changes
- Ensure all tests pass before submitting

## Documentation Files

### README.md

- Keep up-to-date with the latest features and usage
- Include: overview, installation, quick start, examples
- Use badges for build status, version, license

### API Documentation

- Document all public APIs
- Include examples for common use cases
- Document breaking changes between versions

### Markdown Standards

- Use ATX-style headers (`#` for h1, `##` for h2)
- Line width: 80 characters maximum
- Use fenced code blocks with language specification
- Use reference-style links for repeated URLs

## Documentation Testing

- Verify code examples work as documented
- Run documentation through a spell checker
- Validate all links periodically

## Release Notes

- Document all significant changes
- Categorize as: Added, Changed, Deprecated, Removed, Fixed, Security
- Reference relevant issue/PR numbers

## Changelog

Maintain a CHANGELOG.md file following the [Keep a Changelog](https://keepachangelog.com/) format:

```markdown
# Changelog
All notable changes to this project will be documented in this file.

## [Unreleased]
### Added
- New feature X

### Fixed
- Bug in component Y

## [0.1.0] - 2025-03-21
### Added
- Initial release
- Core functionality
```