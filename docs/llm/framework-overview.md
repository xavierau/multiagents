# MultiAgents Framework - LLM Overview

## Core Framework Concepts

The MultiAgents Framework is a hybrid event-driven orchestration system that combines the benefits of orchestration (centralized control) with event-driven architecture (loose coupling). It enables building complex, fault-tolerant workflows with built-in compensation mechanisms.

### Architecture Components

```
┌─────────────────────────────────────────────────────────────────────┐
│                    MULTIAGENTS FRAMEWORK ARCHITECTURE               │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐ │
│  │   ORCHESTRATOR  │    │   EVENT BUS     │    │    WORKERS      │ │
│  │                 │    │                 │    │                 │ │
│  │ • Workflow mgmt │◄──►│ • Redis Pub/Sub │◄──►│ • Task execution│ │
│  │ • State tracking│    │ • Event routing │    │ • DSPy support  │ │
│  │ • Compensation  │    │ • Monitoring    │    │ • Error handling│ │
│  │ • Saga pattern  │    │ • Persistence   │    │ • Specialization│ │
│  └─────────────────┘    └─────────────────┘    └─────────────────┘ │
│           │                       │                       │         │
│           └───────────────────────┼───────────────────────┘         │
│                                   │                                 │
│                    ┌─────────────────┐                              │
│                    │   MONITORING    │                              │
│                    │                 │                              │
│                    │ • Event tracking│                              │
│                    │ • Performance   │                              │
│                    │ • Error logging │                              │
│                    │ • Health checks │                              │
│                    └─────────────────┘                              │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### Key Design Principles

1. **Separation of Concerns**: "What" (orchestration logic) is separated from "how" (communication)
2. **Event-Driven**: All components communicate via asynchronous events
3. **Fault Tolerance**: Built-in saga pattern with compensating transactions
4. **Stateless Workers**: Workers are stateless regarding overall workflow
5. **Hierarchical**: Workers can be orchestrators for sub-processes
6. **Observable**: Comprehensive monitoring and tracing capabilities

## Core Data Structures

### Event Types

```python
# Command Events - Trigger worker execution
CommandEvent = {
    "event_type": "command",
    "worker_name": str,
    "transaction_id": str,
    "correlation_id": str,
    "context": Dict[str, Any],
    "timestamp": str,
    "retry_count": int
}

# Result Events - Worker execution results
ResultEvent = {
    "event_type": "result", 
    "worker_name": str,
    "transaction_id": str,
    "correlation_id": str,
    "result": Dict[str, Any],
    "success": bool,
    "timestamp": str
}

# Error Events - Worker execution failures
ErrorEvent = {
    "event_type": "error",
    "worker_name": str, 
    "transaction_id": str,
    "correlation_id": str,
    "error": str,
    "timestamp": str,
    "retry_count": int
}

# Compensation Events - Rollback actions
CompensationEvent = {
    "event_type": "compensation",
    "worker_name": str,
    "transaction_id": str,
    "correlation_id": str,
    "context": Dict[str, Any],
    "timestamp": str
}

# Status Events - Workflow status updates
StatusEvent = {
    "event_type": "status",
    "transaction_id": str,
    "state": str,  # pending, running, completed, failed, compensated
    "current_step": Optional[str],
    "step_results": Dict[str, Any],
    "timestamp": str
}
```

### Workflow States

```python
WorkflowState = Literal[
    "pending",      # Workflow created but not started
    "running",      # Workflow executing steps
    "completed",    # All steps completed successfully
    "failed",       # Step failed, no compensation needed
    "compensated",  # Failed with compensation executed
    "cancelled"     # Workflow cancelled by user
]
```

### Worker Types

1. **Function Workers**: Simple function-based workers
2. **DSPy Workers**: LLM-powered workers using DSPy framework
3. **Compensation Workers**: Special workers for rollback operations

## Essential Patterns

### 1. Basic Worker Pattern

```python
from multiagents import worker

