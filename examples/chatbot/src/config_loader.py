"""
Configuration loader for the chatbot application.

Handles loading configuration from YAML files and environment variables.
"""

import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass
import structlog
from dotenv import load_dotenv


logger = structlog.get_logger()

# Load environment variables
load_dotenv()


@dataclass
class PersonalityConfig:
    """Configuration for a chatbot personality."""
    name: str
    description: str
    system_prompt: str
    temperature: float = 0.7
    traits: list = None
    
    def __post_init__(self):
        if self.traits is None:
            self.traits = []


def load_yaml_config(config_path: str) -> Dict[str, Any]:
    """Load configuration from a YAML file."""
    path = Path(config_path)
    
    if not path.exists():
        logger.warning(f"Configuration file not found: {config_path}")
        return {}
    
    try:
        with open(path, 'r') as f:
            content = f.read()
            
        # Replace environment variables
        content = os.path.expandvars(content)
        
        config = yaml.safe_load(content)
        return config or {}
        
    except Exception as e:
        logger.error(f"Error loading config file: {config_path}", error=str(e))
        return {}


def load_config(config_path: str = "config/chatbot_config.yaml") -> Dict[str, Any]:
    """
    Load main chatbot configuration.
    
    Args:
        config_path: Path to the configuration file
        
    Returns:
        Configuration dictionary
    """
    config = load_yaml_config(config_path)
    
    # Apply environment variable overrides
    env_overrides = {
        "chatbot.model.name": os.getenv("CHATBOT_MODEL"),
        "chatbot.model.temperature": os.getenv("CHATBOT_TEMPERATURE"),
        "chatbot.model.max_tokens": os.getenv("CHATBOT_MAX_TOKENS"),
        "chatbot.default_personality": os.getenv("CHATBOT_PERSONALITY"),
    }
    
    for key, value in env_overrides.items():
        if value is not None:
            # Navigate nested dictionary
            parts = key.split(".")
            current = config
            
            for part in parts[:-1]:
                if part not in current:
                    current[part] = {}
                current = current[part]
            
            # Convert numeric values
            if parts[-1] in ["temperature", "max_tokens"]:
                try:
                    value = float(value) if parts[-1] == "temperature" else int(value)
                except ValueError:
                    logger.warning(f"Invalid numeric value for {key}: {value}")
                    continue
                    
            current[parts[-1]] = value
    
    logger.info("Loaded configuration", config_path=config_path)
    return config


def load_personalities(personalities_path: str = "config/personalities.yaml") -> Dict[str, PersonalityConfig]:
    """
    Load personality configurations.
    
    Args:
        personalities_path: Path to personalities YAML file
        
    Returns:
        Dictionary of personality name to PersonalityConfig
    """
    data = load_yaml_config(personalities_path)
    personalities = {}
    
    for name, config in data.get("personalities", {}).items():
        try:
            personality = PersonalityConfig(
                name=config.get("name", name),
                description=config.get("description", ""),
                system_prompt=config.get("system_prompt", ""),
                temperature=config.get("temperature", 0.7),
                traits=config.get("traits", [])
            )
            personalities[name] = personality
            
        except Exception as e:
            logger.error(f"Error loading personality '{name}'", error=str(e))
    
    logger.info(f"Loaded {len(personalities)} personalities")
    return personalities


def load_personality(name: str, personalities_path: str = "config/personalities.yaml") -> Optional[PersonalityConfig]:
    """
    Load a specific personality by name.
    
    Args:
        name: Personality name
        personalities_path: Path to personalities file
        
    Returns:
        PersonalityConfig or None if not found
    """
    personalities = load_personalities(personalities_path)
    
    if name not in personalities:
        logger.warning(f"Personality '{name}' not found")
        return None
        
    return personalities[name]


def get_monitoring_config(config_path: str = "config/monitoring.yaml") -> Dict[str, Any]:
    """
    Load monitoring configuration.
    
    Args:
        config_path: Path to monitoring config file
        
    Returns:
        Monitoring configuration dictionary
    """
    return load_yaml_config(config_path)


def validate_environment() -> Dict[str, bool]:
    """
    Validate that required environment variables are set.
    
    Returns:
        Dictionary of variable name to whether it's set
    """
    required_vars = {
        "GOOGLE_API_KEY": "Google Gemini API key"
    }
    
    optional_vars = {
        "REDIS_URL": "Redis connection URL",
        "LOG_LEVEL": "Logging level",
        "LOG_FILE": "Log file path"
    }
    
    validation = {}
    
    # Check required variables
    for var, description in required_vars.items():
        is_set = bool(os.getenv(var))
        validation[var] = is_set
        
        if not is_set:
            logger.error(f"Required environment variable not set: {var} ({description})")
    
    # Check optional variables
    for var, description in optional_vars.items():
        is_set = bool(os.getenv(var))
        validation[var] = is_set
        
        if not is_set:
            logger.info(f"Optional environment variable not set: {var} ({description})")
    
    return validation