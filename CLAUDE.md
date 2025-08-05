# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Hybrid Event-Driven Orchestration Framework project in early development. The framework aims to provide developers with a robust, scalable system for building intelligent, multi-step, and fault-tolerant applications by combining orchestration and event-driven patterns.

## Architecture Overview

The framework consists of three core components:

1. **Orchestrator Service** - The centralized "brain" that manages workflow state and coordinates activities
2. **Worker Agents** - Stateless specialists that execute specific tasks via an SDK
3. **Event Bus** - The decoupled communication layer (initially Redis Pub/Sub)

Key architectural principles:
- Separation of "what" (orchestration logic) from "how" (communication)
- All components communicate asynchronously via events
- Support for hierarchical orchestration (workers can be orchestrators for sub-processes)
- Built-in support for compensating transactions and failure handling
- The project also follow SOLID and clean code principles

## Development Setup

Since this is a new project, when implementing:

1. Set up a Python virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

2. Create a requirements.txt or use a modern dependency manager (poetry/pipenv)

3. Suggested project structure:
   ```
   multiagents/
   ├── orchestrator/       # Orchestrator service implementation
   ├── worker_sdk/         # Python SDK for building workers
   ├── event_bus/          # Event bus abstraction layer
   ├── examples/           # Example implementations
   ├── tests/             # Test suite
   └── docs/              # Additional documentation
   ```

## Implementation Guidelines

### Event System
- All events must carry `transaction_id` and `correlation_id` for tracing
- Events should follow a consistent naming convention (e.g., `CommandEvent`, `ResultEvent`)
- Consider using dataclasses or Pydantic for event schemas

### State Management
- Orchestrator state must be persisted (Redis or PostgreSQL)
- Design for horizontal scalability - externalize all state

### Worker SDK Design
- Provide simple decorators or base classes for worker creation
- Workers must be stateless regarding overall workflow
- Include built-in error handling and retry mechanisms

### Testing Strategy
- Unit tests for individual components
- Integration tests for end-to-end workflows
- Load tests for performance validation
- Use pytest as the testing framework

## Common Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Run examples (recommended - handles Python path)
python run_examples.py

# Or run examples individually with proper path setup:
python -c "
import sys; sys.path.insert(0, '.')
import asyncio
from examples.ecommerce_order.main import main
asyncio.run(main())
"

# Run tests
pytest

# Run with coverage
pytest --cov=multiagents

# Run linting
ruff check .
black --check .

# Format code
black .
ruff check --fix .

# Type checking
mypy multiagents/
```

## Implementation Status

### Phase 1 Complete ✓
- **Orchestrator**: Full implementation with state machine and saga pattern
- **Worker SDK**: Decorator-based API with DSPy integration
- **Event Bus**: Redis Pub/Sub implementation with abstraction layer
- **Monitoring System**: Comprehensive observability and debugging capabilities
- **Example**: Complete e-commerce order processing workflow with monitoring

### Key Implementation Details

1. **Event Types**: CommandEvent, ResultEvent, ErrorEvent, CompensationEvent, StatusEvent
2. **Worker Types**: 
   - Function-based workers via @worker decorator
   - Enhanced DSPy-powered workers via @dspy_worker (with tool support, ReAct/CodeAct patterns)
   - Tool definitions via @tool decorator for reusable functions
3. **Workflow Definition**: Fluent API with WorkflowBuilder, support for compensations
4. **State Persistence**: Redis-based with automatic expiration
5. **Worker Management**: WorkerManager handles lifecycle, event subscriptions, and health monitoring
6. **DSPy Integration**: Real DSPy modules with reasoning patterns, tool integration, training data collection
7. **Monitoring**: File-based logging, event lifecycle tracking, worker performance metrics, error tracking

### Monitoring & Observability

The framework includes a comprehensive monitoring system:

#### **ILogger Interface**
- File-based logging with rotation (default)
- Console logging for development
- Composite logging for multiple outputs
- JSON structured logging
- Configurable log levels and formatting

#### **Event Monitoring**
- Tracks complete event lifecycle: dispatch → pickup → processing → completion
- Event correlation and transaction tracking
- Performance metrics (latency, throughput)
- Automatic cleanup and retention management

#### **Worker Performance Monitoring** 
- Success/failure rates per worker
- Processing time statistics
- Health status monitoring with automatic checks
- Error pattern tracking and reporting

#### **Configuration**
```yaml
# monitoring.yaml
logging:
  default_logger: "file"  # or "console", "composite"
  level: "INFO"
  file_path: "./logs/multiagents.log"
  
event_monitoring:
  enabled: true
  trace_retention_hours: 24
  
worker_monitoring:
  enabled: true
  health_check_interval_seconds: 30