@worker("worker_name")
async def worker_function(context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Standard worker pattern.
    
    Args:
        context: Input data from previous steps or initial input
        
    Returns:
        Dict containing worker results
        
    Raises:
        WorkerExecutionError: For retryable errors
        ValueError: For validation errors (non-retryable)
    """
    # Input validation
    required_field = context.get("required_field")
    if not required_field:
        raise ValueError("Missing required field")
    
    # Worker logic
    result = perform_work(required_field)
    
    # Return structured result
    return {
        "output_field": result,
        "status": "success",
        "timestamp": datetime.utcnow().isoformat()
    }
```

### 2. DSPy Worker Pattern

```python
from multiagents import dspy_worker
import dspy

class WorkerSignature(dspy.Signature):
    """Define structured input/output for LLM."""
    input_field = dspy.InputField(desc="Input description")
    output_field = dspy.OutputField(desc="Output description")

@dspy_worker("llm_worker", signature=WorkerSignature)
async def llm_worker(context: Dict[str, Any]) -> Dict[str, Any]:
    """
    DSPy-powered worker with LLM integration.
    
    The framework automatically handles LLM interaction based on signature.
    """
    return {
        "input_field": context.get("input"),
        "processing_type": "llm_analysis"
    }

@llm_worker.post_process
async def validate_llm_output(dspy_result: Dict[str, Any], original_context: Dict[str, Any]) -> Dict[str, Any]:
    """Post-process LLM results for validation and enhancement."""
    # Validate LLM output
    validated_output = validate_output(dspy_result)
    
    # Add metadata
    validated_output["validation_timestamp"] = datetime.utcnow().isoformat()
    
    return validated_output
```

### 3. Workflow Definition Pattern

```python
from multiagents.orchestrator.workflow import WorkflowBuilder

def create_workflow():
    """Standard workflow creation pattern."""
    return (WorkflowBuilder("workflow_name")
        .add_step("step1", "worker1")
        .add_step("step2", "worker2", compensation="compensation_worker2")
        .add_step("step3", "worker3", compensation="compensation_worker3")
        .build())
```

### 4. Compensation Worker Pattern

```python
@worker("compensation_worker")
async def compensation_worker(context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Compensation worker for rollback operations.
    
    Should be idempotent and robust against failures.
    """
    resource_id = context.get("resource_id")
    
    if not resource_id:
        return {"status": "no_action_needed"}
    
    try:
        # Perform rollback
        release_resource(resource_id)
        
        return {
            "status": "success",
            "resource_released": resource_id,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        # Don't raise exceptions in compensation workers
        # Log and return failure status
        return {
            "status": "failed",
            "error": str(e),
            "requires_manual_intervention": True
        }
```

### 5. Framework Setup Pattern

```python
from multiagents.core.factory import create_simple_framework

async def setup_framework(workflow):
    """Standard framework setup pattern."""
    # Create framework components
    event_bus, worker_manager, orchestrator = await create_simple_framework(workflow)
    
    # Start framework
    await event_bus.start()
    
    # Register workers
    workers = [worker1, worker2, worker3, compensation_worker2, compensation_worker3]
    for worker_func in workers:
        worker_manager.register(worker_func)
    
    await worker_manager.start()
    await orchestrator.start()
    
    return event_bus, worker_manager, orchestrator

async def shutdown_framework(event_bus, worker_manager, orchestrator):
    """Standard framework shutdown pattern."""
    await worker_manager.stop()
    await orchestrator.stop() 
    await event_bus.stop()
```

### 6. Workflow Execution Pattern

```python
async def execute_workflow(orchestrator, workflow_name, input_data):
    """Standard workflow execution pattern."""
    # Start workflow
    transaction_id = await orchestrator.execute_workflow(workflow_name, input_data)
    
    # Monitor execution
    completed_states = {"completed", "failed", "compensated", "cancelled"}
    
    while True:
        status = await orchestrator.get_status(transaction_id)
        
        if status['state'] in completed_states:
            return status
        
        await asyncio.sleep(1)  # Poll interval
```

## Error Handling Strategies

### Error Categories

1. **Validation Errors**: Input validation failures (don't trigger compensation)
2. **Resource Errors**: Resource allocation failures (may trigger compensation)
3. **Service Errors**: External service failures (retryable vs non-retryable)
4. **System Errors**: Unexpected failures (trigger compensation)

### Error Handling Pattern

```python
from multiagents.core.exceptions import WorkerExecutionError

@worker("error_handling_worker")
async def error_handling_worker(context: Dict[str, Any]) -> Dict[str, Any]:
    """Comprehensive error handling pattern."""
    
    # Input validation (non-retryable)
    if not context.get("required_field"):
        raise ValueError("Missing required field")
    
    try:
        # Main worker logic
        result = await external_service_call(context)
        
        return {
            "result": result,
            "status": "success"
        }
        
    except TimeoutError:
        # Retryable error
        raise WorkerExecutionError("Service timeout - retryable")
    
    except ServiceUnavailableError:
        # Non-retryable service error
        return {
            "status": "service_unavailable",
            "error": "Service temporarily unavailable",
            "retry_later": True
        }
    
    except Exception as e:
        # Unexpected error - let framework handle
        raise WorkerExecutionError(f"Unexpected error: {str(e)}")
```

## Monitoring Integration

### Event Monitoring

```python
from multiagents.monitoring import EventMonitor

# Monitor event lifecycle
event_monitor = EventMonitor(logger=logger)

# Events are automatically tracked:
# - dispatch -> pickup -> processing -> completion
# - Latency measurements
# - Error tracking
# - Correlation tracking
```

### Worker Performance Monitoring

```python
from multiagents.monitoring import WorkerMonitor

# Monitor worker performance
worker_monitor = WorkerMonitor(logger=logger)

# Metrics tracked:
# - Success/failure rates
# - Processing times
# - Health status
# - Error patterns
```

## Configuration Patterns

### DSPy Configuration

```python
import dspy
import os

def configure_dspy_for_environment():
    """Environment-specific DSPy configuration."""
    env = os.getenv("ENVIRONMENT", "development")
    
    if env == "production":
        lm = dspy.OpenAI(
            model="gpt-3.5-turbo",
            api_key=os.getenv("OPENAI_API_KEY"),
            max_tokens=300,
            temperature=0.3
        )
    else:
        lm = dspy.OpenAI(
            model="gpt-3.5-turbo", 
            api_key=os.getenv("OPENAI_API_KEY"),
            max_tokens=200,
            temperature=0.8
        )
    
    dspy.settings.configure(lm=lm)
    return lm
```

### Monitoring Configuration

```python
from multiagents.monitoring import MonitoringConfig

config = MonitoringConfig.from_file("monitoring.yaml")
# or
config = MonitoringConfig(
    logging={"default_logger": "file", "level": "INFO"},
    event_monitoring={"enabled": True, "trace_retention_hours": 24},
    worker_monitoring={"enabled": True, "health_check_interval_seconds": 30}
)
```

## Performance Considerations

### Resource Management

1. **Connection Pooling**: Use connection pools for Redis and databases
2. **Batch Processing**: Group similar operations for efficiency
3. **Caching**: Cache LLM responses and expensive computations
4. **Memory Management**: Monitor memory usage in long-running workflows

### Scaling Patterns

1. **Horizontal Scaling**: Multiple worker instances
2. **Load Balancing**: Distribute work across instances
3. **Event Bus Clustering**: Redis cluster for high availability
4. **State Management**: External state storage for scalability

## Common Implementation Challenges

### Challenge 1: Worker State Management

**Problem**: Workers need to maintain state across retries
**Solution**: Use external storage (Redis, database) for worker state

### Challenge 2: Long-Running Operations

**Problem**: Some operations take longer than timeout limits
**Solution**: Break into smaller steps or use async patterns with status polling

### Challenge 3: Partial Failures

**Problem**: Some items in a batch succeed, others fail
**Solution**: Design workers to handle partial success and report detailed status

### Challenge 4: Compensation Failures

**Problem**: Compensation workers themselves can fail
**Solution**: Make compensations idempotent and log failures for manual intervention

## Testing Strategies

### Unit Testing Workers

```python
import pytest

@pytest.mark.asyncio
async def test_worker():
    """Test worker in isolation."""
    context = {"input": "test_value"}
    result = await worker_function(context)
    
    assert result["status"] == "success"
    assert "output" in result
```

### Integration Testing

```python
@pytest.mark.asyncio
async def test_workflow():
    """Test complete workflow."""
    workflow = create_workflow()
    event_bus, worker_manager, orchestrator = await create_simple_framework(workflow)
    
    try:
        await setup_framework_components()
        
        transaction_id = await orchestrator.execute_workflow("test_workflow", test_data)
        status = await wait_for_completion(orchestrator, transaction_id)
        
        assert status['state'] == 'completed'
    finally:
        await shutdown_framework_components()
```

This overview provides the foundational understanding needed to work effectively with the MultiAgents Framework. For specific implementation patterns, refer to the other LLM documentation files.