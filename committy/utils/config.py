"""Configuration utilities for Committy."""

import logging
import os
import yaml
from pathlib import Path
from typing import Any, Dict, Optional

# Configure logger
logger = logging.getLogger(__name__)

# Default configuration values
DEFAULT_CONFIG = {
    "model": "gemma3:12b",
    "format": "conventional",
    "max_tokens": 256,
    "temperature": 0.2,
    "no_confirm": False,
    "with_scope": True,
    "editor": None,  # Uses system default
    "prompt_template": "enhanced",
}


def get_default_config_path() -> str:
    """Get the default configuration file path.
    
    Returns:
        Path to default configuration file
    """
    # Check for XDG config home
    if "XDG_CONFIG_HOME" in os.environ:
        config_dir = Path(os.environ["XDG_CONFIG_HOME"]) / "committy"
    else:
        # Fall back to ~/.config
        config_dir = Path.home() / ".config" / "committy"
    
    # Create directory if it doesn't exist
    os.makedirs(config_dir, exist_ok=True)
    
    return str(config_dir / "config.yml")


def load_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """Load configuration from file.
    
    Args:
        config_path: Path to configuration file
            If None, tries to load from default location
    
    Returns:
        Configuration dictionary
    """
    # Start with default configuration
    config = DEFAULT_CONFIG.copy()
    
    # Determine config path
    if config_path is None:
        config_path = get_default_config_path()
    
    # Try to load configuration file
    try:
        if os.path.exists(config_path):
            with open(config_path, "r") as f:
                file_config = yaml.safe_load(f)
                if file_config and isinstance(file_config, dict):
                    # Update config with values from file
                    config.update(file_config)
                    logger.info(f"Loaded configuration from {config_path}")
    except Exception as e:
        logger.warning(f"Error loading configuration from {config_path}: {e}")
        logger.info("Using default configuration")
    
    # Override with environment variables
    env_config = _load_from_env()
    if env_config:
        config.update(env_config)
        logger.info("Applied configuration from environment variables")
    
    return config


def save_config(config: Dict[str, Any], config_path: Optional[str] = None) -> bool:
    """Save configuration to file.
    
    Args:
        config: Configuration dictionary
        config_path: Path to configuration file
            If None, uses default location
    
    Returns:
        True if configuration was saved successfully, False otherwise
    """
    # Determine config path
    if config_path is None:
        config_path = get_default_config_path()
    
    # Ensure directory exists
    try:
        os.makedirs(os.path.dirname(config_path), exist_ok=True)
    except (PermissionError, OSError) as e:
        logger.error(f"Error creating directory for {config_path}: {e}")
        return False
    
    # Save configuration
    try:
        with open(config_path, "w") as f:
            yaml.dump(config, f, default_flow_style=False)
        logger.info(f"Saved configuration to {config_path}")
        return True
    except Exception as e:
        logger.error(f"Error saving configuration to {config_path}: {e}")
        return False


def create_default_config(config_path: Optional[str] = None) -> bool:
    """Create default configuration file.
    
    Args:
        config_path: Path to configuration file
            If None, uses default location
    
    Returns:
        True if configuration was created successfully, False otherwise
    """
    # Determine config path
    if config_path is None:
        config_path = get_default_config_path()
    
    # Check if file already exists
    if os.path.exists(config_path):
        logger.warning(f"Configuration file already exists at {config_path}")
        return False
    
    # Create default configuration
    default_config = DEFAULT_CONFIG.copy()
    
    # Add comments for documentation
    comments = (
        "# Committy Configuration\n"
        "# --------------------\n"
        "# model: LLM model to use (e.g., gemma3:12b, phi3:mini, llama3:70b)\n"
        "# format: Commit message format (conventional, angular, simple)\n"
        "# max_tokens: Maximum tokens for LLM response\n"
        "# temperature: Temperature for LLM (0.0-1.0, lower is more deterministic)\n"
        "# no_confirm: Skip confirmation prompt (true/false)\n"
        "# with_scope: Include scope in commit message (true/false)\n"
        "# editor: Editor to use for message editing (null uses system default)\n"
        "# prompt_template: Prompt template to use (enhanced, simple)\n"
        "\n"
    )
    
    # Save configuration with comments
    try:
        os.makedirs(os.path.dirname(config_path), exist_ok=True)
        with open(config_path, "w") as f:
            f.write(comments)
            yaml.dump(default_config, f, default_flow_style=False)
        logger.info(f"Created default configuration at {config_path}")
        return True
    except Exception as e:
        logger.error(f"Error creating default configuration at {config_path}: {e}")
        return False


def _load_from_env() -> Dict[str, Any]:
    """Load configuration from environment variables.
    
    Returns:
        Configuration dictionary with values from environment variables
    """
    config = {}
    
    # Define mappings from environment variables to config keys
    env_mappings = {
        "COMMITTY_MODEL": "model",
        "OLLAMA_MODEL": "model",  # Alternative for model
        "COMMITTY_FORMAT": "format",
        "COMMITTY_MAX_TOKENS": "max_tokens",
        "COMMITTY_TEMP": "temperature",
        "AUTOCOMMIT_TEMP": "temperature",  # For backward compatibility
        "COMMITTY_NO_CONFIRM": "no_confirm",
        "COMMITTY_WITH_SCOPE": "with_scope",
        "COMMITTY_EDITOR": "editor",
        "EDITOR": "editor",  # System editor
        "COMMITTY_PROMPT_TEMPLATE": "prompt_template",
    }
    
    # Load values from environment
    for env_var, config_key in env_mappings.items():
        if env_var in os.environ:
            value = os.environ[env_var]
            
            # Convert boolean strings
            if value.lower() in ("true", "yes", "1"):
                value = True
            elif value.lower() in ("false", "no", "0"):
                value = False
            # Convert numeric strings
            elif value.replace(".", "", 1).isdigit():
                if "." in value:
                    value = float(value)
                else:
                    value = int(value)
            
            config[config_key] = value
    
    return config