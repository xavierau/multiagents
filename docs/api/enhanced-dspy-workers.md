# Enhanced DSPy Workers API Reference

The MultiAgents framework provides an enhanced DSPy worker system with tool support, multiple reasoning patterns, and optimization-ready features.

## Overview

The enhanced `@dspy_worker` decorator now supports:
- **Tool Integration**: Use functions as tools with ReAct/CodeAct patterns
- **Multiple Reasoning Types**: predict, chain_of_thought, react, codeact
- **Real DSPy Modules**: Proper DSPy module architecture instead of simple wrappers
- **Optimization Ready**: Training data collection for future optimization
- **Backward Compatibility**: Existing code works unchanged

## Quick Start

```python
from multiagents import dspy_worker, tool
import dspy
import os

# Configure DSPy with Gemini
api_key = os.getenv("GOOGLE_API_KEY")
lm = dspy.LM(model="gemini/gemini-1.5-flash", api_key=api_key)
dspy.configure(lm=lm)

# Simple worker (backward compatible)
@dspy_worker("classifier", signature="text -> sentiment: str")
async def classify_text(context: dict) -> dict:
    return {"processed": True}

# Tool-enabled worker
@tool("web_search")
async def search_web(query: str) -> list[str]:
    # Real web search implementation
    return ["result1", "result2"]

@dspy_worker("research_agent",
            signature="question -> answer: str",
            tools=[search_web],
            reasoning="react")
async def research_agent(context: dict) -> dict:
    return {"research_complete": True}
```

## API Reference

### @dspy_worker Decorator

```python
@dspy_worker(
    worker_type: str,
    *,
    signature: Optional[str] = None,
    tools: Optional[List[Union[Callable, WorkerTool]]] = None,
    reasoning: str = "predict",
    timeout: int = 300,
    retry_attempts: int = 3,
    model: Optional[str] = None,
    max_iters: int = 5,
    enable_optimization: bool = False,
) -> Callable
```

#### Parameters

- **worker_type** (str): Unique identifier for this worker type
- **signature** (Optional[str]): DSPy signature string (e.g., "question -> answer")
- **tools** (Optional[List]): List of tools/functions the worker can use
- **reasoning** (str): Type of reasoning to use
  - `"predict"`: Simple signature execution (default)
  - `"chain_of_thought"`: Step-by-step reasoning with explanations
  - `"program_of_thought"`: Code-based reasoning for mathematical problems
  - `"react"`: Reasoning + Action pattern with tool usage
  - `"codeact"`: Code generation with tool assistance
- **timeout** (int): Timeout in seconds (default: 300)
- **retry_attempts** (int): Number of retry attempts (default: 3)
- **model** (Optional[str]): LLM model to use (e.g., "gemini/gemini-1.5-pro")
- **max_iters** (int): Maximum iterations for ReAct/CodeAct (default: 5)
- **enable_optimization** (bool): Enable optimization features (default: False)

### @tool Decorator

```python
@tool(name: Optional[str] = None)
def tool_function(param: type, ...) -> return_type:
    """Tool description for the LLM."""
    # Tool implementation
    return result
```

#### Parameters

- **name** (Optional[str]): Optional name for the tool (defaults to function name)

#### Requirements

- Function must have type hints for parameters and return value
- Function should have a descriptive docstring
- Both sync and async functions are supported

### Worker Methods

Enhanced DSPy workers provide additional methods:

```python
worker = my_dspy_worker

# Get worker information
worker_type = worker.get_worker_type()
available_tools = worker.get_available_tools()

# Get optimization data (for future optimization features)
opt_data = worker.get_optimization_data()
# Returns: {
#   "training_examples": List[dspy.Example],
#   "execution_history": List[Dict],
#   "success_rate": float,
#   "total_executions": int,
#   "available_tools": List[str]
# }
```

## Examples

### 1. Backward Compatible Worker

```python
# Existing code works unchanged
@dspy_worker("sentiment_classifier", signature="text -> sentiment: str, confidence: float")
async def classify_sentiment(context: dict) -> dict:
    sentiment = context.get('sentiment', 'neutral')
    confidence = context.get('confidence', 0.0)
    return {"needs_review": confidence < 0.8}
```

