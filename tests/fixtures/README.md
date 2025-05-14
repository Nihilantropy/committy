# Test Fixtures

This directory contains test fixtures used by Committy's test suite. The fixtures are designed to represent various types of common git changes and their expected commit messages.

## Directory Contents

- `feature_addition.diff`: A git diff representing a new feature addition, specifically a new user dashboard component
- `feature_addition.expected.txt`: The expected commit message for the feature addition diff
- `bug_fix.diff`: A git diff representing a bug fix, focusing on improving input validation
- `bug_fix.expected.txt`: The expected commit message for the bug fix diff
- `test_suite.json`: A combined test suite definition for automated testing

## Using the Fixtures

These fixtures are used by various tests in the Committy project:

1. **Unit tests**: Testing individual components like the diff parser or message formatter
2. **Integration tests**: Testing interactions between Git diff parsing and LLM prompting
3. **End-to-end tests**: Testing the complete workflow

## Adding New Fixtures

To add a new test fixture:

1. Create a `.diff` file with the git diff content (you can use `git diff --staged > new_fixture.diff`)
2. Create a corresponding `.expected.txt` file with the expected commit message
3. Update `test_suite.json` to include the new fixture
4. Add appropriate tests that use the new fixture

## Fixture Types

Currently, the following fixture types are available:

- **Feature Addition**: Adding new functionality
- **Bug Fix**: Fixing issues or bugs

Additional fixture types that could be added:

- **Documentation Change**: Changes to documentation files
- **Refactoring**: Code changes that don't add features or fix bugs
- **Style Change**: Changes to formatting, whitespace, etc.
- **Test Addition**: Adding or modifying tests
- **Performance Improvement**: Changes to improve performance
- **Build System**: Changes to build configuration
- **Dependency Updates**: Updating dependencies

## Notes on Test Fixtures

- All fixtures should be real-world examples or realistic synthetic examples
- Each fixture should focus on a single type of change
- Fixtures should include enough context for accurate commit message generation
- Expected messages should follow the conventional commits format