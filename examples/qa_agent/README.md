# Q&A Agent System

Two implementations of a Question & Answer system using the MultiAgents framework:

## 🤖 DSPy-Powered Version (Recommended)

**🌟 NEW**: Intelligent Q&A system with real codebase RAG using Gemini LLM!

### Features
- **🧠 Gemini LLM Integration**: Uses DSPy with Google's Gemini for intelligent responses
- **📚 Real Codebase RAG**: Automatically indexes and searches the MultiAgents codebase
- **🔍 Smart Code Analysis**: Extracts classes, functions, and documentation
- **✨ Intelligent Agents**: Three DSPy-powered agents working together

### Architecture
```
User Question → DSPy Coordinator (Gemini) → DSPy RAG (Codebase Search) → DSPy Validator → Response
```

### Agents
1. **DSPy Coordinator** - Uses Gemini to classify questions and plan search strategy
2. **DSPy RAG Agent** - Searches actual codebase and generates contextual responses  
3. **DSPy Validator** - Validates technical accuracy using Gemini

### Usage

```bash
# Set up your Gemini API key
export GOOGLE_API_KEY="your-api-key"

# Install dependencies  
pip install -r requirements.txt

# Run the intelligent Q&A system
python dspy_main.py

# Or run tests
python dspy_main.py --test

# Ask a single question
python dspy_main.py --question "How do I create a worker?"
```

## 📝 Simple Version

Basic Q&A system with static document store:

### Features
- Interactive question clarification
- Document-based answer generation  
- Response validation with regeneration loop
- Simple in-memory document store

### Usage
```bash
python main.py
```

## Example Interaction

```
User: "How do I create a worker?"

Coordinator: "I understand you want to know about creating workers. Are you asking about:
1. Creating a basic @worker decorator function?
2. Creating a DSPy-powered worker?
3. Creating a worker with compensation logic?
Please specify (1-3) or provide more details."

User: "1"

[System retrieves relevant documentation and generates response...]

Response: "To create a basic worker in MultiAgents, use the @worker decorator..."
```