### 2. Enhanced Reasoning

```python
@dspy_worker("document_summarizer",
            signature="document -> summary: str, key_points: list[str]",
            reasoning="chain_of_thought",
            model="gemini/gemini-1.5-pro")
async def summarize_document(context: dict) -> dict:
    summary = context.get('summary', '')
    key_points = context.get('key_points', [])
    
    return {
        "summary_length": len(summary.split()),
        "key_point_count": len(key_points),
        "quality": "high" if len(key_points) >= 3 else "moderate"
    }
```

### 3. Tool-Enabled ReAct Worker

```python
@tool("database_query")
def query_database(table: str, filters: dict) -> dict:
    """Query database with filters."""
    # Real database implementation
    import sqlite3
    conn = sqlite3.connect("app.db")
    # ... query logic
    return {"results": [...]}

@tool("send_email")
async def send_email(to: str, subject: str, body: str) -> bool:
    """Send email notification."""
    # Real email implementation
    import smtplib
    # ... email sending logic
    return True

@dspy_worker("customer_service_agent",
            signature="customer_request -> response: str, action_taken: str",
            tools=[query_database, send_email],
            reasoning="react",
            max_iters=4,
            model="gemini/gemini-1.5-flash")
async def customer_service_agent(context: dict) -> dict:
    """Customer service agent with database and email capabilities."""
    response = context.get('response', '')
    action = context.get('action_taken', '')
    
    return {
        "response_provided": bool(response),
        "action_completed": bool(action),
        "customer_satisfied": True  # Based on agent's analysis
    }
```

### 4. Code Generation with CodeAct

```python
@tool("search_examples")
async def search_code_examples(language: str, functionality: str) -> list[str]:
    """Search for code examples online."""
    # Real search implementation
    return ["example1", "example2", "example3"]

@dspy_worker("code_generator",
            signature="requirements -> code: str, explanation: str, tests: list[str]",
            tools=[search_code_examples],
            reasoning="codeact",
            model="gemini/gemini-1.5-pro")
async def generate_code(context: dict) -> dict:
    """Generate code with examples and tests."""
    code = context.get('code', '')
    explanation = context.get('explanation', '')
    tests = context.get('tests', [])
    
    return {
        "code_generated": bool(code),
        "has_explanation": bool(explanation),
        "test_count": len(tests),
        "code_quality": "production" if len(tests) >= 3 else "prototype"
    }
```

## Tool Development Guidelines

### 1. Tool Function Requirements

```python
@tool("example_tool")
def example_tool(param1: str, param2: int = 10) -> dict:
    """
    Clear description of what this tool does.
    
    Args:
        param1: Description of parameter 1
        param2: Description of parameter 2 (optional)
    
    Returns:
        Dictionary with results
    """
    # Implementation here
    return {"result": "success"}
```

**Requirements:**
- Type hints for all parameters and return value
- Descriptive docstring
- Handle errors gracefully
- Return structured data (dict/list/str)

### 2. Async Tool Support

```python
@tool("async_api_call")
async def call_external_api(endpoint: str, params: dict) -> dict:
    """Make async API call."""
    import httpx
    async with httpx.AsyncClient() as client:
        response = await client.get(endpoint, params=params)
        return response.json()
```

### 3. Tool Error Handling

```python
@tool("robust_tool")
def robust_tool(input_data: str) -> dict:
    """A tool with proper error handling."""
    try:
        # Tool logic here
        result = process_data(input_data)
        return {"success": True, "data": result}
    except ValueError as e:
        return {"success": False, "error": f"Invalid input: {e}"}
    except Exception as e:
        return {"success": False, "error": f"Unexpected error: {e}"}
```

## DSPy Configuration

### Gemini Configuration

