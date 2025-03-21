# Ollama Setup Guide

This document provides instructions for installing, configuring, and testing Ollama for use with AutoCommit.

## Prerequisites

AutoCommit requires Ollama to be installed and running with the necessary models already downloaded. This setup must be completed **before** running AutoCommit.

## 1. Installing Ollama

Ollama is a tool for running LLMs locally. Follow these steps to install Ollama on your system.

### 1.1 Ubuntu/Linux Installation

```bash
# Download and install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Verify installation
ollama --version
```

### 1.2 Manual Installation

If the script doesn't work, you can manually install Ollama:

1. Download the latest release for your platform from [Ollama's GitHub releases](https://github.com/ollama/ollama/releases)
2. Extract the archive and move the `ollama` binary to a location in your PATH (e.g., `/usr/local/bin/`)
3. Make the binary executable with `chmod +x /usr/local/bin/ollama`

## 2. Starting the Ollama Service

Ollama needs to run as a service to respond to API requests. You must start this service before running AutoCommit:

```bash
# Start Ollama service
ollama serve
```

This will start Ollama in the foreground. To run it in the background, use:

```bash
# Start Ollama service in the background
nohup ollama serve > ollama.log 2>&1 &
```

## 3. Installing Models

AutoCommit uses the Gemma3:12b model by default, but this can be changed via environment variables. You must download your chosen model before running AutoCommit:

### 3.1 Default Model Installation

```bash
# Install the default model
ollama pull gemma3:12b
```

### 3.2 Alternative Models

For systems with limited resources, you can use a smaller model:

```bash
# Install a smaller model
ollama pull phi3:mini
```

For higher quality results (requiring more resources):

```bash
# Install a larger model
ollama pull llama3:70b
```

## 4. Configuring AutoCommit

AutoCommit uses environment variables to configure Ollama integration:

| Variable | Description | Default Value |
|----------|-------------|---------------|
| `OLLAMA_MODEL` | Model to use | `gemma3:12b` |
| `OLLAMA_HOST` | Ollama API host | `http://localhost:11434` |
| `AUTOCOMMIT_TEMP` | Generation temperature | `0.2` |
| `AUTOCOMMIT_MAX_TOKENS` | Max tokens to generate | `256` |
| `AUTOCOMMIT_TIMEOUT` | Request timeout (seconds) | `10` |

Example usage:

```bash
# Use a different model
export OLLAMA_MODEL=phi3:mini

# Change temperature (higher = more creative)
export AUTOCOMMIT_TEMP=0.4
```

## 5. Verification Script

After installation, you can verify that everything is working correctly by running the tests:

```bash
# Run the tests for the Ollama integration
pytest tests/llm/test_ollama.py -v
```

## 6. Troubleshooting

### 6.1 Connection Errors

If AutoCommit reports that it can't connect to Ollama:
- Ensure the Ollama service is running with `ps aux | grep ollama`
- Check if Ollama is listening on the expected port with `netstat -tuln | grep 11434`
- Try restarting the Ollama service with `ollama serve`

### 6.2 Model Not Found

If you get a "Model not found" error:
- Verify the model is downloaded with `ollama list`
- Check that the model name in your environment matches exactly (e.g., `gemma3:12b` not `gemma3`)
- Try pulling the model again with `ollama pull <model-name>`

### 6.3 Out of Memory Errors

If you experience out-of-memory errors:
- Try using a smaller model (e.g., phi3:mini) by setting `OLLAMA_MODEL=phi3:mini`
- Close other memory-intensive applications
- Increase swap space on your system

## 7. Advanced Configuration

### 7.1 Custom Modelfile

You can create custom modelfiles for specialized commit message generation:

```
FROM gemma3:12b

# Set system message to optimize for commit messages
SYSTEM You are a commit message generator that follows the Conventional Commits format.
```

Save this to a file named `Modelfile` and run:

```bash
ollama create commit-generator -f Modelfile
```

Then use it with AutoCommit:

```bash
export OLLAMA_MODEL=commit-generator
```

### 7.2 Performance Optimization

For better performance:

```bash
# Enable GPU acceleration (if available)
export OLLAMA_GPU=true

# Set number of threads
export OLLAMA_THREADS=4
```

## 8. Resources

- [Ollama Documentation](https://github.com/ollama/ollama/tree/main/docs)
- [Ollama Model Library](https://ollama.com/library)
- [Ollama API Reference](https://github.com/ollama/ollama/blob/main/docs/api.md)