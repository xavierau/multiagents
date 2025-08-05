# MultiAgents Examples

This directory contains examples demonstrating the MultiAgents framework capabilities, especially the enhanced DSPy worker system with tool support.

## Quick Start

1. **Set up environment**:
   ```bash
   export GOOGLE_API_KEY='your-gemini-api-key'
   ```
   Get your API key from: https://aistudio.google.com/app/apikey

2. **Install dependencies**:
   ```bash
   pip install dspy
   ```

3. **Run examples**:
   ```bash
   python examples/real_dspy_examples.py
   ```

## Examples Overview

### 1. Enhanced DSPy Worker Examples (`enhanced_dspy_worker_examples.py`)
- Demonstrates the refactored `@dspy_worker` decorator
- Shows backward compatibility with existing code
- Covers different reasoning types and tool integration
- **Note**: Shows structure examples, see `real_dspy_examples.py` for actual LLM calls

### 2. Real DSPy Examples (`real_dspy_examples.py`)
- **Uses actual Gemini LLM calls** instead of hardcoded logic
- Demonstrates real tool implementations
- Shows practical examples of:
  - Sentiment analysis with chain of thought
  - Research assistant with ReAct pattern
  - Data analysis with tools
  - Content creation pipeline
  - Document summarization

### 3. Real Workflow Example (`real_workflow_example.py`)
- Complete end-to-end workflow using real DSPy
- Content creation pipeline with multiple stages:
  - Research → Write → Review → Publish
- Demonstrates tool integration in workflows
- **Run with**: `python examples/real_workflow_example.py --simple`

## Featured Examples

### Sentiment Analysis (Real LLM)
```python
@dspy_worker("sentiment_analyzer", 
            signature="text -> sentiment: str, confidence: float, reasoning: str",
            reasoning="chain_of_thought",
            model="gemini/gemini-1.5-flash")
async def analyze_sentiment(context: dict) -> dict:
    # LLM performs actual sentiment analysis
    sentiment = context.get('sentiment', 'neutral')
    confidence = context.get('confidence', 0.0)
    reasoning = context.get('reasoning', '')
    
    return {
        "sentiment_category": sentiment,
        "confidence_score": confidence,
        "llm_reasoning": reasoning,
        "needs_human_review": confidence < 0.8
    }
```

### Research Assistant with Tools (Real LLM + Tools)
```python
@tool("web_search")
async def search_web(query: str) -> List[str]:
    # Real web search implementation
    return [f"Result 1 for: {query}", f"Result 2 for: {query}"]

@dspy_worker("research_assistant",
            signature="question -> comprehensive_answer: str, sources: list[str]",
            tools=[search_web, lookup_knowledge],
            reasoning="react",
            max_iters=4)
async def research_question(context: dict) -> dict:
    # LLM uses ReAct pattern to reason and use tools
    answer = context.get('comprehensive_answer', '')
    sources = context.get('sources_used', [])
    
    return {
        "research_summary": answer,
        "information_sources": sources,
        "research_quality": "high" if len(sources) >= 3 else "moderate"
    }
```

## Tool Examples

The examples include realistic tool implementations:

- **`@tool("web_search")`**: Mock web search with realistic results
- **`@tool("database_query")`**: Database querying with filters
- **`@tool("send_notification")`**: Notification sending (email, Slack, etc.)
- **`@tool("calculate_metrics")`**: Statistical calculations
- **`@tool("fact_check")`**: Content fact-checking
- **`@tool("seo_optimize")`**: SEO optimization analysis

## Running Examples

### Basic Structure Demo
```bash
python examples/enhanced_dspy_worker_examples.py
```
- Shows worker creation and configuration
- Demonstrates all reasoning types
- Works without API keys (structure only)

### Real LLM Examples
```bash
# Set API key first
export GOOGLE_API_KEY='your-key-here'

# Run real examples
python examples/real_dspy_examples.py
```
- Makes actual LLM calls to Gemini
- Uses real tool implementations
- Demonstrates practical applications

### Complete Workflow
```bash
# Simple version (no Redis required)
python examples/real_workflow_example.py --simple

# Full workflow (requires Redis)
python examples/real_workflow_example.py
```
- End-to-end content creation pipeline
- Real DSPy workers with tools
- Workflow orchestration

## Key Features Demonstrated

### ✅ Backward Compatibility
- Existing `@dspy_worker` code works unchanged
- No breaking changes to current implementations

### ✅ Enhanced Reasoning
- **`predict`**: Simple signature execution
- **`chain_of_thought`**: Step-by-step reasoning
- **`react`**: Reasoning + Action with tools
- **`codeact`**: Code generation with tools

### ✅ Tool Integration
- Easy tool definition with `@tool` decorator
- Async and sync tool support
- Tool reuse across workers
- Realistic tool implementations

### ✅ Real LLM Integration
- Actual Gemini LM calls (not hardcoded)
- Proper DSPy configuration
- Error handling and fallbacks

### ✅ Production Ready
- Training data collection for optimization
- Performance monitoring
- Comprehensive error handling
- Workflow orchestration support

## Configuration

### Environment Variables
```bash
# Required for real LLM examples
export GOOGLE_API_KEY='your-gemini-api-key'

# Optional for OpenAI examples
export OPENAI_API_KEY='your-openai-api-key'

# Optional for workflow examples
export REDIS_URL='redis://localhost:6379'
```

### DSPy Configuration
```python
import dspy
import os

# Configure with Gemini (recommended)
api_key = os.getenv("GOOGLE_API_KEY")
lm = dspy.LM(model="gemini/gemini-1.5-flash", api_key=api_key)
dspy.configure(lm=lm)
```

## Troubleshooting

### Common Issues

1. **Missing API Key**
   ```
   ValueError: GOOGLE_API_KEY environment variable required
   ```
   **Solution**: Get API key from https://aistudio.google.com/app/apikey

2. **DSPy Import Error**
   ```
   ModuleNotFoundError: No module named 'dspy'
   ```
   **Solution**: `pip install dspy`

3. **Redis Connection Error** (workflow examples)
   ```
   ConnectionError: Error connecting to Redis
   ```
   **Solution**: Run with `--simple` flag or install Redis

### Debug Mode
```python
# Enable debug logging
import logging
logging.basicConfig(level=logging.DEBUG)

# Check worker configuration
print(f"Worker type: {worker.get_worker_type()}")
print(f"Available tools: {worker.get_available_tools()}")
```

## Next Steps

1. **Explore Examples**: Start with `real_dspy_examples.py`
2. **Create Your Own Tools**: Use the `@tool` decorator
3. **Build Workflows**: Combine workers in pipelines
4. **Optimize Performance**: Use appropriate reasoning types
5. **Production Deployment**: Add error handling and monitoring

For more information, see the [API documentation](../docs/api/enhanced-dspy-workers.md).