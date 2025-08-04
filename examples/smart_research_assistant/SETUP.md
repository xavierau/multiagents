# Smart Research Assistant - Setup Guide

A comprehensive guide for setting up the Smart Research Assistant both in development and as a pip-installed library.

## 🚀 Quick Start

### Option 1: Development Setup

```bash
# Clone and navigate to project
git clone <repository-url>
cd multiagents/examples/smart_research_assistant

# Create .env file in project root
cp ../../../.env.example ../../../.env
# Edit ../../../.env with your API keys

# Install dependencies
pip install -r requirements.txt

# Test the setup
python config/env_config.py
```

### Option 2: Pip Installation (Future)

```bash
# Install the package
pip install multiagents-research-assistant

# Create ~/.multiagents.env with your API keys
# (see Configuration section below)

# Test the installation
python -c "from smart_research_assistant.config.env_config import setup_configuration; setup_configuration(verbose=True)"
```

## 🔧 Configuration

The Smart Research Assistant uses a robust configuration system that searches for environment variables in multiple locations:

### Environment File Locations (Priority Order)

1. **`.env`** - Current working directory (highest priority)
2. **`<project_root>/.env`** - Project root directory (for development)
3. **`~/.multiagents.env`** - User home directory (recommended for pip installs)
4. **`~/.env`** - User home directory (alternative)
5. **`/etc/multiagents/.env`** - System-wide (production deployments)
6. **`/usr/local/etc/multiagents/.env`** - System-wide alternative

### Required API Keys

Create an environment file with the following variables:

```bash
# Google API Key for Gemini LLM
# Get from: https://aistudio.google.com/app/apikey
GOOGLE_API_KEY=your_gemini_api_key_here

# Google Custom Search API (Optional but recommended)
# Get from: https://console.cloud.google.com/
GOOGLE_SEARCH_API_KEY=your_google_search_api_key_here
GOOGLE_SEARCH_ENGINE_ID=your_search_engine_id_here

# Alternative environment variable names (also supported)
# GOOGLE_CUSTOM_SEARCH_API_KEY=your_api_key
# GOOGLE_CSE_ID=your_engine_id
```

### Google Custom Search Setup

1. **Get API Key**:
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Enable "Custom Search JSON API"
   - Create API key

2. **Create Search Engine**:
   - Go to [Google Custom Search](https://cse.google.com/)
   - Create new search engine
   - Configure to search the entire web
   - Get your Search Engine ID

3. **Test Configuration**:
   ```bash
   python config/env_config.py
   ```

## 📁 Directory Structure for Pip Installation

When installed via pip, the configuration system automatically detects:

```
~/.multiagents.env                 # User configuration
/etc/multiagents/.env             # System configuration  
/usr/local/etc/multiagents/.env   # Alternative system config
```

## 🧪 Testing Your Setup

### Test Configuration Loading

```bash
# Test environment loading
python config/env_config.py

# Expected output:
# ✅ Loaded environment from: /path/to/.env
# Google Search API: ✅
# Gemini API: ✅
```

### Test Google Custom Search

```bash
# Test web search functionality  
python tools/web_search.py

# Expected output:
# 🔍 Testing Google Custom Search
# 1. [Real search results from Google]
#    Source: google_custom_search
```

### Test Complete Workflow

```bash
# Test full Smart Research Assistant
python cli.py --query "Test query" --verbose

# Should show:
# - Real DSPy/Gemini LLM integration
# - Live Google Custom Search results
# - Multi-agent coordination
```

## 🐛 Troubleshooting

### Issue: "Google Custom Search API credentials not found"

**Solution**: Check environment file loading:
```bash
python -c "
from config.env_config import setup_configuration
config = setup_configuration(verbose=True)
print('Google Search API Key found:', bool(config['google_api_key']))
"
```

### Issue: "DSPy initialization failed"

**Solution**: Verify Gemini API key:
```bash
python -c "
import os
from config.env_config import load_environment_config
load_environment_config()
print('Gemini API Key:', bool(os.getenv('GOOGLE_API_KEY')))
"
```

### Issue: "ModuleNotFoundError" when installed via pip

**Solution**: The configuration system handles both development and installed package scenarios. Ensure you're importing from the correct module path.

## 🔒 Security Best Practices

1. **Never commit .env files** to version control
2. **Use restrictive file permissions** for environment files:
   ```bash
   chmod 600 ~/.multiagents.env
   ```
3. **Rotate API keys regularly**
4. **Use different keys** for development/production

## 🌟 Advanced Configuration

### Custom Configuration Path

```python
from config.env_config import load_environment_config

# Load from custom location
success = load_environment_config('/custom/path/.env')
```

### Programmatic Configuration

```python
import os
from config.env_config import setup_configuration

# Set environment variables programmatically
os.environ['GOOGLE_API_KEY'] = 'your_key_here'
os.environ['GOOGLE_SEARCH_API_KEY'] = 'your_search_key'

# Setup configuration
config = setup_configuration(verbose=True)
```

### Production Deployment

For production deployments, consider:

1. **System-wide configuration**: `/etc/multiagents/.env`
2. **Environment variable injection** via Docker/Kubernetes
3. **Secret management** systems (AWS Secrets Manager, etc.)
4. **Configuration validation** in CI/CD pipelines

## 📝 Configuration File Templates

### Development Template (`.env`)
```bash
# Development configuration
GOOGLE_API_KEY=your_gemini_api_key_here
GOOGLE_SEARCH_API_KEY=your_google_search_api_key_here  
GOOGLE_SEARCH_ENGINE_ID=your_search_engine_id_here

# Optional: Redis for advanced features
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
```

### User Template (`~/.multiagents.env`)
```bash
# User-specific configuration for pip installations
GOOGLE_API_KEY=your_gemini_api_key_here
GOOGLE_SEARCH_API_KEY=your_google_search_api_key_here
GOOGLE_SEARCH_ENGINE_ID=your_search_engine_id_here
```

This setup guide ensures the Smart Research Assistant works seamlessly in both development environments and as a distributed pip package! 🎉