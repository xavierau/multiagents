# Getting Started with MultiAgents Framework

Welcome! This guide will get you up and running with the MultiAgents Framework in just a few minutes.

## What is MultiAgents Framework?

MultiAgents is a hybrid event-driven orchestration framework that combines:
- **Centralized orchestration** for clear workflow logic
- **Event-driven communication** for scalable, decoupled architecture
- **Built-in monitoring** for production observability
- **DSPy integration** for LLM-powered intelligent workers

## Prerequisites

- **Python 3.8+**
- **Redis Server** (for event bus and state storage)
- Basic knowledge of async/await Python

## Installation

### 1. Start Redis

The framework requires Redis for event communication and state storage.

```bash
# macOS with Homebrew
brew services start redis

# Ubuntu/Debian
sudo systemctl start redis

# Docker
docker run -d -p 6379:6379 redis:alpine

# Test Redis connection
redis-cli ping  # Should return PONG
```

### 2. Set Up the Project

```bash
# Navigate to your multiagents directory
cd /path/to/multiagents

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Verify Installation

```bash
# Run the simple example
python run_examples.py

# Or run directly
python -c "
import sys; sys.path.insert(0, '.')
import asyncio
from examples.simple_workflow import main
asyncio.run(main())
"
```

## Your First Workflow

Let's create a simple data processing workflow from scratch.

### Step 1: Create Workers

Workers are the building blocks that execute tasks. Create `my_first_workflow.py`:

```python
import asyncio
from multiagents import worker
from multiagents.core.factory import create_simple_framework
from multiagents.orchestrator.workflow import WorkflowBuilder

# Define workers using decorators
@worker("validate_data")
async def validate_data_worker(context):
    """Validate input data."""
    data = context.get("data", "")
    
    if not data:
        raise ValueError("No data provided")
    
    if not isinstance(data, str) or len(data) < 3:
        raise ValueError("Data must be a string with at least 3 characters")
    
    return {
        "data": data,
        "status": "validated",
        "length": len(data)
    }

@worker("process_data")
async def process_data_worker(context):
    """Process the validated data."""
    data = context["data"]
    
    # Simulate processing
    processed = data.upper().replace(" ", "_")
    
    return {
        "original": data,
        "processed": processed,
        "status": "processed"
    }

@worker("save_result")
async def save_result_worker(context):
    """Save the final result."""
    result = context["processed"]
    
    # Simulate saving to database
    saved_id = f"SAVED_{hash(result) % 10000}"
    
    return {
        "result": result,
        "saved_id": saved_id,
        "status": "saved"
    }
```

### Step 2: Create Workflow

```python
def create_my_workflow():
    """Create a simple data processing workflow."""
    return (WorkflowBuilder("data_processing")
        .add_step("validate", "validate_data")
        .add_step("process", "process_data") 
        .add_step("save", "save_result")
        .build())
```

### Step 3: Execute the Workflow

```python
async def main():
    print("🚀 Running My First Workflow")
    
    # Create workflow
    workflow = create_my_workflow()
    
    # Create framework components with automatic monitoring
    event_bus, worker_manager, orchestrator = await create_simple_framework(workflow)
    
    try:
        # Start the framework
        await event_bus.start()
        
        # Register workers
        worker_manager.register(validate_data_worker)
        worker_manager.register(process_data_worker)
        worker_manager.register(save_result_worker)
        
        await worker_manager.start()
        await orchestrator.start()
        
        # Execute workflow
        print("📊 Executing workflow...")
        transaction_id = await orchestrator.execute_workflow(
            "data_processing",
            {"data": "hello world"}
        )
        
        # Monitor progress
        while True:
            status = await orchestrator.get_status(transaction_id)
            print(f"State: {status['state']}, Step: {status['current_step']}")
            
            if status['state'] in {"completed", "failed"}:
                print(f"✅ Final state: {status['state']}")
                if status['step_results']:
                    print("📋 Results:")
                    for step, result in status['step_results'].items():
                        print(f"  {step}: {result}")
                break
                
            await asyncio.sleep(1)
            
    finally:
        # Cleanup
        await worker_manager.stop()
        await orchestrator.stop()
        await event_bus.stop()

if __name__ == "__main__":
    asyncio.run(main())
```

### Step 4: Run Your Workflow

```bash
python my_first_workflow.py
```

You should see output like:
```
🚀 Running My First Workflow
📊 Executing workflow...
State: running, Step: validate
State: running, Step: process
State: running, Step: save
✅ Final state: completed
📋 Results:
  validate: {'data': 'hello world', 'status': 'validated', 'length': 11}
  process: {'original': 'hello world', 'processed': 'HELLO_WORLD', 'status': 'processed'}
  save: {'result': 'HELLO_WORLD', 'saved_id': 'SAVED_1234', 'status': 'saved'}
```

## Understanding What Happened

1. **Workers**: You created three workers using the `@worker` decorator
2. **Workflow**: You defined a sequential workflow with three steps
3. **Framework**: The framework automatically handled:
   - Event communication between components
   - State management and persistence
   - Error handling and monitoring
   - Async coordination

## Key Concepts

### Workers
- Stateless functions that execute specific tasks
- Decorated with `@worker("worker_name")`
- Receive context dict, return result dict
- Can be sync or async functions

### Workflows
- Define the sequence and logic of steps
- Built using `WorkflowBuilder` for fluent API
- Support conditional branching and error handling
- Automatically managed by the orchestrator

### Event Bus
- Handles all communication between components
- Uses Redis Pub/Sub for scalability
- Provides guaranteed delivery and ordering
- Includes built-in monitoring

### Monitoring
- Automatically tracks all events and worker performance
- Provides structured logging and metrics
- Includes health checking and alerting
- Essential for production deployments

## Next Steps

Now that you have a working workflow, explore these topics:

1. **[Worker Development Guide](worker-development.md)** - Learn about advanced worker patterns
2. **[Examples](../examples/)** - Study the complete e-commerce example
3. **[Error Handling Tutorial](../tutorials/error-handling.md)** - Add compensations and retry logic
4. **[Monitoring Guide](monitoring.md)** - Set up production monitoring
5. **[DSPy Integration](dspy-integration.md)** - Add LLM-powered workers

## Common Issues

### Redis Connection Errors
```
ConnectionError: Error 61 connecting to localhost:6379. Connection refused.
```
**Solution**: Start Redis server (`redis-server` or `brew services start redis`)

### Import Errors
```
ModuleNotFoundError: No module named 'multiagents'
```
**Solution**: Run from project root or add to Python path:
```python
import sys
sys.path.insert(0, '.')
```

### Worker Not Found
```
ValueError: Worker 'my_worker' not found
```
**Solution**: Ensure worker is registered before starting:
```python
worker_manager.register(my_worker_function)
```

## Framework Components Overview

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Orchestrator  │    │   Event Bus     │    │ Worker Manager  │
│                 │    │                 │    │                 │
│ • State machine │◄──►│ • Redis Pub/Sub │◄──►│ • Worker registry│
│ • Workflow exec │    │ • Event routing │    │ • Lifecycle mgmt│
│ • Error handling│    │ • Monitoring    │    │ • Health checks │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌─────────────────┐
                    │   Monitoring    │
                    │                 │
                    │ • Event tracking│
                    │ • Metrics       │
                    │ • Structured log│
                    └─────────────────┘
```

This gives you a solid foundation for building distributed workflows with the MultiAgents Framework!