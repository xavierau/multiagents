"""
Environment configuration utilities for Smart Research Assistant.

This module provides robust environment variable loading that works in:
1. Development environments
2. Production deployments  
3. Pip-installed packages
4. Different working directories
"""

import os
from typing import Optional, List
from dotenv import load_dotenv


def find_project_root(start_path: Optional[str] = None) -> Optional[str]:
    """
    Find project root by looking for common project indicators.
    
    Args:
        start_path: Starting directory (defaults to current file's directory)
        
    Returns:
        Project root path or None if not found
    """
    if start_path is None:
        start_path = os.path.dirname(os.path.abspath(__file__))
    
    current_dir = start_path
    
    # Walk up the directory tree to find project root
    while current_dir != os.path.dirname(current_dir):  # Stop at filesystem root
        # Check for common project root indicators
        for indicator in ['setup.py', 'pyproject.toml', '.git', 'requirements.txt', 'MANIFEST.in']:
            if os.path.exists(os.path.join(current_dir, indicator)):
                return current_dir
        current_dir = os.path.dirname(current_dir)
    
    return None


def get_env_file_locations() -> List[str]:
    """
    Get list of potential .env file locations in priority order.
    
    Returns:
        List of .env file paths to check
    """
    project_root = find_project_root()
    
    locations = [
        '.env',  # Current working directory (highest priority)
    ]
    
    # Add project root if found
    if project_root:
        locations.append(os.path.join(project_root, '.env'))
    
    # Add user home directory
    locations.append(os.path.join(os.path.expanduser('~'), '.multiagents.env'))
    locations.append(os.path.join(os.path.expanduser('~'), '.env'))
    
    # Add system-wide locations (for production)
    locations.extend([
        '/etc/multiagents/.env',
        '/usr/local/etc/multiagents/.env'
    ])
    
    return locations


def load_environment_config(verbose: bool = False) -> bool:
    """
    Load environment configuration from the first available .env file.
    
    Args:
        verbose: Print debug information about loading process
        
    Returns:
        True if any .env file was loaded, False otherwise
    """
    locations = get_env_file_locations()
    
    for env_path in locations:
        if os.path.exists(env_path):
            load_dotenv(env_path)
            if verbose:
                print(f"✅ Loaded environment from: {env_path}")
            return True
        elif verbose:
            print(f"⏭️  Checked: {env_path} (not found)")
    
    if verbose:
        print("⚠️  No .env file found in any standard location")
    return False


def get_api_credentials() -> tuple[Optional[str], Optional[str]]:
    """
    Get API credentials from environment variables.
    
    Returns:
        Tuple of (google_search_api_key, google_search_engine_id)
    """
    # Try multiple environment variable names for flexibility
    api_key = (
        os.getenv('GOOGLE_SEARCH_API_KEY') or 
        os.getenv('GOOGLE_API_KEY') or
        os.getenv('GOOGLE_CUSTOM_SEARCH_API_KEY')
    )
    
    engine_id = (
        os.getenv('GOOGLE_SEARCH_ENGINE_ID') or
        os.getenv('GOOGLE_CSE_ID') or
        os.getenv('GOOGLE_CUSTOM_SEARCH_ENGINE_ID')
    )
    
    return api_key, engine_id


def setup_configuration(verbose: bool = False) -> dict:
    """
    Set up complete configuration for the Smart Research Assistant.
    
    Args:
        verbose: Print configuration details
        
    Returns:
        Configuration dictionary
    """
    # Load environment
    env_loaded = load_environment_config(verbose=verbose)
    
    # Get API credentials
    google_api_key, google_search_engine_id = get_api_credentials()
    
    config = {
        'env_loaded': env_loaded,
        'project_root': find_project_root(),
        'google_api_key': google_api_key,
        'google_search_engine_id': google_search_engine_id,
        'has_google_search': bool(google_api_key and google_search_engine_id),
        'gemini_api_key': os.getenv('GOOGLE_API_KEY'),
        'has_gemini': bool(os.getenv('GOOGLE_API_KEY'))
    }
    
    if verbose:
        print(f"\n📋 Configuration Summary:")
        print(f"   Project root: {config['project_root']}")
        print(f"   Environment loaded: {config['env_loaded']}")
        print(f"   Google Search API: {'✅' if config['has_google_search'] else '❌'}")
        print(f"   Gemini API: {'✅' if config['has_gemini'] else '❌'}")
    
    return config


# Initialize configuration on import (but don't be verbose by default)
_config = setup_configuration(verbose=False)

# Export commonly used values
PROJECT_ROOT = _config['project_root']
HAS_GOOGLE_SEARCH = _config['has_google_search']
HAS_GEMINI = _config['has_gemini']


if __name__ == "__main__":
    # Demo/test the configuration system
    print("🔧 Smart Research Assistant - Configuration Test")
    print("=" * 60)
    
    config = setup_configuration(verbose=True)
    
    print(f"\n🧪 Testing API Access:")
    if config['has_google_search']:
        print(f"   Google Search: ✅ Ready")
    else:
        print(f"   Google Search: ❌ Missing credentials")
        
    if config['has_gemini']:
        print(f"   Gemini LLM: ✅ Ready")
    else:
        print(f"   Gemini LLM: ❌ Missing credentials")