```python
import dspy
import os

def configure_gemini():
    """Configure DSPy with Gemini."""
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("GOOGLE_API_KEY environment variable required")
    
    # Choose appropriate model
    lm = dspy.LM(
        model="gemini/gemini-1.5-flash",  # Fast, cost-effective
        # model="gemini/gemini-1.5-pro",  # More capable, higher cost
        api_key=api_key,
        temperature=0.7,
        max_tokens=2000
    )
    dspy.configure(lm=lm)

# Call before using DSPy workers
configure_gemini()
```

### OpenAI Configuration

```python
def configure_openai():
    """Configure DSPy with OpenAI."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY environment variable required")
    
    lm = dspy.LM(
        model="gpt-4o-mini",  # or "gpt-4", "gpt-3.5-turbo"
        api_key=api_key
    )
    dspy.configure(lm=lm)
```

## Optimization Features (Future)

The enhanced DSPy workers collect training data automatically for future optimization:

```python
# Workers collect execution data
worker = my_research_agent

# Get optimization data
opt_data = worker.get_optimization_data()

# Future optimization (EPIC-009)
# optimizer = dspy.BootstrapFewShot(metric=accuracy)
# optimized_worker = optimizer.compile(worker, trainset=opt_data['training_examples'])
```

## Migration Guide

### From Old DSPy Workers

```python
# OLD (still works)
@dspy_worker("classifier", signature="text -> sentiment")
async def old_classifier(context): 
    return {"result": "processed"}

# NEW (enhanced features)
@dspy_worker("classifier", 
            signature="text -> sentiment: str, confidence: float",
            reasoning="chain_of_thought",
            model="gemini/gemini-1.5-flash")
async def new_classifier(context):
    sentiment = context.get('sentiment', 'neutral')
    confidence = context.get('confidence', 0.0)
    return {"enhanced": True, "confidence": confidence}
```

### Adding Tools to Existing Workers

```python
# Step 1: Define tools
@tool("lookup_data")
def lookup_data(id: str) -> dict:
    return {"data": f"Information for {id}"}

# Step 2: Add tools to worker
@dspy_worker("enhanced_worker",
            signature="query -> response",
            tools=[lookup_data],        # Add this line
            reasoning="react")          # Change reasoning
async def enhanced_worker(context):
    return {"enhanced_with_tools": True}
```

## Best Practices

1. **Choose Appropriate Reasoning**: 
   - Use `predict` for simple tasks
   - Use `chain_of_thought` for complex reasoning
   - Use `react` when tools are needed
   - Use `codeact` for code generation

2. **Tool Design**:
   - Keep tools focused and single-purpose
   - Provide clear documentation
   - Handle errors gracefully
   - Use async for I/O operations

3. **Model Selection**:
   - Use `gemini-1.5-flash` for speed and cost-effectiveness
   - Use `gemini-1.5-pro` for complex reasoning tasks
   - Configure temperature based on creativity needs

4. **Error Handling**:
   - Always handle LLM failures gracefully
   - Provide fallback mechanisms
   - Log errors for debugging

5. **Performance**:
   - Monitor worker execution times
   - Use appropriate max_iters for ReAct
   - Consider caching for expensive operations

## Troubleshooting

### Common Issues

1. **API Key Not Found**
   ```
   ValueError: GOOGLE_API_KEY environment variable required
   ```
   **Solution**: Set your API key: `export GOOGLE_API_KEY='your-key'`

2. **DSPy Not Configured**
   ```
   No language model configured
   ```
   **Solution**: Call `dspy.configure(lm=your_lm)` before using workers

3. **Tool Import Errors**
   ```
   AttributeError: 'WorkerTool' object has no attribute 'dspy_tool'
   ```
   **Solution**: Make sure tools are properly decorated with `@tool`

4. **ReAct Timeout**
   ```
   ReAct exceeded max_iters
   ```
   **Solution**: Increase `max_iters` or simplify the task

### Debug Mode

```python
# Enable debug logging
import logging
logging.basicConfig(level=logging.DEBUG)

# Check worker configuration
print(f"Worker type: {worker.get_worker_type()}")
print(f"Available tools: {worker.get_available_tools()}")
print(f"Reasoning: {worker.dspy_config.reasoning}")
```