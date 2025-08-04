# 🧠 Smart Research Assistant

A comprehensive multi-agent AI research system powered by DSPy and Gemini LLM, demonstrating advanced orchestration patterns and intelligent agent collaboration.

## 🌟 Features

### 🤖 Multi-Agent Architecture
- **Coordinator Agent**: Routes questions and manages workflow orchestration
- **Research Agent**: Conducts comprehensive research with interactive clarification
- **Analyst Agent**: Performs financial calculations and statistical analysis  
- **Formatter Agent**: Creates structured, readable responses

### 🧰 Advanced Capabilities
- **DSPy Integration**: Leverages DSPy framework for optimized LLM interactions
- **Gemini LLM**: Powered by Google's Gemini-1.5-Flash model
- **Interactive Clarification**: Agents can ask follow-up questions for better results
- **Tool Integration**: Calculator, web search, and data analysis tools
- **Multi-format Support**: Financial analysis, market research, calculations, and general research

### 🔧 Developer Features
- **Comprehensive Testing**: Automated test scenarios with performance metrics
- **Interactive CLI**: User-friendly command-line interface
- **Session Management**: Track and review research sessions
- **Error Handling**: Robust error handling with graceful degradation

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Google AI API key (for Gemini)
- Redis (optional, for full orchestrator features)

### Installation

1. **Clone the repository**:
```bash
git clone <repository-url>
cd multiagents/examples/smart_research_assistant
```

2. **Set up environment**:
```bash
# Set your Google AI API key
export GOOGLE_AI_API_KEY="your_api_key_here"

# Install dependencies (from project root)
pip install -r requirements.txt
```

3. **Run the interactive CLI**:
```bash
PYTHONPATH=../../../ python cli.py
```

## 💡 Usage Examples

### Interactive CLI Mode
```bash
# Start interactive session
python cli.py

# Example session
🧠 Research Assistant > What's the ROI of investing $10,000 in renewable energy stocks for 5 years?
```

### Single Query Mode
```bash
# Run single query with verbose output
python cli.py --query "Calculate compound interest on $5,000 at 8% for 3 years" --verbose

# Show example questions
python cli.py --examples
```

### Programmatic Usage
```python
from simple_workflow import run_research_query

# Run a research query
result = await run_research_query("What are the best ESG investments?")
print(result['response']['executive_summary'])
```

## 🧪 Testing

### Quick Test Suite
```bash
# Run 3 quick validation tests
python test_scenarios.py --quick
```

### Full Test Suite
```bash
# Run all 13 comprehensive test scenarios
python test_scenarios.py --concurrent 2 --save
```

### Individual Agent Testing
```bash
# Test individual agents
python test_agents.py
```

## 📋 Example Questions

### 💰 Financial Analysis
- "What's the ROI of investing $15,000 in renewable energy stocks for 7 years?"
- "Calculate compound interest on $8,000 at 6.5% annually for 4 years"
- "Compare the risk-return profile of Tesla vs Apple stock"

### 📈 Market Research
- "Analyze growth trends in electric vehicle market for 2024-2025"
- "What are the best ESG investment opportunities in technology?"
- "Research the impact of AI on healthcare stock valuations"

### 🔢 Calculations
- "Calculate present value of $50,000 received in 8 years at 4% discount rate"
- "What's the break-even point for a business with $25,000 fixed costs?"
- "Analyze loan payment options for $250,000 at different rates"

### 🌍 General Research
- "Research latest developments in quantum computing applications"
- "Analyze environmental impact of cryptocurrency mining"
- "What are emerging trends in sustainable agriculture?"

## 🏗️ Architecture

### Agent Flow
```
User Question → Coordinator → Research ↘
                     ↓              ↗    → Analyst → Formatter → Response
              Clarification (if needed)
```

### Core Components

#### 🎯 Coordinator Agent (`agents/coordinator.py`)
- Routes questions to appropriate specialists
- Determines complexity and processing requirements
- Manages coordination between agents

