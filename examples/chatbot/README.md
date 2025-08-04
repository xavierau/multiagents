# MultiAgents Chatbot Example with DSPy and Gemini

A simple yet powerful command-line chatbot demonstrating DSPy integration with Google Gemini within the MultiAgents framework.

## 🚀 Quick Start

### Prerequisites

1. **Install MultiAgents Framework**
   ```bash
   pip install multiagents
   ```

2. **Set up Google Gemini API Key**
   ```bash
   export GOOGLE_API_KEY="your-gemini-api-key"
   ```
   
   Get your API key from [Google AI Studio](https://makersuite.google.com/app/apikey)

3. **Install Dependencies**
   ```bash
   cd examples/chatbot
   pip install -r requirements.txt
   ```

### Running the Chatbot

```bash
python main.py
```

Or with custom configuration:
```bash
python main.py --config config/custom_config.yaml --personality technical
```

## 🎯 Features

- **Interactive CLI Interface**: Beautiful command-line interface with colored output
- **Multi-turn Conversations**: Context-aware conversations with memory
- **DSPy Integration**: Leveraging DSPy's powerful LLM abstractions
- **Google Gemini Support**: Using latest Gemini models for generation
- **Configurable Personalities**: Switch between different chatbot personalities
- **Conversation History**: Save and export conversation logs
- **Monitoring Integration**: Full MultiAgents framework monitoring support

## 🛠️ Configuration

### Environment Variables

Create a `.env` file in the chatbot directory:
```env
# Required
GOOGLE_API_KEY=your-gemini-api-key

# Optional
CHATBOT_MODEL=gemini/gemini-1.5-flash
CHATBOT_TEMPERATURE=0.7
CHATBOT_MAX_TOKENS=1000
CHATBOT_PERSONALITY=default
```

### Available Models

- `gemini/gemini-1.5-flash` - Fast, efficient model (default)
- `gemini/gemini-1.5-pro` - More capable model for complex conversations

### Personalities

Configure different chatbot personalities in `config/personalities.yaml`:

- **default**: Helpful AI assistant
- **creative**: Creative writing companion
- **technical**: Programming and technical support
- **casual**: Friendly conversational partner

## 💬 Chat Commands

During conversation, you can use these commands:

- `/exit` or `/quit` - End the conversation
- `/clear` - Clear conversation history
- `/save [filename]` - Save conversation to file
- `/personality [name]` - Switch personality
- `/help` - Show available commands

## 🏗️ Architecture

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   CLI Interface │────▶│  DSPy Chatbot    │────▶│  Google Gemini  │
│   (Rich/Click) │     │     Agent        │     │      API        │
└─────────────────┘     └──────────────────┘     └─────────────────┘
         │                       │
         ▼                       ▼
┌─────────────────┐     ┌──────────────────┐
│  Conversation   │     │   MultiAgents    │
│    Manager      │     │   Monitoring     │
└─────────────────┘     └──────────────────┘
```

## 📁 Project Structure

```
chatbot/
├── main.py                    # Entry point
├── requirements.txt           # Dependencies
├── README.md                 # This file
├── config/
│   ├── chatbot_config.yaml   # Main configuration
│   ├── personalities.yaml    # Personality definitions
│   └── .env.example         # Environment template
├── src/
│   ├── __init__.py
│   ├── chatbot_agent.py     # DSPy chatbot implementation
│   ├── cli_interface.py     # CLI interaction logic
│   ├── conversation_manager.py # Context management
│   └── config_loader.py     # Configuration utilities
├── tests/
│   └── test_chatbot.py      # Unit tests
└── examples/
    ├── basic_chat.py        # Simple usage example
    └── personality_demo.py  # Personality showcase
```

## 🧪 Testing

Run tests with:
```bash
pytest tests/
```

## 📊 Monitoring

The chatbot integrates with MultiAgents monitoring:

```yaml
# config/monitoring.yaml
logging:
  level: INFO
  file_path: ./logs/chatbot.log

event_monitoring:
  enabled: true
  trace_conversations: true
```

View logs:
```bash
tail -f logs/chatbot.log
```

## 🎨 Customization

### Creating Custom Personalities

Add to `config/personalities.yaml`:
```yaml
my_personality:
  name: "My Custom Bot"
  system_prompt: "You are a helpful assistant specialized in..."
  temperature: 0.8
  traits:
    - "Always responds with enthusiasm"
    - "Uses relevant emojis"
```

### Extending the Chatbot

```python
from src.chatbot_agent import ChatbotAgent

# Create custom chatbot
class MyCustomChatbot(ChatbotAgent):
    def preprocess_message(self, message: str) -> str:
        # Add custom preprocessing
        return message.lower()
    
    def postprocess_response(self, response: str) -> str:
        # Add custom postprocessing
        return response + " 😊"
```

## 🤝 Contributing

Feel free to submit issues and enhancement requests!

## 📄 License

Same as MultiAgents Framework - MIT License