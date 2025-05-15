# LLM Selection & Configuration

This document outlines the simplified approach for configuring Large Language Models (LLMs) in Committy for generating commit messages.

## 1. Model Selection Approach

Committy adopts a flexible approach to LLM selection, focusing on usability and adaptability:

1. **Default Model**: Gemma3:12b
2. **User Customization**: Any Ollama-compatible model can be used via configuration
3. **Environment Variable Control**: Primary configuration through `OLLAMA_MODEL` environment variable

This approach prioritizes:
- Simplicity in configuration
- Flexibility for different user needs and hardware capabilities
- Future-proofing as new models become available

## 2. Default Model: Gemma3:12b

### 2.1 Model Specifications

- **Model**: Gemma3:12b
- **Parameter Count**: 12 billion parameters
- **Context Window**: ~8K tokens (sufficient for most git diffs)
- **Hardware Requirements**: ~10GB RAM, 4-core CPU recommended
- **Use Case**: Good balance between quality and performance for code understanding

### 2.2 Recommended Alternative Models

| Model Size | Recommended Model | RAM Requirements | Use Case |
|------------|-------------------|------------------|----------|
| Small (~3-7B) | Phi-3 Mini or Gemma3:7b | 4-8GB | Resource-constrained environments |
| Medium (~10-15B) | Gemma3:12b or CodeLlama:13b | 8-16GB | Standard use (default) |
| Large (~27-70B) | Llama3:70b or Mistral:36b | 32GB+ | Quality-critical applications |

## 3. Configuration System

### 3.1 Environment Variables

The primary method for model configuration is through environment variables:

| Environment Variable | Description | Default Value |
|----------------------|-------------|---------------|
| `OLLAMA_MODEL` | Model identifier to use | gemma3:12b |
| `OLLAMA_HOST` | Ollama API host | http://localhost:11434 |
| `COMMITTY_TEMP` | Model temperature | 0.2 |
| `COMMITTY_MAX_TOKENS` | Maximum response length | 256 |
| `COMMITTY_TIMEOUT` | Request timeout in seconds | 10 |

### 3.2 Configuration File

Users can also set model preferences in the Committy configuration file:

```yaml
# ~/.config/committy/config.yml
llm:
  model: gemma3:12b
  temperature: 0.2
  max_tokens: 256
  timeout: 10
  parameters:
    top_p: 0.9
    top_k: 40
    repeat_penalty: 1.1
```

### 3.3 Command Line Options

For one-time usage, command-line options override defaults:

```
committy --model=codellama:13b --temperature=0.3
```

### 3.4 Configuration Precedence

1. Command-line options (highest priority)
2. Environment variables
3. User configuration file
4. System defaults (lowest priority)

## 4. Universal Parameter Template

Committy uses a universal parameter template compatible with all Ollama models:

```python
DEFAULT_PARAMETERS = {
    "temperature": float(os.environ.get("COMMITTY_TEMP", "0.2")),
    "top_p": 0.9,
    "top_k": 40,
    "repeat_penalty": 1.1,
    "max_tokens": int(os.environ.get("COMMITTY_MAX_TOKENS", "256")),
    "stop": ["```", "---"]
}
```

These parameters can be customized in the configuration file on a per-model basis.

## 5. Prompt Engineering

The prompt template has been designed to work effectively across different models:

```markdown
# Git Diff Analysis
You are analyzing the following git diff to generate a commit message following Conventional Commits format.

## Changed Files
{{files_summary}}

## Diff Content

{{diff_content}}


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

## 6. Implementation Guidelines

### 6.1 Model Configuration Code

```python
import os
from typing import Dict, Any, Optional

def get_model_config() -> Dict[str, Any]:
    """Get the LLM model configuration from environment variables or defaults."""
    model_name = os.environ.get("OLLAMA_MODEL", "gemma3:12b")
    
    # Universal parameter template
    config = {
        "model": model_name,
        "parameters": {
            "temperature": float(os.environ.get("COMMITTY_TEMP", "0.2")),
            "top_p": 0.9,
            "top_k": 40,
            "repeat_penalty": 1.1,
            "max_tokens": int(os.environ.get("COMMITTY_MAX_TOKENS", "256")),
            "stop": ["```", "---"]
        }
    }
    
    return config
```

### 6.2 Ollama Integration

```python
import requests
import os
from typing import Dict, Any, Optional

class OllamaClient:
    """Client for interacting with Ollama API."""
    
    def __init__(self, host: Optional[str] = None):
        """Initialize the Ollama client.
        
        Args:
            host: Ollama API host. Defaults to OLLAMA_HOST env var or localhost.
        """
        self.host = host or os.environ.get("OLLAMA_HOST", "http://localhost:11434")
        self.timeout = int(os.environ.get("COMMITTY_TIMEOUT", "10"))
    
    def generate(self, prompt: str, model_config: Dict[str, Any]) -> str:
        """Generate text using the Ollama API.
        
        Args:
            prompt: The prompt to send to the model
            model_config: Model configuration including model name and parameters
            
        Returns:
            Generated text from the model
            
        Raises:
            ConnectionError: If Ollama cannot be reached
            TimeoutError: If request times out
            ValueError: If model is not available
        """
        url = f"{self.host}/api/generate"
        
        payload = {
            "model": model_config["model"],
            "prompt": prompt,
            **model_config.get("parameters", {})
        }
        
        try:
            response = requests.post(url, json=payload, timeout=self.timeout)
            response.raise_for_status()
            return response.json().get("response", "")
        except requests.exceptions.ConnectionError:
            raise ConnectionError("Could not connect to Ollama. Is it running?")
        except requests.exceptions.Timeout:
            raise TimeoutError(f"Request to Ollama timed out after {self.timeout} seconds")
        except requests.exceptions.HTTPError as e:
            if response.status_code == 404:
                raise ValueError(f"Model {model_config['model']} not found in Ollama")
            raise e
```

## 7. Conclusion

This simplified approach to model selection provides a good balance between ease of use and flexibility. By defaulting to Gemma3:12b but allowing easy customization through environment variables, Committy accommodates a wide range of user needs and hardware capabilities.

As new models become available in Ollama, users can experiment with them simply by changing the `OLLAMA_MODEL` environment variable, without requiring changes to the Committy codebase.