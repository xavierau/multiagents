# Core API Reference

Core utilities, base classes, and shared components used throughout the MultiAgents Framework.

## Saga Context

### `SagaContext`

Container for workflow state and execution context.

#### Constructor

```python
SagaContext(
    transaction_id: str,
    workflow_id: str,
    state: str = "pending",
    current_step: Optional[str] = None,
    step_results: Optional[Dict[str, Any]] = None,
    compensation_stack: Optional[List[str]] = None,
    original_context: Optional[Dict[str, Any]] = None,
    error: Optional[str] = None,
    created_at: Optional[datetime] = None,
    updated_at: Optional[datetime] = None
)
```

#### Attributes

- `transaction_id` (str): Unique workflow instance identifier
- `workflow_id` (str): Workflow definition identifier
- `state` (str): Current workflow state
- `current_step` (Optional[str]): Currently executing step
- `step_results` (Dict[str, Any]): Results from completed steps
- `compensation_stack` (List[str]): Stack of compensations to execute
- `original_context` (Dict[str, Any]): Initial workflow input
- `error` (Optional[str]): Error message if workflow failed
- `created_at` (datetime): Context creation timestamp
- `updated_at` (datetime): Last modification timestamp

#### Methods

##### `add_step_result(step_name: str, result: Dict[str, Any]) -> None`

Add result from a completed step.

**Parameters:**
- `step_name` (str): Name of the completed step
- `result` (Dict[str, Any]): Step execution result

**Example:**
```python
context.add_step_result("validate_order", {
    "order_id": "ORDER-123",
    "status": "valid",
    "total": 99.99
})
```

##### `get_step_result(step_name: str) -> Optional[Dict[str, Any]]`

Get result from a specific step.

**Parameters:**
- `step_name` (str): Name of the step

**Returns:**
- `Optional[Dict[str, Any]]`: Step result or None if not found

**Example:**
```python
validation_result = context.get_step_result("validate_order")
if validation_result:
    order_total = validation_result["total"]
```

##### `add_compensation(compensation_name: str) -> None`

Add a compensation to the stack.

**Parameters:**
- `compensation_name` (str): Name of compensation worker

**Example:**
```python
context.add_compensation("release_inventory")
```

##### `get_compensation_stack() -> List[str]`

Get the compensation stack in reverse order (LIFO).

**Returns:**
- `List[str]`: Compensation workers to execute

##### `get_flattened_context() -> Dict[str, Any]`

Get a flattened context with all data accessible at the top level.

**Returns:**
- `Dict[str, Any]`: Flattened context containing:
  - Original context data
  - Step results (flattened to top level)
  - Metadata (transaction_id, workflow_id, etc.)

**Example:**
```python
# If step results contain {"validate": {"order_id": "123"}}
# Flattened context will have "order_id": "123" at top level
flat_context = context.get_flattened_context()
order_id = flat_context["order_id"]  # Direct access
```

##### `to_dict() -> Dict[str, Any]`

Serialize context to dictionary for persistence.

**Returns:**
- `Dict[str, Any]`: Serialized context

##### `from_dict(data: Dict[str, Any]) -> SagaContext`

Deserialize context from dictionary.

**Parameters:**
- `data` (Dict[str, Any]): Serialized context data

**Returns:**
- `SagaContext`: Restored context instance

## Exception Types

### `MultiAgentsError`

Base exception for all framework errors.

```python
class MultiAgentsError(Exception):
    """Base exception for MultiAgents framework."""
    pass
```

### `WorkflowExecutionError`

Errors during workflow execution.

```python
class WorkflowExecutionError(MultiAgentsError):
    """Raised when workflow execution fails."""
    
    def __init__(self, message: str, transaction_id: Optional[str] = None):
        super().__init__(message)
        self.transaction_id = transaction_id
```

**Example:**
```python
try:
    await orchestrator.execute_workflow("invalid_workflow", {})
except WorkflowExecutionError as e:
    print(f"Workflow failed: {e}")
    if e.transaction_id:
        print(f"Transaction ID: {e.transaction_id}")
```

