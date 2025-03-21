# AutoCommit Application Architecture

This document outlines the architecture design for AutoCommit, including the command-line interface, application flow, component structure, and module interfaces.

## 1. Command-Line Interface Design

AutoCommit provides a seamless CLI experience that integrates with git workflows while offering configuration options and powerful features.

### 1.1 Primary Commands

```
autocommit [options]
```

Without arguments, the default behavior is to:
1. Extract git diff from staged changes
2. Analyze the diff using the LLM
3. Generate an appropriate commit message
4. Prompt the user for confirmation
5. Execute the commit if confirmed

### 1.2 Command Options

| Option | Description |
|--------|-------------|
| `--help`, `-h` | Display help information |
| `--version`, `-v` | Display version information |
| `--dry-run`, `-d` | Generate a commit message without committing |
| `--format=<format>`, `-f <format>` | Specify commit message format (conventional, angular, simple) |
| `--model=<model>`, `-m <model>` | Specify the LLM model to use |
| `--edit`, `-e` | Open the generated message in an editor before committing |
| `--config=<path>`, `-c <path>` | Specify config file location |
| `--init-config` | Generate default configuration file |
| `--verbose` | Increase output verbosity |
| `--no-confirm` | Skip confirmation step |
| `--with-scope` | Force inclusion of scope in commit message |
| `--max-tokens=<n>` | Limit the LLM output token count |

### 1.3 Secondary Commands

```
autocommit config [get|set|list] [key] [value]
```
Manage configuration without editing the config file directly.

```
autocommit model [list|download|update|info] [model_name]
```
Manage Ollama models used by AutoCommit.

### 1.4 Output Format

```
$ autocommit
Analyzing changes... ⏳
Found changes in 3 files:
  - src/main.py (modified)
  - tests/test_parser.py (added)
  - docs/README.md (modified)

Generated commit message:
feat(parser): add regex-based code block parser

Implement parser to extract code blocks using regular expressions.
Add unit tests and update documentation.

Confirm commit with this message? [Y/n/e(dit)]: 
```

## 2. Application Flow

The application follows a structured flow from git diff extraction to commit message generation:

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  Extract Git    │     │  Preprocess     │     │  Build LLM      │
│  Diff Data      │────▶│  Diff Data      │────▶│  Prompt         │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                                                         │
                                                         ▼
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  Execute Git    │     │  Format         │     │  Generate       │
│  Commit         │◀────│  Message        │◀────│  Message via    │
└─────────────────┘     └─────────────────┘     │  LLM            │
                                                └─────────────────┘
```

### 2.1 Detailed Flow Steps

1. **Parse Command Line Arguments**
   - Process options and commands
   - Load configuration settings
   - Validate input parameters

2. **Extract Git Diff**
   - Use GitPython to access repository
   - Extract staged changes
   - Identify file types and change types

3. **Preprocess Diff Data**
   - Filter non-essential changes (whitespace, comments)
   - Categorize changes by type (add, modify, delete)
   - Extract context from surrounding code
   - Identify potential semantic meaning

4. **Build LLM Prompt**
   - Construct prompt template based on diff analysis
   - Include instructions for commit format
   - Add context about repository and change patterns

5. **Generate Message via LLM**
   - Send prompt to Ollama
   - Process LLM response
   - Extract structured components (type, scope, description)

6. **Format Message**
   - Apply conventional commits format
   - Validate format compliance
   - Post-process for consistency

7. **User Interaction**
   - Display generated message
   - Prompt for confirmation/edit
   - Process user feedback

8. **Execute Git Commit**
   - Commit with generated message
   - Provide confirmation output

### 2.2 Error Handling Flow

The application incorporates comprehensive error handling:

1. **Git Repository Issues**
   - No git repository found
   - No staged changes
   - Repository access problems

2. **LLM-Related Issues**
   - Ollama not installed/running
   - Model not available
   - Timeout or processing errors

3. **User Input Issues**
   - Invalid command options
   - Configuration errors
   - File access problems

## 3. Architecture Diagram

```
┌───────────────────────────────────────────────────────────────────┐
│ AutoCommit Application                                             │
│                                                                    │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────────────┐    │
│  │   CLI       │    │   Core      │    │   Git Integration   │    │
│  │ Interface   │───▶│ Engine      │───▶│                     │    │
│  └─────────────┘    └─────────────┘    └─────────────────────┘    │
│        │                   │                      │                │
│        │                   │                      │                │
│        ▼                   ▼                      ▼                │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────────────┐    │
│  │ Config      │    │ LLM         │    │ Formatter           │    │
│  │ Manager     │    │ Integration │    │                     │    │
│  └─────────────┘    └─────────────┘    └─────────────────────┘    │
│                            │                                       │
│                            ▼                                       │
│                     ┌─────────────┐                                │
│                     │ Ollama      │                                │
│                     │ Integration │                                │
│                     └─────────────┘                                │
└───────────────────────────────────────────────────────────────────┘
```

### 3.1 Component Descriptions

1. **CLI Interface**
   - Handles user input/output
   - Parses command-line arguments
   - Manages user interaction flow
   - Displays results and prompts

2. **Config Manager**
   - Loads and validates configuration
   - Provides access to settings
   - Manages user preferences
   - Handles configuration persistence

3. **Core Engine**
   - Coordinates overall application flow
   - Manages component interactions
   - Handles error conditions
   - Controls processing pipeline

4. **Git Integration**
   - Interfaces with git repository
   - Extracts and parses git diffs
   - Analyzes code changes
   - Executes git commands

5. **LLM Integration**
   - Manages LLM interaction
   - Builds and optimizes prompts
   - Processes model responses
   - Handles model-specific configurations

6. **Ollama Integration**
   - Communicates with Ollama API
   - Manages model selection
   - Handles model loading/unloading
   - Optimizes performance settings

7. **Formatter**
   - Applies commit message format rules
   - Ensures consistency and compliance
   - Handles special formatting needs
   - Validates output quality

## 4. Module Interfaces

### 4.1 CLI Module Interface

```python
class CLI:
    """Command-line interface for AutoCommit."""
    
    def parse_args(self, args: list[str]) -> dict:
        """Parse command-line arguments."""
        
    def display_message(self, message: str, message_type: str) -> None:
        """Display a message to the user."""
        
    def prompt_confirmation(self, message: str) -> bool:
        """Prompt user for confirmation."""
        
    def edit_message(self, message: str) -> str:
        """Open editor for user to modify message."""
        
    def handle_command(self, command: str, options: dict) -> int:
        """Handle a specific command."""