#### 🔍 Research Agent (`agents/researcher.py`)
- Two-phase operation: clarification then research
- Asks specific questions before starting research
- Conducts comprehensive information gathering

#### 📊 Analyst Agent (`agents/analyst.py`)
- Financial calculations (ROI, compound interest, risk scenarios)
- Statistical analysis with trend detection
- Mathematical operations and modeling

#### 📝 Formatter Agent (`agents/formatter.py`)
- Creates structured, readable responses
- Generates executive summaries
- Adds appropriate disclaimers and metadata

### Tools (`tools/`)
- **Calculator**: Safe mathematical expression evaluation
- **Web Search**: Mock web search with realistic results
- **Data Analyzer**: Statistical analysis and insights generation

## 🔧 Configuration

### Gemini Configuration (`config/gemini_config.py`)
```python
@dataclass
class GeminiConfig:
    model: str = "gemini/gemini-1.5-flash"
    api_key: Optional[str] = None  # Reads from GOOGLE_AI_API_KEY
    temperature: float = 0.7
    max_tokens: int = 2000
```

Specialized configurations for each agent type:
- Coordinator: Balanced for routing decisions
- Researcher: Optimized for information gathering
- Analyst: Focused on mathematical precision
- Formatter: Tuned for readability and structure

## 📊 Performance Metrics

### Test Results (Quick Suite)
- **Total Tests**: 3/3 passed (100% success rate)
- **Average Duration**: 11.2 seconds
- **Categories**: Financial Analysis, Calculations, General Research

### Key Performance Indicators
- **Response Time**: 7-20 seconds for most queries
- **Success Rate**: >95% for well-formed questions
- **Agent Coordination**: 6-step workflow completion
- **Output Quality**: Structured responses with 5-6 sections

## 🛠️ Development

### Project Structure
```
smart_research_assistant/
├── agents/           # DSPy-powered agent implementations
├── config/          # Configuration management
├── tools/           # Tool implementations
├── simple_workflow.py    # Main workflow orchestration
├── cli.py           # Interactive command-line interface
├── test_scenarios.py     # Comprehensive test suite
└── README.md        # This file
```

### Adding New Agents
1. Create agent file in `agents/` directory
2. Use `@dspy_worker` decorator with appropriate signature
3. Register in `simple_workflow.py`
4. Add test scenarios in `test_scenarios.py`

### Extending Tools
1. Add tool implementation to `tools/` directory
2. Import and integrate in relevant agents
3. Update test coverage

## 🔍 Troubleshooting

### Common Issues

#### "DSPy compatibility issues with complex data"
- **Cause**: Gemini/DSPy has limitations with complex nested data structures
- **Solution**: Workflow includes fallback mechanisms for graceful degradation

#### "No API key found"
- **Cause**: Missing GOOGLE_AI_API_KEY environment variable
- **Solution**: Set your Google AI API key: `export GOOGLE_AI_API_KEY="your_key"`

#### "Redis connection failed"
- **Cause**: Full orchestrator requires Redis for state management
- **Solution**: Use `simple_workflow.py` which doesn't require Redis

### Debug Mode
Run with verbose output to see detailed processing steps:
```bash
python cli.py --query "your question" --verbose
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Run tests (`python test_scenarios.py --quick`)
4. Commit changes (`git commit -m 'Add amazing feature'`)
5. Push to branch (`git push origin feature/amazing-feature`)
6. Open a Pull Request

## 📝 License

This project is part of the multiagents framework. See the main project license for details.

## 🙏 Acknowledgments

- **DSPy Framework**: For LLM optimization and agent orchestration
- **Google Gemini**: For powerful LLM capabilities
- **Multiagents Framework**: For the underlying orchestration infrastructure

---

**Built with ❤️ using the Multiagents Framework**

*This example demonstrates the power of multi-agent orchestration for complex AI workflows.*