# Prompt Engineering for Commit Messages

This document outlines the strategies and templates used for generating high-quality commit messages in Committy.

## 1. Prompt Engineering Goals

Our prompt engineering approach aims to achieve the following goals:

1. **Format Adherence**: Ensure commit messages follow the Conventional Commits specification
2. **Relevance**: Generate messages that accurately describe the actual changes
3. **Conciseness**: Produce clear, focused messages without unnecessary details
4. **Completeness**: Capture all relevant changes, including context and motivation
5. **Adaptability**: Adjust based on the type of change (feature, bugfix, refactor, etc.)

## 2. Core Prompt Structure

All our prompt templates follow this general structure:

1. **Task Definition**: Clearly define what the LLM should produce
2. **Context Presentation**: Present the git diff context in a structured way
3. **Format Specification**: Define the expected output format
4. **Guidelines**: Provide specific guidelines for generating high-quality messages
5. **Analysis Guidance**: Help the LLM identify patterns in the diff
6. **Output Request**: Explicitly request the output in the desired format

## 3. Specialized Templates

Committy uses specialized templates for different types of changes:

### 3.1 Feature Addition Template

Optimized for commits that add new functionality:
- Emphasizes identifying what the feature enables
- Guides the LLM to describe how the feature can be used
- Encourages noting any configuration or setup required
- Suggests mentioning limitations or known issues

### 3.2 Bug Fix Template

Designed for commits that fix issues:
- Focuses on identifying the nature of the bug
- Prompts for explaining the root cause
- Encourages describing how the fix works
- Suggests noting how to verify the fix

### 3.3 Refactoring Template

Tailored for code restructuring without functional changes:
- Guides the LLM to identify refactoring patterns
- Encourages explaining the motivation behind the changes
- Prompts for noting improvements in code quality
- Suggests mentioning any performance implications

### 3.4 Documentation Template

Specialized for documentation changes:
- Focuses on what documentation was modified
- Encourages describing the reason for changes
- Guides identification of what was added, updated, or removed
- Suggests noting which components are being documented

## 4. Change Type Detection

Committy attempts to automatically detect the type of change to select the appropriate template:

1. **Keyword Analysis**: Scan the diff context for keywords associated with each change type
2. **File Pattern Recognition**: Use file paths to identify test files, documentation, etc.
3. **Addition/Deletion Ratios**: Analyze the ratio of added to deleted lines for clues
4. **Special Patterns**: Look for specific patterns like new functions, fixed conditions, etc.

If the change type cannot be determined with confidence, the system defaults to the enhanced general template.

## 5. Prompt Optimization Techniques

Several techniques are used to optimize the prompts:

### 5.1 Context Prioritization

The git diff context is preprocessed to prioritize the most relevant information:
- Summary information first (total files, additions, deletions)
- Most significant changes based on relevance ranking
- Balance between breadth (all files) and depth (specific changes)

### 5.2 Token Management

Since LLMs have context window limitations:
- Diff content is summarized for large changes
- Less relevant changes may be omitted
- Headers and file information are preserved
- Summary is always included for context

### 5.3 Domain Knowledge Injection

The prompts contain domain-specific knowledge:
- Common refactoring patterns
- Bug fix patterns
- Feature implementation patterns
- Documentation conventions

## 6. Post-Processing

After generating the commit message, Committy applies post-processing for quality assurance:

1. **Format Verification**: Ensure adherence to Conventional Commits format
2. **Case Normalization**: Convert description to lowercase per convention
3. **Punctuation Fixing**: Remove trailing periods from first line
4. **Whitespace Normalization**: Fix spacing between sections
5. **Line Length Enforcement**: Ensure first line is under 72 characters

## 7. Prompt Evolution

The prompt templates are designed for continuous improvement:

1. **Performance Analysis**: Templates can be evaluated based on output quality
2. **Example-Based Enhancement**: Templates can be augmented with examples of good commits
3. **A/B Testing**: Different templates can be compared to determine the most effective approaches
4. **User Feedback Loop**: User edits to generated messages can inform template improvements

## 8. Example Prompts

### Basic Feature Addition Prompt

```
# Git Diff Analysis Task
You are analyzing a git diff for a new feature addition. Your task is to identify the nature of the feature and how it was implemented.

## Git Diff Content
[Context here]

## Feature Addition Patterns to Look For
- New functions, methods, or classes
- New API endpoints
- New UI components
- New configuration options
...

## Conventional Commits Format for Features
feat[optional scope]: <description>

[explanation of the feature and its usage]

[optional footer with references or breaking changes]

## Guidelines for Feature Commits
1. Always use type "feat"
2. Describe what the feature enables, not how it works
...

## Output:
Generate a high-quality commit message for this feature addition.
```

## 9. Implementation

The prompt templates are implemented in `committy/llm/prompts.py` and are used by the LLM interface to generate commit messages based on the git diff context provided by the LlamaIndex module.

The `get_prompt_for_diff` function selects the appropriate template based on the detected or specified change type, while `enhance_commit_message` performs post-processing on the generated message to ensure quality.