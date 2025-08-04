# API Reference

Complete API documentation for the MultiAgents Framework.

## Core Components

### [Orchestrator](orchestrator.md)
Manages workflow execution and state coordination.
- `IOrchestrator` - Main orchestrator interface
- `Orchestrator` - Implementation with Redis state store
- `WorkflowBuilder` - Fluent API for building workflows

### [Workers](workers.md)  
Stateless task executors with decorator-based API.
- `@worker` - Function-based worker decorator
- `@dspy_worker` - DSPy-powered LLM workers
- `WorkerManager` - Worker lifecycle management

### [Event Bus](event_bus.md)
Decoupled communication layer for all components.
- `IEventBus` - Event bus interface
- `RedisEventBus` - Redis Pub/Sub implementation
- Event types and schemas

### [Monitoring](monitoring.md)
Comprehensive observability and debugging system.
- `EventMonitor` - Event lifecycle tracking
- `WorkerMonitor` - Worker performance monitoring
- `MetricsCollector` - System metrics collection

### [Core](core.md)
Shared utilities and base classes.
- `SagaContext` - Workflow state container
- Exception types and error handling
- Factory functions for easy setup

## Quick Reference

### Creating a Workflow
```python
from multiagents.orchestrator.workflow import WorkflowBuilder

workflow = (WorkflowBuilder("my_workflow")
    .add_step("step1", "worker1")
    .add_step("step2", "worker2", compensation="compensate_worker2")
    .add_conditional_step("step3", "worker3", condition=lambda ctx: ctx.get("proceed"))
    .build())
```

### Creating Workers
```python
from multiagents import worker, dspy_worker

@worker("my_worker")
async def my_worker(context):
    return {"result": "processed"}

@dspy_worker("llm_worker")
async def llm_worker(context):
    return {"answer": "LLM response"}
```

### Framework Setup
```python
from multiagents.core.factory import create_simple_framework

# Automatic setup with monitoring
event_bus, worker_manager, orchestrator = await create_simple_framework(workflow)
```

## Error Handling

All API methods follow consistent error handling patterns:

- **ValidationError**: Invalid input parameters
- **WorkflowExecutionError**: Workflow execution failures  
- **WorkerNotFoundError**: Requested worker doesn't exist
- **EventBusError**: Communication failures
- **StateStoreError**: State persistence issues

## Type Annotations

The framework uses comprehensive type hints:

```python
from typing import Dict, Any, Optional, List, Callable, Awaitable

# Common type aliases
Context = Dict[str, Any]
WorkerFunction = Callable[[Context], Awaitable[Context]]
```

## Async/Await Pattern

All framework operations are async:

```python
# Always use await with framework operations
await event_bus.start()
await worker_manager.register(worker)
transaction_id = await orchestrator.execute_workflow("workflow_id", context)
status = await orchestrator.get_status(transaction_id)
```