```

### 4.2 Config Module Interface

```python
class Config:
    """Configuration manager for AutoCommit."""
    
    def load(self, config_path: Optional[str] = None) -> dict:
        """Load configuration from file."""
        
    def save(self, config: dict, config_path: Optional[str] = None) -> bool:
        """Save configuration to file."""
        
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value."""
        
    def set(self, key: str, value: Any) -> None:
        """Set configuration value."""
        
    def create_default_config(self, config_path: str) -> bool:
        """Create default configuration file."""
```

### 4.3 Git Integration Module Interface

```python
class GitIntegration:
    """Git integration for AutoCommit."""
    
    def get_repository(self, path: Optional[str] = None) -> GitRepo:
        """Get git repository object."""
        
    def get_staged_diff(self) -> str:
        """Get diff of staged changes."""
        
    def get_unstaged_diff(self) -> str:
        """Get diff of unstaged changes."""
        
    def get_changed_files(self) -> list[dict]:
        """Get list of changed files with metadata."""
        
    def commit(self, message: str) -> bool:
        """Create a commit with the specified message."""
        
    def is_git_repository(self, path: str) -> bool:
        """Check if path is a git repository."""
```

### 4.4 LLM Integration Module Interface

```python
class LLMIntegration:
    """LLM integration for AutoCommit."""
    
    def build_prompt(self, diff_data: dict, format_type: str) -> str:
        """Build prompt for LLM based on diff data."""
        
    def generate_message(self, prompt: str, model: str, 
                         max_tokens: int) -> str:
        """Generate commit message using LLM."""
        
    def parse_response(self, response: str) -> dict:
        """Parse LLM response into structured format."""
        
    def available_models(self) -> list[str]:
        """Get list of available models."""
        
    def validate_model(self, model: str) -> bool:
        """Check if model is valid and available."""
```

### 4.5 Formatter Module Interface

```python
class Formatter:
    """Commit message formatter for AutoCommit."""
    
    def format_message(self, message_parts: dict, format_type: str) -> str:
        """Format commit message according to specified format."""
        
    def validate_format(self, message: str, format_type: str) -> bool:
        """Validate if message follows the specified format."""
        
    def extract_parts(self, message: str) -> dict:
        """Extract parts from formatted message."""
        
    def get_type_description(self, type_: str) -> str:
        """Get description for commit type."""
```

### 4.6 Ollama Integration Module Interface

```python
class OllamaIntegration:
    """Ollama integration for AutoCommit."""
    
    def is_installed(self) -> bool:
        """Check if Ollama is installed."""
        
    def is_running(self) -> bool:
        """Check if Ollama service is running."""
        
    def list_models(self) -> list[dict]:
        """List available models in Ollama."""
        
    def download_model(self, model_name: str) -> bool:
        """Download a model to Ollama."""
        
    def generate(self, prompt: str, model: str, 
                 parameters: dict) -> str:
        """Generate text using Ollama API."""
```

### 4.7 Core Engine Module Interface

```python
class Engine:
    """Core engine for AutoCommit."""
    
    def process(self, options: dict) -> tuple[bool, str]:
        """Process git diff and generate commit message."""
        
    def preprocess_diff(self, diff: str) -> dict:
        """Preprocess git diff for LLM consumption."""
        
    def analyze_changes(self, files: list[dict]) -> dict:
        """Analyze changes to determine commit type and scope."""
        
    def execute_commit(self, message: str) -> bool:
        """Execute git commit with generated message."""
        
    def handle_error(self, error: Exception) -> str:
        """Handle error and return user-friendly message."""
```

## 5. Data Flow

### 5.1 Git Diff Structure

The git diff data is structured as follows:

```python
diff_data = {
    "files": [
        {
            "path": "src/main.py",
            "change_type": "modified",
            "additions": 15,
            "deletions": 5,
            "language": "python",
            "diff_content": "...",
            "extension": ".py"
        },
        # More files...
    ],
    "summary": {
        "total_files": 3,
        "total_additions": 25,
        "total_deletions": 7,
        "languages": ["python", "markdown"]
    }
}
```

### 5.2 LLM Prompt Structure

The LLM prompt is structured with specific sections:

```
# Git Diff Analysis
You are analyzing the following git diff to generate a commit message following Conventional Commits format.

## Changed Files
- src/main.py (modified): 15 additions, 5 deletions
- tests/test_parser.py (added): 20 additions, 0 deletions
- docs/README.md (modified): 10 additions, 2 deletions

## Diff Content
```diff
[DIFF CONTENT HERE]
```

## Instructions
Generate a commit message following the Conventional Commits format:
1. Type: feat, fix, docs, style, refactor, perf, test, build, ci, chore
2. Optional scope in parentheses
3. Description in imperative mood
4. Optional body with details
5. Optional footer for breaking changes or issue references

## Output Format
type(scope): description

body

footer
```

### 5.3 LLM Response Structure

The parsed LLM response is structured as:

```python
message_parts = {
    "type": "feat",
    "scope": "parser",
    "description": "add regex-based code block parser",
    "body": "Implement parser to extract code blocks using regular expressions.\nAdd unit tests and update documentation.",
    "footer": None
}
```

## 6. Implementation Considerations

### 6.1 Performance Optimization

1. **Diff Preprocessing**
   - Filter non-essential whitespace changes
   - Truncate large diffs to relevant portions
   - Summarize repetitive changes

2. **LLM Interaction**
   - Cache similar requests
   - Optimize prompt size
   - Use appropriate temperature settings
   - Implement request timeouts

3. **User Experience**
   - Show progress indicators for long operations
   - Provide immediate feedback
   - Cache results for quick retries

### 6.2 Security Considerations

1. **Code Privacy**
   - All analysis happens locally
   - No code leaves the user's machine
   - No telemetry or analytics

2. **Model Validation**
   - Verify model source and integrity
   - Use established Ollama model repositories
   - Document model source and version

3. **Configuration Security**
   - Store sensitive settings securely
   - Validate configuration file integrity
   - Use appropriate file permissions

### 6.3 Extensibility

1. **Plugin System**
   - Support custom formatters
   - Allow custom diff preprocessing
   - Enable organization-specific extensions

2. **Model Flexibility**
   - Support multiple LLM providers
   - Allow custom model configuration
   - Provide model switching at runtime

3. **Output Customization**
   - Support multiple output formats
   - Allow organization-specific templates
   - Enable custom validation rules

## 7. Dependencies

| Component | Primary Dependencies |
|-----------|---------------------|
| Git Integration | GitPython |
| LLM Integration | LlamaIndex |
| CLI | Click |
| Config | PyYAML |
| Ollama | Requests |
| Core Engine | Standard Library |
| Formatter | Standard Library |

## 8. Testing Strategy

1. **Unit Tests**
   - Test each module in isolation
   - Mock external dependencies
   - Validate interface contracts

2. **Integration Tests**
   - Test component interactions
   - Validate data flow
   - Test error handling

3. **End-to-End Tests**
   - Test complete workflows
   - Validate with real git repositories
   - Test with various change patterns

4. **Performance Tests**
   - Measure response times
   - Test with large diffs
   - Validate memory usage

## 9. Future Expansion

1. **IDE Integration**
   - VS Code extension
   - JetBrains plugin
   - Atom/Sublime integration

2. **CI/CD Integration**
   - GitHub Actions support
   - GitLab CI support
   - Jenkins plugin

3. **Enhanced Analytics**
   - Commit quality metrics
   - Pattern recognition
   - Suggestion improvements

4. **Team Collaboration**
   - Team-specific configuration
   - Organizational best practices
   - Shared prompt templates