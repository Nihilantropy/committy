"""Ollama integration for Committy using LlamaIndex."""

import logging
import os
from typing import Any, Dict, List, Optional, Union

# Import LlamaIndex's Ollama integration
from llama_index.llms.ollama import Ollama

# Configure logger
logger = logging.getLogger(__name__)

class OllamaClient:
    """Client for interacting with Ollama API using LlamaIndex."""

    def __init__(self, host: Optional[str] = None):
        """Initialize the Ollama client.
        
        Args:
            host: Ollama API host. Defaults to OLLAMA_HOST env var or localhost.
        """
        self.host = host or os.environ.get("OLLAMA_HOST", "http://localhost:11434")
        self.timeout = int(os.environ.get("COMMITTY_TIMEOUT", "100"))
        logger.debug(f"Initialized Ollama client with host: {self.host}")
        
        # Initialize the LlamaIndex Ollama client
        self._client = None  # Lazy initialization
        self._current_model_name = None

    def _get_client(self, model_name: str):
        """Get or create the Ollama client for the specified model."""
        if self._client is None or self._current_model_name != model_name:
            self._client = Ollama(
                model=model_name,
                base_url=self.host,
                request_timeout=self.timeout,
            )
            self._current_model_name = model_name
        return self._client

    def is_running(self) -> bool:
        """Check if Ollama service is running.
        
        Returns:
            True if Ollama service is running, False otherwise.
        """
        try:
            # Keep original timeout for test compatibility
            import requests
            response = requests.get(f"{self.host}/api/tags", timeout=2)
            return response.status_code == 200
        except Exception:
            logger.debug("Ollama service is not running")
            return False

    def list_models(self) -> List[Dict[str, Any]]:
        """List available models in Ollama.
        
        Returns:
            List of model information dictionaries.
        """
        if not self.is_running():
            logger.error("Ollama service is not running. Please start it first.")
            return []
        
        try:
            import requests
            response = requests.get(f"{self.host}/api/tags", timeout=self.timeout)
            response.raise_for_status()
            models = response.json().get("models", [])
            logger.debug(f"Retrieved {len(models)} models from Ollama")
            return models
        except Exception as e:
            logger.error(f"Error listing models: {e}")
            return []

    def has_model(self, model_name: str) -> bool:
        """Check if a model is available in Ollama.
        
        Args:
            model_name: Name of the model to check.
            
        Returns:
            True if model is available, False otherwise.
        """
        models = self.list_models()
        return any(model.get("name") == model_name for model in models)

    def generate(self, prompt: str, model_config: Dict[str, Any]) -> str:
        """Generate text using the Ollama API via LlamaIndex.
        
        Args:
            prompt: The prompt to send to the model
            model_config: Model configuration including model name and parameters
            
        Returns:
            Generated text from the model
            
        Raises:
            ConnectionError: If Ollama cannot be reached
            ValueError: If model is not available
        """
        if not self.is_running():
            message = (
                "Could not connect to Ollama. Please ensure Ollama is installed and "
                "running. See docs/OLLAMA_SETUP.md for installation instructions."
            )
            logger.error(message)
            raise ConnectionError(message)
        
        model_name = model_config["model"]
        if not self.has_model(model_name):
            raise ValueError(
                f"Model {model_name} is not available in Ollama. Please download it first "
                f"with 'ollama pull {model_name}'. See docs/OLLAMA_SETUP.md for details."
            )
        
        try:
            logger.debug(f"Sending prompt to model {model_name}")
            
            # Get parameters
            params = {}
            if "parameters" in model_config:
                params = model_config["parameters"]
            
            # Get Ollama client for this model
            client = self._get_client(model_name)
            
            # Configure client with parameters
            temperature = params.get("temperature", 0.2)
            top_p = params.get("top_p", 0.9)
            top_k = params.get("top_k", 40)
            max_tokens = params.get("max_tokens", 256)
            
            logger.debug(f"Prompt to llm {prompt}")

            # Send request using LlamaIndex's Ollama integration
            response = client.complete(
                prompt, 
                temperature=temperature,
                top_p=top_p,
                top_k=top_k,
                max_tokens=max_tokens,
            )
            
            generated_text = str(response)
            logger.debug(f"Received response {generated_text}")
            logger.debug(f"Received response of length {len(generated_text)}")
            return generated_text
        except Exception as e:
            if "connection" in str(e).lower():
                raise ConnectionError(
                    "Lost connection to Ollama. Please ensure the service is still running."
                )
            elif "timeout" in str(e).lower():
                raise TimeoutError(f"Request to Ollama timed out after {self.timeout} seconds")
            else:
                raise e


def get_default_model_config() -> Dict[str, Any]:
    """Get the default LLM model configuration from environment variables.
    
    Returns:
        A dictionary with model configuration.
    """
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