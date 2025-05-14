# Committy!

![GitHub License](https://img.shields.io/github/license/claudio/committy)
![Python Version](https://img.shields.io/badge/python-3.10%2B-blue)

Committy is an AI-powered git commit message generator that automatically creates professional, meaningful commit messages by analyzing your git diffs.

## Features

- 🚀 **Zero-cost operation**: Uses locally-hosted LLMs through Ollama
- 🔒 **Full privacy**: All analysis happens on your machine
- 🧠 **Intelligent analysis**: Understands code changes across files
- 🛠️ **Seamless git integration**: Designed to replace your standard `git commit -m ""` workflow
- 📋 **Best practices**: Generates commit messages following conventional commits specification 
- ⚙️ **Customizable**: Configure message format, LLM model, and more
- 🏎️ **Fast**: Optimized for speed (typically < 5 seconds)
- 🎨 **Rich interface**: Color-coded output with progress indicators

## Installation

### Quick Install

```bash
# Clone the repository
git clone https://github.com/claudio/committy.git
cd committy

# Run the installation script
./scripts/install-dev.sh
```

### Manual Installation

```bash
# Clone the repository
git clone https://github.com/claudio/committy.git
cd committy

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -e .
pip install -r requirements-dev.txt

# Create symlink for easy access
ln -s "$(pwd)/scripts/committy" ~/.local/bin/committy
```

## Activate venv

```bash
. venv/bin/activate
```

## Quick Start

```bash
# Stage your changes
git add .

# Generate commit message and commit
committy

# Or preview without committing
committy --dry-run

# Get detailed analysis of your changes
committy --analyze
```

## Command-Line Options

| Option | Description |
|--------|-------------|
| `--version`, `-v` | Display version information |
| `--dry-run`, `-d` | Generate a message without committing |
| `--format=<format>`, `-f` | Specify commit format (conventional, angular, simple) |
| `--model=<model>`, `-m` | Specify LLM model to use |
| `--edit`, `-e` | Edit message before committing |
| `--config=<path>`, `-c` | Use a specific config file |
| `--init-config` | Generate default configuration |
| `--verbose` | Increase output verbosity (can be used multiple times) |
| `--no-confirm` | Skip confirmation step |
| `--with-scope` | Force inclusion of scope |
| `--max-tokens=<n>` | Limit LLM token count |
| `--analyze` | Show analysis without committing |
| `--no-color` | Disable colored output |

## How It Works

Committy:
1. Analyzes the staged git diff
2. Extracts the essential changes
3. Processes the changes through a locally-hosted LLM via Ollama
4. Formats the output according to best practices
5. Confirms with you before committing

## Configuration

Committy can be customized through a configuration file:

```bash
# Generate default config
committy --init-config

# Edit config
nano ~/.config/committy/config.yml
```

You can also use environment variables:

```bash
# Change the model
export COMMITTY_MODEL=phi3:mini

# Change temperature (creativity)
export COMMITTY_TEMP=0.3
```

## Requirements

- Python 3.10+
- Git
- Ollama
- Minimum 8GB RAM recommended for LLM operation

## Development

### Setting Up Development Environment

```bash
# Clone the repository
git clone https://github.com/claudio/committy.git
cd committy

# Set up virtual environment
python -m venv venv
source venv/bin/activate

# Install development dependencies
pip install -e ".[dev]"
```

### Running Tests

```bash
pytest
```

## Project Roadmap

See the [RoadMap.md](RoadMap.md) file for the detailed development plan.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.