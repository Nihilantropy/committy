"""Tests for the Ollama integration module."""

import os
import pytest
import requests
from unittest.mock import patch, MagicMock

from committy.llm.ollama import OllamaClient, get_default_model_config

class TestOllamaClient:
    """Tests for the OllamaClient class."""

    def test_init_default_host(self):
        """Test client initialization with default host."""
        client = OllamaClient()
        assert client.host == "http://localhost:11434"
        assert client.api_base == "http://localhost:11434/api"

    def test_init_custom_host(self):
        """Test client initialization with custom host."""
        client = OllamaClient(host="http://192.168.1.100:11434")
        assert client.host == "http://192.168.1.100:11434"
        assert client.api_base == "http://192.168.1.100:11434/api"

    def test_init_from_env(self):
        """Test client initialization from environment variable."""
        with patch.dict(os.environ, {"OLLAMA_HOST": "http://custom:11434"}):
            client = OllamaClient()
            assert client.host == "http://custom:11434"

    def test_is_running_true(self):
        """Test is_running when Ollama is running."""
        mock_response = MagicMock()
        mock_response.status_code = 200

        with patch("requests.get", return_value=mock_response) as mock_get:
            client = OllamaClient()
            result = client.is_running()
            
            assert result is True
            mock_get.assert_called_once_with(
                "http://localhost:11434/api/tags", timeout=2
            )

    def test_is_running_false_connection_error(self):
        """Test is_running when connection fails."""
        with patch("requests.get", side_effect=requests.exceptions.ConnectionError()) as mock_get:
            client = OllamaClient()
            result = client.is_running()
            
            assert result is False
            mock_get.assert_called_once()

    def test_list_models_success(self):
        """Test list_models success case."""
        # Mock response for is_running check
        mock_running_response = MagicMock()
        mock_running_response.status_code = 200
        
        # Mock response for list_models
        mock_models_response = MagicMock()
        mock_models_response.status_code = 200
        mock_models_response.json.return_value = {
            "models": [
                {"name": "gemma3:12b", "size": "12.0GB"},
                {"name": "phi3:mini", "size": "3.8GB"}
            ]
        }
        
        with patch("requests.get", side_effect=[mock_running_response, mock_models_response]):
            client = OllamaClient()
            models = client.list_models()
            
            assert len(models) == 2
            assert models[0]["name"] == "gemma3:12b"
            assert models[1]["name"] == "phi3:mini"

    def test_list_models_service_not_running(self):
        """Test list_models when service is not running."""
        # Mock response for is_running check
        with patch.object(OllamaClient, "is_running", return_value=False):
            client = OllamaClient()
            models = client.list_models()
            
            assert models == []

    def test_has_model_true(self):
        """Test has_model when model exists."""
        client = OllamaClient()
        
        # Mock list_models to return models
        with patch.object(
            client, "list_models", 
            return_value=[
                {"name": "gemma3:12b", "size": "12.0GB"},
                {"name": "phi3:mini", "size": "3.8GB"}
            ]
        ):
            assert client.has_model("gemma3:12b") is True
            assert client.has_model("phi3:mini") is True

    def test_has_model_false(self):
        """Test has_model when model does not exist."""
        client = OllamaClient()
        
        # Mock list_models to return models
        with patch.object(
            client, "list_models", 
            return_value=[
                {"name": "gemma3:12b", "size": "12.0GB"},
                {"name": "phi3:mini", "size": "3.8GB"}
            ]
        ):
            assert client.has_model("nonexistent-model") is False

    def test_generate_success(self):
        """Test generate text successfully."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"response": "Generated text"}
        
        client = OllamaClient()
        
        # Mock dependencies
        with patch.object(client, "is_running", return_value=True), \
             patch.object(client, "has_model", return_value=True), \
             patch("requests.post", return_value=mock_response) as mock_post:
            
            model_config = {"model": "gemma3:12b", "parameters": {"temperature": 0.2}}
            result = client.generate("Test prompt", model_config)
            
            assert result == "Generated text"
            mock_post.assert_called_once()
            # Check that payload was constructed correctly
            args, kwargs = mock_post.call_args
            assert kwargs["json"]["model"] == "gemma3:12b"
            assert kwargs["json"]["prompt"] == "Test prompt"
            assert kwargs["json"]["temperature"] == 0.2

    def test_generate_ollama_not_running(self):
        """Test generate when Ollama is not running."""
        client = OllamaClient()
        
        # Mock is_running to return False
        with patch.object(client, "is_running", return_value=False):
            with pytest.raises(ConnectionError) as excinfo:
                client.generate("Test prompt", {"model": "gemma3:12b"})
            
            assert "Could not connect to Ollama" in str(excinfo.value)
            assert "See docs/OLLAMA_SETUP.md" in str(excinfo.value)

    def test_generate_model_not_available(self):
        """Test generate when model is not available."""
        client = OllamaClient()
        
        # Mock dependencies
        with patch.object(client, "is_running", return_value=True), \
             patch.object(client, "has_model", return_value=False):
            
            with pytest.raises(ValueError) as excinfo:
                client.generate("Test prompt", {"model": "nonexistent-model"})
            
            assert "Model nonexistent-model is not available" in str(excinfo.value)
            assert "See docs/OLLAMA_SETUP.md" in str(excinfo.value)


class TestConfigFunctions:
    """Tests for configuration functions."""

    def test_get_default_model_config(self):
        """Test default model configuration."""
        config = get_default_model_config()
        assert config["model"] == "gemma3:12b"
        assert config["parameters"]["temperature"] == 0.2
        assert config["parameters"]["max_tokens"] == 256

    def test_get_default_model_config_from_env(self):
        """Test getting model config from environment variables."""
        with patch.dict(os.environ, {
            "OLLAMA_MODEL": "phi3:mini",
            "AUTOCOMMIT_TEMP": "0.7",
            "AUTOCOMMIT_MAX_TOKENS": "512"
        }):
            config = get_default_model_config()
            assert config["model"] == "phi3:mini"
            assert config["parameters"]["temperature"] == 0.7
            assert config["parameters"]["max_tokens"] == 512