# Examples Documentation

This section provides detailed documentation for all examples included with the MultiAgents Framework.

## Available Examples

### [Simple Workflow](simple-workflow.md)
**File**: `examples/simple_workflow.py`

A basic workflow demonstrating core framework concepts:
- Worker creation with decorators
- Sequential step execution
- Basic error handling
- Framework setup and teardown

**Best for**: Understanding framework fundamentals

### [E-commerce Order Processing](ecommerce-order.md)
**File**: `examples/ecommerce_order/`

Complete order processing pipeline featuring:
- Complex workflow with multiple steps
- Compensation pattern (saga pattern)
- DSPy-powered LLM workers
- Comprehensive monitoring
- Error handling and recovery

**Best for**: Real-world application patterns

### [Monitoring Demonstration](monitoring-demo.md)
**File**: `examples/monitoring_example.py`

Comprehensive monitoring example showing:
- Event lifecycle tracking
- Worker performance monitoring
- Error handling and recovery patterns
- System metrics collection
- Custom monitoring configuration

**Best for**: Production monitoring setup

## Quick Start

To run any example:

```bash
# Option 1: Use the example runner (recommended)
python run_examples.py

# Option 2: Run specific example directly
python -c "
import sys; sys.path.insert(0, '.')
import asyncio
from examples.simple_workflow import main
asyncio.run(main())
"
```

## Prerequisites

All examples require:
- Python 3.8+
- Redis server running on localhost:6379
- Dependencies installed: `pip install -r requirements.txt`

## Example Categories

### Learning Examples
- **Simple Workflow** - Framework basics
- **Monitoring Demo** - Observability features

### Production Examples  
- **E-commerce Order** - Complete business workflow
- **DSPy Integration** - LLM-powered workers

### Advanced Patterns
- **Diagram Generation** - Workflow visualization
- **Load Testing** - Performance testing

## Common Patterns Demonstrated

### 1. Framework Setup
```python
from multiagents.core.factory import create_simple_framework

workflow = create_my_workflow()
event_bus, worker_manager, orchestrator = await create_simple_framework(workflow)
```

### 2. Worker Registration
```python
# Register multiple workers
worker_manager.register(worker1)
worker_manager.register(worker2) 
worker_manager.register(worker3)
```

### 3. Workflow Execution
```python
transaction_id = await orchestrator.execute_workflow(
    "workflow_name", 
    initial_context
)
```

### 4. Status Monitoring
```python
while True:
    status = await orchestrator.get_status(transaction_id)
    if status['state'] in completed_states:
        break
    await asyncio.sleep(1)
```

### 5. Graceful Shutdown
```python
finally:
    await worker_manager.stop()
    await orchestrator.stop()
    await event_bus.stop()
```

## Understanding the Examples

Each example includes:

1. **Purpose Statement** - What the example demonstrates
2. **Architecture Overview** - Component diagram and flow
3. **Key Components** - Workers, workflows, and integrations
4. **Code Walkthrough** - Step-by-step explanation
5. **Configuration** - Settings and customization options
6. **Common Issues** - Troubleshooting guide
7. **Extensions** - How to modify and extend

## Running Examples in Development

### Development Setup
```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate

# Install in development mode
pip install -e .
pip install -r requirements.txt

# Start Redis
redis-server

# Run examples
python run_examples.py
```

### Debugging Examples
```bash
# Run with debug logging
MULTIAGENTS_LOG_LEVEL=DEBUG python examples/simple_workflow.py

# Monitor Redis activity
redis-cli monitor

# Check logs
tail -f logs/multiagents.log
```

## Example Output

Each example provides clear output showing:

```
🚀 Starting [Example Name]
📊 Setting up framework with monitoring...
📡 Starting event bus...
👷 Registering workers...
✓ Registered X workers
🎯 Starting orchestrator...
📦 Creating sample data...
🔄 Executing workflow...
✓ Workflow started with transaction ID: TX-123
📊 Monitoring workflow TX-123...
State: running, Step: validate
State: running, Step: process
State: completed, Step: notify
✅ Workflow completed with state: completed
📋 Results:
  validate: {...}
  process: {...}
  notify: {...}
📈 MONITORING SUMMARY
===================
📨 Total Events: 15
✅ Success Rate: 100.0%
👷 Worker Commands: 8
🎯 Worker Success Rate: 100.0%
🧹 Cleaning up...
✓ Shutdown complete
```

## Next Steps

After reviewing the examples:

1. **Modify Examples** - Change parameters and see the effects
2. **Create Custom Workflows** - Build your own workflows using patterns from examples
3. **Add Monitoring** - Implement custom monitoring for your use cases
4. **Production Deployment** - Use examples as templates for production systems

## Getting Help

If examples don't work as expected:

1. Check Redis is running: `redis-cli ping`
2. Verify Python environment: `python --version`
3. Check dependencies: `pip list | grep -E "(redis|dspy|pydantic)"`
4. Review logs: `cat logs/multiagents.log`
5. Check framework status: Review `BACKLOG.md` for known issues