# Commit Message Convention

This document outlines the commit message format and best practices adopted by Committy for generating high-quality, consistent commit messages.

## 1. Conventional Commits Specification

Committy follows the [Conventional Commits](https://www.conventionalcommits.org/) specification, a lightweight convention built on top of commit messages. This specification provides a set of rules for creating an explicit commit history that makes automated tools more effective and helps with automated versioning and changelog generation.

### 1.1 Basic Structure

```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

### 1.2 Types

Types indicate the kind of change being made:

| Type | Description |
|------|-------------|
| `feat` | A new feature |
| `fix` | A bug fix |
| `docs` | Documentation changes |
| `style` | Code style changes (formatting, missing semi-colons, etc; no code change) |
| `refactor` | Code refactoring (neither fixes a bug nor adds a feature) |
| `perf` | Performance improvements |
| `test` | Adding or correcting tests |
| `build` | Build system or external dependency changes |
| `ci` | CI configuration changes |
| `chore` | Other changes that don't modify src or test files |

### 1.3 Scope

The scope provides additional contextual information:

- Should be a noun describing the section of the codebase
- Examples: `api`, `auth`, `core`, `ui`, `config`
- For changes affecting multiple scopes, use `*` or omit scope

### 1.4 Description

The description is a short, imperative summary of the changes:

- Use the imperative mood ("add" not "added" or "adds")
- Don't capitalize the first letter
- No period at the end
- Limited to 72 characters

### 1.5 Body

The body provides detailed, explanatory text:

- Use to explain the motivation for the change
- Can span multiple lines
- Separate from subject by a blank line
- Each line limited to 100 characters

### 1.6 Footer

The footer is used for metadata:

- Reference issues being closed: `Closes #123, #456`
- Indicate breaking changes: `BREAKING CHANGE: <description>`
- List co-authors: `Co-authored-by: name <email>`

### 1.7 Breaking Changes

Breaking changes should be indicated in two ways:

1. Using an exclamation mark after the type/scope: `feat(api)!: change authentication protocol`
2. Adding a `BREAKING CHANGE:` entry in the footer

## 2. Industry Standards and Best Practices

Beyond the Conventional Commits specification, Committy incorporates additional best practices from the industry:

### 2.1 Angular's Commit Convention

Angular's commit convention forms the basis for Conventional Commits and adds:

- More specific types like `docs`, `style`, `refactor`, `perf`, `test`, `build`, `ci` and `chore`
- Scope brackets to specify the context
- Subject line length limits of 72 characters

### 2.2 Google's Engineering Practices

Google recommends:

- First line as a summary of the change (up to 50 characters)
- Detailed explanation in the body
- Explaining the why, not the how

### 2.3 Linux Kernel Guidelines

The Linux kernel recommends:

- Separate subject from body with a blank line
- Limit the subject line to 50 characters
- Use the body to explain what and why vs. how

### 2.4 GitHub Pull Request Titles

GitHub PR titles often become merge commit messages, so similar rules apply:

- Concise, descriptive titles
- Reference issue numbers when applicable
- Use keywords that GitHub recognizes (like "Fixes #123")

## 3. Committy's Adopted Format

Based on the above research, Committy generates commit messages with the following format:

### 3.1 Basic Format

```
<type>(<scope>): <short description>

<body>

<footer>
```

### 3.2 Rules

1. **Type**: Must be one of: feat, fix, docs, style, refactor, perf, test, build, ci, or chore
2. **Scope**: Optional, should be noun describing section of codebase
3. **Description**:
   - Imperative mood
   - No capitalization of first letter
   - No period at the end
   - Maximum 72 characters
4. **Body**: 
   - Explains motivation for change
   - May include context for reviewers
   - Each line maximum 100 characters
5. **Footer**:
   - References related issues
   - Notes breaking changes
   - Credits co-authors if applicable

### 3.3 Examples

#### Feature Addition
```
feat(auth): add multi-factor authentication

Implement TOTP-based two-factor authentication for user login.
This adds an additional security layer for sensitive operations.

Closes #142
```

#### Bug Fix
```
fix(api): prevent race condition in concurrent requests

The previous implementation didn't properly handle simultaneous
requests with the same resource ID, leading to data corruption.

Fixes #253
```

#### Breaking Change
```
feat(database)!: migrate from MongoDB to PostgreSQL

BREAKING CHANGE: Database connection methods have completely changed.
Users will need to update their configuration files.

Closes #198, #201
```

#### Documentation Update
```
docs: update installation instructions for Ubuntu 2024

Add missing dependencies and clarify environment setup process.
```

#### Performance Improvement
```
perf(search): optimize index lookup algorithm

Reduces query time by 40% for large datasets by implementing
a more efficient B-tree traversal.
```

## 4. Implementation Guidelines for Committy

The AI-powered commit message generator should:

1. Analyze git diffs to understand:
   - Files modified
   - Types of changes (additions, deletions, modifications)
   - Functional impact of changes

2. Determine the appropriate type and scope based on:
   - File paths (for scope inference)
   - Code patterns that indicate specific change types
   - Special comments that might provide hints

3. Generate a concise but descriptive summary that:
   - Focuses on the "what" and "why", not the "how"
   - Uses consistent language and terminology
   - Avoids vague descriptions like "fix bug" or "update code"

4. Detect potential breaking changes by:
   - Looking for significant interface modifications
   - Identifying changes to public APIs
   - Recognizing major version updates in dependencies

5. Include relevant issue references by:
   - Parsing branch names for issue numbers
   - Scanning commit message templates or previous commits
   - Looking for issue number patterns in code comments

## 5. References

1. [Conventional Commits](https://www.conventionalcommits.org/)
2. [Angular Commit Message Guidelines](https://github.com/angular/angular/blob/master/CONTRIBUTING.md#commit)
3. [Google Engineering Practices](https://google.github.io/eng-practices/review/developer/cl-descriptions.html)
4. [Git Commit Best Practices](https://github.com/trein/dev-best-practices/wiki/Git-Commit-Best-Practices)
5. [Linux Kernel Commit Guidelines](https://www.kernel.org/doc/html/latest/process/submitting-patches.html)