"""Tests for the configuration utilities."""

import os
import tempfile
import yaml
import pytest
from pathlib import Path

from committy.utils.config import (
    load_config,
    save_config,
    create_default_config,
    get_default_config_path,
    DEFAULT_CONFIG
)


class TestConfigUtils:
    """Tests for configuration utilities."""
    
    def test_get_default_config_path(self):
        """Test getting the default config path."""
        # Test with XDG_CONFIG_HOME
        with pytest.MonkeyPatch().context() as mp:
            mp.setenv("XDG_CONFIG_HOME", "/tmp/xdg_config")
            path = get_default_config_path()
            assert path == "/tmp/xdg_config/committy/config.yml"
        
        # Test default fallback
        path = get_default_config_path()
        assert str(Path.home() / ".config" / "committy" / "config.yml") == path
    
    def test_load_config_default(self):
        """Test loading default configuration."""
        # Test with non-existent config file
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = os.path.join(tmpdir, "nonexistent.yml")
            config = load_config(config_path)
            
            # Should return default config
            assert config == DEFAULT_CONFIG
    
    def test_load_config_from_file(self):
        """Test loading configuration from file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = os.path.join(tmpdir, "config.yml")
            
            # Create a test config file
            test_config = {
                "model": "test-model",
                "format": "test-format",
                "max_tokens": 123
            }
            
            with open(config_path, "w") as f:
                yaml.dump(test_config, f)
            
            # Load the config
            config = load_config(config_path)
            
            # Check that values from file are loaded
            assert config["model"] == "test-model"
            assert config["format"] == "test-format"
            assert config["max_tokens"] == 123
            
            # Check that default values for missing keys are preserved
            assert "temperature" in config
            assert config["temperature"] == DEFAULT_CONFIG["temperature"]
    
    def test_load_config_from_env(self):
        """Test loading configuration from environment variables."""
        with pytest.MonkeyPatch().context() as mp:
            # Set environment variables
            mp.setenv("COMMITTY_MODEL", "env-model")
            mp.setenv("COMMITTY_TEMP", "0.7")
            mp.setenv("COMMITTY_NO_CONFIRM", "true")
            
            # Load config with a non-existent path to force defaults
            with tempfile.TemporaryDirectory() as tmpdir:
                config_path = os.path.join(tmpdir, "nonexistent.yml")
                config = load_config(config_path)
                
                # Check that environment variables override defaults
                assert config["model"] == "env-model"
                assert config["temperature"] == 0.7
                assert config["no_confirm"] is True
    
    def test_save_config(self):
        """Test saving configuration to file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = os.path.join(tmpdir, "config.yml")
            
            # Create a test config
            test_config = {
                "model": "test-model",
                "format": "test-format",
                "max_tokens": 123
            }
            
            # Save the config
            result = save_config(test_config, config_path)
            assert result is True
            
            # Verify the file exists
            assert os.path.exists(config_path)
            
            # Load the config and verify contents
            with open(config_path, "r") as f:
                loaded_config = yaml.safe_load(f)
                
            assert loaded_config["model"] == "test-model"
            assert loaded_config["format"] == "test-format"
            assert loaded_config["max_tokens"] == 123
    
    def test_save_config_invalid_path(self):
        """Test saving configuration to an invalid path."""
        # Try to save to a path where parent directory doesn't exist and cannot be created
        with pytest.MonkeyPatch().context() as mp:
            # Mock os.makedirs to fail
            def mock_makedirs(*args, **kwargs):
                raise PermissionError("Permission denied")
            
            mp.setattr(os, "makedirs", mock_makedirs)
            
            # Try to save config
            result = save_config(DEFAULT_CONFIG, "/nonexistent/dir/config.yml")
            assert result is False
    
    def test_create_default_config(self):
        """Test creating default configuration file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = os.path.join(tmpdir, "config.yml")
            
            # Create default config
            result = create_default_config(config_path)
            assert result is True
            
            # Verify the file exists
            assert os.path.exists(config_path)
            
            # Verify the content is correct
            with open(config_path, "r") as f:
                content = f.read()
                
            # Check that it contains comments and default values
            assert "# Committy Configuration" in content
            assert "model:" in content
            assert "format:" in content
            
            # Load the config and verify defaults
            with open(config_path, "r") as f:
                # Skip comments at the beginning
                while True:
                    line = f.readline()
                    if not line.startswith("#") and line.strip():
                        f.seek(0)
                        break
                
                loaded_config = yaml.safe_load(f)
            
            assert loaded_config["model"] == DEFAULT_CONFIG["model"]
            assert loaded_config["format"] == DEFAULT_CONFIG["format"]
    
    def test_create_default_config_file_exists(self):
        """Test creating default config when file already exists."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = os.path.join(tmpdir, "config.yml")
            
            # Create an existing file
            with open(config_path, "w") as f:
                f.write("existing: file")
            
            # Try to create default config
            result = create_default_config(config_path)
            assert result is False
            
            # Verify the original file is unchanged
            with open(config_path, "r") as f:
                content = f.read()
                
            assert content == "existing: file"