### `WorkerNotFoundError`

Worker not found in registry.

```python
class WorkerNotFoundError(MultiAgentsError):
    """Raised when a required worker is not found."""
    
    def __init__(self, worker_name: str):
        self.worker_name = worker_name
        super().__init__(f"Worker '{worker_name}' not found")
```

### `EventBusError`

Event bus communication errors.

```python
class EventBusError(MultiAgentsError):
    """Raised when event bus operations fail."""
    pass
```

### `StateStoreError`

State persistence errors.

```python
class StateStoreError(MultiAgentsError):
    """Raised when state store operations fail."""
    pass
```

### `WorkerExecutionError`

Worker execution failures.

```python
class WorkerExecutionError(MultiAgentsError):
    """Raised when worker execution fails."""
    
    def __init__(self, message: str, worker_name: Optional[str] = None):
        super().__init__(message)
        self.worker_name = worker_name
```

## Factory Functions

### `create_simple_framework(workflow: IWorkflowDefinition, config: Optional[Dict[str, Any]] = None) -> Tuple[IEventBus, WorkerManager, Orchestrator]`

Factory function to create a complete framework setup with automatic monitoring.

**Parameters:**
- `workflow` (IWorkflowDefinition): Workflow to execute
- `config` (Optional[Dict[str, Any]]): Framework configuration

**Returns:**
- `Tuple[IEventBus, WorkerManager, Orchestrator]`: Configured framework components

**Example:**
```python
from multiagents.core.factory import create_simple_framework

workflow = WorkflowBuilder("my_workflow").add_step("step1", "worker1").build()
event_bus, worker_manager, orchestrator = await create_simple_framework(workflow)

# Components are pre-configured with monitoring
await event_bus.start()
await worker_manager.start()
await orchestrator.start()
```

### `create_monitoring_components(config: Optional[MonitoringConfig] = None) -> Tuple[EventMonitor, WorkerMonitor, MetricsCollector, ILogger]`

Factory function to create monitoring components.

**Parameters:**
- `config` (Optional[MonitoringConfig]): Monitoring configuration

**Returns:**
- `Tuple[EventMonitor, WorkerMonitor, MetricsCollector, ILogger]`: Monitoring components

**Example:**
```python
from multiagents.core.factory import create_monitoring_components

event_monitor, worker_monitor, metrics_collector, logger = create_monitoring_components()
```

## Utilities

### Context Utilities

#### `merge_contexts(*contexts: Dict[str, Any]) -> Dict[str, Any]`

Merge multiple context dictionaries with conflict resolution.

**Parameters:**
- `*contexts`: Variable number of context dictionaries

**Returns:**
- `Dict[str, Any]`: Merged context

**Example:**
```python
from multiagents.core.utils import merge_contexts

context1 = {"a": 1, "b": 2}
context2 = {"b": 3, "c": 4}
merged = merge_contexts(context1, context2)
# Result: {"a": 1, "b": 3, "c": 4}  # Later values override
```

#### `validate_context(context: Dict[str, Any], required_keys: List[str]) -> None`

Validate that context contains required keys.

**Parameters:**
- `context` (Dict[str, Any]): Context to validate
- `required_keys` (List[str]): Required key names

**Raises:**
- `ValidationError`: If required keys are missing

**Example:**
```python
from multiagents.core.utils import validate_context

try:
    validate_context(context, ["order_id", "customer_id"])
except ValidationError as e:
    print(f"Missing required fields: {e}")
```

### ID Generation

#### `generate_transaction_id() -> str`

Generate a unique transaction ID.

**Returns:**
- `str`: Unique transaction identifier

**Example:**
```python
from multiagents.core.utils import generate_transaction_id

tx_id = generate_transaction_id()
# Returns: "TX-20240101-123456-abc123"
```

#### `generate_correlation_id() -> str`

Generate a unique correlation ID.

**Returns:**
- `str`: Unique correlation identifier

### Serialization Utilities

#### `serialize_datetime(dt: datetime) -> str`

