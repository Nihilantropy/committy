# Committy!

![GitHub License](https://img.shields.io/github/license/claudio/committy)
![Python Version](https://img.shields.io/badge/python-3.10%2B-blue)

committy is an AI-powered git commit message generator that automatically creates professional, meaningful commit messages by analyzing your git diffs.

## Features

- 🚀 **Zero-cost operation**: Uses locally-hosted LLMs through Ollama
- 🔒 **Full privacy**: All analysis happens on your machine
- 🧠 **Intelligent analysis**: Understands code changes across files
- 🛠️ **Seamless git integration**: Designed to replace your standard `git commit -m ""` workflow
- 📋 **Best practices**: Generates commit messages following conventional commits specification 
- ⚙️ **Customizable**: Configure message format, LLM model, and more
- 🏎️ **Fast**: Optimized for speed (typically < 5 seconds)

## Installation

```bash
# Coming soon
pip install committy
```

## Quick Start

```bash
# Stage your changes
git add .

# Generate commit message and commit
committy
```

## How It Works

committy:
1. Analyzes the staged git diff
2. Extracts the essential changes
3. Processes the changes through a locally-hosted LLM via Ollama
4. Formats the output according to best practices
5. Commits the changes with the generated message

## Requirements

- Python 3.10+
- Git
- Ollama
- Minimum 8GB RAM recommended for LLM operation

## Configuration

committy can be customized through a configuration file:

```bash
# Generate default config
committy --init-config

# Edit config
nano ~/.config/committy/config.yml
```

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