```

#### **Usage**
```python
from multiagents.monitoring import MonitoringConfig, EventMonitor, WorkerMonitor

# Setup monitoring
config = MonitoringConfig.from_file("monitoring.yaml")
logger = config.create_logger()
event_monitor = EventMonitor(logger=logger)
worker_monitor = WorkerMonitor(logger=logger)

# Integrate with framework components
event_bus = RedisEventBus(event_monitor=event_monitor, logger=logger)
worker_manager = WorkerManager(event_bus, worker_monitor=worker_monitor, logger=logger)
```

### Enhanced DSPy Worker System

The framework features a powerful DSPy integration with tool support and multiple reasoning patterns:

#### **Worker Types**

```python
from multiagents import dspy_worker, worker, tool

# 1. Basic function worker
@worker("process_data")
async def process_data(context: dict) -> dict:
    return {"processed": context["data"]}

# 2. Simple DSPy signature worker (backward compatible)
@dspy_worker("text_classifier", signature="text -> sentiment: str, confidence: float")
async def classify_text(context: dict) -> dict:
    # DSPy handles the LLM call, additional processing here
    return {"needs_review": context.get("confidence", 0) < 0.7}

# 3. Enhanced DSPy worker with reasoning
@dspy_worker("summarizer", 
            signature="document -> summary: str, key_points: list[str]",
            reasoning="chain_of_thought")
async def summarize_document(context: dict) -> dict:
    return {"word_count": len(context.get("summary", "").split())}
```

#### **Tool System**

```python
# Define reusable tools
@tool("web_search")
async def search_web(query: str) -> list[str]:
    """Search the web for information."""
    # Real implementation with actual web search API
    import httpx
    async with httpx.AsyncClient() as client:
        # Use actual search API here
        response = await client.get(f"https://api.search.com?q={query}")
        return response.json().get("results", [])

@tool("database_query")
def query_database(table: str, filters: dict) -> dict:
    """Query database with filters."""
    # Real database query implementation
    import sqlite3
    conn = sqlite3.connect("app.db")
    # Execute actual query
    cursor = conn.execute(f"SELECT * FROM {table} WHERE ...")
    return {"results": cursor.fetchall()}
```

#### **Tool-Enabled Workers with ReAct**

```python
# Research assistant with real tools
@dspy_worker("research_assistant",
            signature="question -> comprehensive_answer: str, sources: list[str]",
            tools=[search_web, query_database],
            reasoning="react",
            max_iters=5,
            model="gemini/gemini-1.5-pro")
async def research_assistant(context: dict) -> dict:
    """Research assistant that can search web and query database."""
    answer = context.get("comprehensive_answer", "")
    sources = context.get("sources", [])
    
    return {
        "answer_length": len(answer),
        "source_count": len(sources),
        "research_complete": True
    }
```

#### **DSPy Configuration**

```python
import dspy
import os

# Configure DSPy with Gemini
def configure_dspy():
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("GOOGLE_API_KEY environment variable required")
    
    lm = dspy.LM(model="gemini/gemini-1.5-pro", api_key=api_key)
    dspy.configure(lm=lm)

# Use in your application
configure_dspy()
```

#### **Available Reasoning Types**

- **`predict`**: Simple signature execution (default)
- **`chain_of_thought`**: Step-by-step reasoning with explanations
- **`program_of_thought`**: Code-based reasoning for mathematical problems
- **`react`**: Reasoning + Action pattern with tool usage
- **`codeact`**: Code generation with tool assistance

#### **Optimization-Ready Features**

```python
# Workers automatically collect training data
worker = research_assistant

# Get optimization data (for future EPIC-009 tasks)
opt_data = worker.get_optimization_data()
print(f"Training examples: {len(opt_data['training_examples'])}")
print(f"Success rate: {opt_data['success_rate']}")
print(f"Available tools: {opt_data['available_tools']}")
```

### Next Steps

1. **Testing**: Add comprehensive unit and integration tests
2. **Observability**: Integrate OpenTelemetry for distributed tracing
3. **Advanced Features**: Parallel step execution, hierarchical workflows
4. **Documentation**: API reference and additional examples

## Framework Design Principles

- **DSPy Integration**: The framework wraps DSPy to abstract LLM interactions and enable workflow optimization
- **SOLID Principles**: All components follow SOLID principles for maintainability
- **Clean Architecture**: Clear separation between interfaces and implementations
- **Event-Driven**: Fully decoupled communication via event bus
- **Fault Tolerance**: Built-in compensation and rollback mechanisms

## Pending Tasks and Observations

- You should check with context7 mcp with update doc

## Recent Memories

- Remember to use this new project management tool. Review these files if something gets stuck
- For creating example or anything, prefer using the real dspy lm gemini. not hardcode the logic