Serialize datetime to ISO format string.

#### `deserialize_datetime(dt_str: str) -> datetime`

Deserialize ISO format string to datetime.

#### `safe_serialize(obj: Any) -> Any`

Safely serialize object to JSON-compatible format.

**Example:**
```python
from multiagents.core.utils import safe_serialize

# Handles datetime, UUID, and custom objects
serialized = safe_serialize({
    "timestamp": datetime.now(),
    "uuid": uuid.uuid4(),
    "custom": CustomObject()
})
```

## Configuration

### Framework Configuration

```python
# Default configuration structure
{
    "redis": {
        "url": "redis://localhost:6379",
        "connection_pool_max_connections": 50
    },
    "monitoring": {
        "enabled": True,
        "config_file": "monitoring.yaml"
    },
    "orchestrator": {
        "state_retention_hours": 168,  # 7 days
        "cleanup_interval_minutes": 60
    },
    "workers": {
        "default_timeout_seconds": 30,
        "default_retry_count": 3,
        "health_check_interval_seconds": 30
    }
}
```

### Environment Variables

The framework supports configuration via environment variables:

- `MULTIAGENTS_REDIS_URL` - Redis connection URL
- `MULTIAGENTS_LOG_LEVEL` - Logging level (DEBUG, INFO, WARNING, ERROR)
- `MULTIAGENTS_MONITORING_CONFIG` - Path to monitoring configuration file
- `MULTIAGENTS_STATE_RETENTION_HOURS` - How long to keep workflow state

## Type Definitions

### Common Type Aliases

```python
from typing import Dict, Any, Optional, List, Callable, Awaitable, Union

# Context types
Context = Dict[str, Any]
StepResult = Dict[str, Any]

# Worker types
WorkerFunction = Callable[[Context], Awaitable[Context]]
SyncWorkerFunction = Callable[[Context], Context]
AnyWorkerFunction = Union[WorkerFunction, SyncWorkerFunction]

# Event handler types
EventHandler = Callable[[BaseEvent], Awaitable[None]]

# Monitoring types
MetricsData = Dict[str, Union[int, float, str]]
HealthStatus = Dict[str, Any]
```

### Generic Types

```python
from typing import TypeVar, Generic

T = TypeVar('T')

class Result(Generic[T]):
    """Generic result wrapper for operations that may fail."""
    
    def __init__(self, value: Optional[T] = None, error: Optional[str] = None):
        self.value = value
        self.error = error
        self.is_success = error is None

    @classmethod
    def success(cls, value: T) -> 'Result[T]':
        return cls(value=value)

    @classmethod
    def failure(cls, error: str) -> 'Result[T]':
        return cls(error=error)
```

## Best Practices

### Error Handling

1. **Use specific exception types** - Don't catch generic Exception
2. **Include context in errors** - Transaction IDs, worker names, etc.
3. **Log errors with full context** - Enable debugging
4. **Implement retry logic** - Handle transient failures

### Context Management

1. **Keep contexts small** - Only include necessary data
2. **Use flattened contexts in workers** - Easier access to data
3. **Validate inputs** - Check required keys early
4. **Avoid mutation** - Create new contexts instead of modifying

### Performance

1. **Use async operations** - Don't block the event loop
2. **Implement proper cleanup** - Release resources when done
3. **Monitor resource usage** - Memory, connections, etc.
4. **Cache expensive operations** - When appropriate

### Testing

```python
# Unit test with SagaContext
def test_saga_context():
    context = SagaContext("tx-123", "workflow-1")
    context.add_step_result("step1", {"result": "success"})
    
    flat = context.get_flattened_context()
    assert flat["result"] == "success"
    assert flat["transaction_id"] == "tx-123"

# Integration test with factory
async def test_framework_setup():
    workflow = WorkflowBuilder("test").add_step("test", "test_worker").build()
    event_bus, worker_manager, orchestrator = await create_simple_framework(workflow)
    
    assert event_bus is not None
    assert worker_manager is not None
    assert orchestrator is not None
```