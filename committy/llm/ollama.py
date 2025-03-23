"""Ollama integration for AutoCommit.

This module handles the interaction with the Ollama API for text generation.
It assumes Ollama is already installed and the required models are available.
"""

import logging
import os
import subprocess
from typing import Any, Dict, List, Optional, Union

import requests

# Configure logger
logger = logging.getLogger(__name__)


class OllamaClient:
    """Client for interacting with Ollama API."""

    def __init__(self, host: Optional[str] = None):
        """Initialize the Ollama client.
        
        Args:
            host: Ollama API host. Defaults to OLLAMA_HOST env var or localhost.
        """
        self.host = host or os.environ.get("OLLAMA_HOST", "http://localhost:11434")
        self.timeout = int(os.environ.get("AUTOCOMMIT_TIMEOUT", "10"))
        self.api_base = f"{self.host}/api"
        logger.debug(f"Initialized Ollama client with host: {self.host}")

    def is_running(self) -> bool:
        """Check if Ollama service is running.
        
        Returns:
            True if Ollama service is running, False otherwise.
        """
        try:
            response = requests.get(f"{self.api_base}/tags", timeout=2)
            return response.status_code == 200
        except requests.exceptions.RequestException:
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
            response = requests.get(f"{self.api_base}/tags", timeout=self.timeout)
            response.raise_for_status()
            models = response.json().get("models", [])
            logger.debug(f"Retrieved {len(models)} models from Ollama")
            return models
        except requests.exceptions.RequestException as e:
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
        """Generate text using the Ollama API.
        
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
            raise ConnectionError(
                "Could not connect to Ollama. Please ensure Ollama is installed and "
                "running. See docs/OLLAMA_SETUP.md for installation instructions."
            )
        
        model_name = model_config["model"]
        if not self.has_model(model_name):
            raise ValueError(
                f"Model {model_name} is not available in Ollama. Please download it first "
                f"with 'ollama pull {model_name}'. See docs/OLLAMA_SETUP.md for details."
            )
        
        url = f"{self.api_base}/generate"
        
        payload = {
            "model": model_name,
            "prompt": prompt,
        }
        
        # Add parameters if provided
        if "parameters" in model_config:
            payload.update(model_config["parameters"])
        
        try:
            logger.debug(f"Sending prompt to model {model_name}")
            response = requests.post(url, json=payload, timeout=self.timeout)
            response.raise_for_status()
            generated_text = response.json().get("response", "")
            logger.debug(f"Received response of length {len(generated_text)}")
            return generated_text
        except requests.exceptions.ConnectionError:
            raise ConnectionError(
                "Lost connection to Ollama. Please ensure the service is still running."
            )
        except requests.exceptions.Timeout:
            raise TimeoutError(f"Request to Ollama timed out after {self.timeout} seconds")
        except requests.exceptions.HTTPError as e:
            if response.status_code == 404:
                raise ValueError(f"Model {model_name} not found in Ollama")
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
            "temperature": float(os.environ.get("AUTOCOMMIT_TEMP", "0.2")),
            "top_p": 0.9,
            "top_k": 40,
            "repeat_penalty": 1.1,
            "max_tokens": int(os.environ.get("AUTOCOMMIT_MAX_TOKENS", "256")),
            "stop": ["```", "---"]
        }
    }
    
    return config