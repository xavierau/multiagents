# Workers API Reference

Workers are stateless task executors that implement specific business logic. The framework provides decorator-based APIs for easy worker creation.

## Decorators

### `@worker(name: str, config: Optional[WorkerConfig] = None)`

Decorator for creating function-based workers.

**Parameters:**
- `name` (str): Unique worker name for registration
- `config` (Optional[WorkerConfig]): Worker configuration

**Example:**
```python
from multiagents import worker

@worker("process_order")
async def process_order_worker(context):
    order = context["order"]
    # Process the order
    return {"order_id": order["id"], "status": "processed"}
```

### `@dspy_worker(name: str, signature: Optional[str] = None, config: Optional[WorkerConfig] = None)`

Decorator for creating DSPy-powered LLM workers.

**Parameters:**
- `name` (str): Unique worker name
- `signature` (Optional[str]): DSPy signature for input/output specification
- `config` (Optional[WorkerConfig]): Worker configuration

**Example:**
```python
from multiagents import dspy_worker

@dspy_worker("generate_email", signature="customer_name, order_details -> email_content")
async def email_generator_worker(context):
    # DSPy will automatically handle LLM interaction
    return context  # Framework handles DSPy integration
```

## Worker Function Signature

All worker functions must follow this pattern:

```python
async def worker_function(context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Worker function signature.
    
    Args:
        context: Dictionary containing input data and previous step results
        
    Returns:
        Dictionary containing worker results (merged into workflow context)
        
    Raises:
        Any exception will be caught and handled by the framework
    """
    pass
```

### Context Structure

The context dictionary contains:

```python
{
    # Original workflow input
    "original_input": {...},
    
    # Results from previous steps (step_name -> result)
    "step_results": {
        "previous_step": {"result": "value"}
    },
    
    # Current step metadata
    "step_name": "current_step",
    "transaction_id": "uuid",
    "workflow_id": "workflow_name",
    
    # Directly accessible data from previous steps
    "key_from_previous_step": "value"
}
```

### Return Value

Worker functions should return a dictionary:

```python
# Simple result
return {"processed_data": result}

# Multiple values
return {
    "primary_result": main_value,
    "metadata": {"timestamp": "...", "version": "1.0"},
    "status": "completed"
}

# Non-dict return values are automatically wrapped
return "simple_value"  # Becomes {"result": "simple_value"}
```

## Worker Configuration

### `WorkerConfig`

Configuration class for worker behavior.

```python
from multiagents.worker_sdk.base_worker import WorkerConfig

config = WorkerConfig(
    timeout_seconds=30,              # Worker execution timeout
    retry_count=3,                   # Number of retries on failure
    retry_delay_seconds=1.0,         # Initial delay between retries
    retry_backoff_factor=2.0,        # Exponential backoff multiplier
    max_retry_delay_seconds=60.0,    # Maximum delay between retries
    enable_monitoring=True,          # Enable performance monitoring
    tags=["payment", "critical"]     # Worker tags for organization
)

@worker("payment_processor", config=config)
async def payment_worker(context):
    # Implementation
    pass
```

## Worker Types

### Function Workers

Basic workers created with `@worker` decorator:

```python
@worker("data_validator")
async def validate_data(context):
    """Validate input data."""
    data = context.get("data")
    
    if not data:
        raise ValueError("No data provided")
    
    # Validation logic
    validated = clean_and_validate(data)
    
    return {"validated_data": validated, "status": "valid"}

# Sync functions are also supported
@worker("simple_calculator")
def calculate(context):
    """Synchronous calculation worker."""
    a = context["a"]
    b = context["b"]
    return {"result": a + b}
```

### DSPy Workers

LLM-powered workers using DSPy framework:

```python
@dspy_worker("content_generator")
async def generate_content(context):
    """Generate content using LLM."""
    # Context automatically passed to DSPy
    # Return value automatically formatted
    return context

@dspy_worker("sentiment_analyzer", signature="text -> sentiment, confidence")
async def analyze_sentiment(context):
    """Analyze sentiment with structured output."""
    return context
```

### Compensation Workers

Workers that undo actions when workflows fail:

```python
@worker("reserve_inventory")
async def reserve_inventory(context):
    """Reserve inventory items."""
    items = context["items"]
    reservation_id = await inventory_service.reserve(items)
    return {"reservation_id": reservation_id}

@worker("release_inventory")
async def release_inventory(context):
    """Compensation: release reserved inventory."""
    reservation_id = context["reservation_id"]
    await inventory_service.release(reservation_id)
    return {"status": "released"}

# Use in workflow
workflow = (WorkflowBuilder("order_process")
    .add_step("reserve", "reserve_inventory", compensation="release_inventory")
    .build())
```

## Worker Manager

### `WorkerManager`

Manages worker lifecycle and registration.

#### Constructor

```python
WorkerManager(
    event_bus: IEventBus,
    worker_monitor: Optional[WorkerMonitor] = None,
    logger: Optional[ILogger] = None
)
```

#### Methods

##### `register(worker_function: Callable) -> None`

Register a worker function.

**Parameters:**
- `worker_function`: Function decorated with `@worker` or `@dspy_worker`

**Example:**
```python
worker_manager.register(my_worker_function)
```

##### `unregister(worker_name: str) -> bool`

Unregister a worker by name.

**Parameters:**
- `worker_name` (str): Name of worker to unregister

**Returns:**
- `bool`: True if worker was found and unregistered

##### `list_workers() -> List[str]`

Get list of registered worker names.

**Returns:**
- `List[str]`: Names of all registered workers

##### `get_worker(worker_name: str) -> Optional[IWorker]`

Get worker instance by name.

**Parameters:**
- `worker_name` (str): Name of worker

**Returns:**
- `Optional[IWorker]`: Worker instance or None if not found

##### `start() -> None`

Start the worker manager and begin processing commands.

##### `stop() -> None`

Stop the worker manager and cleanup resources.

#### Health Monitoring

```python
# Get worker health status
health = await worker_manager.get_health_status()
print(f"Active workers: {health['active_workers']}")
print(f"Failed workers: {health['failed_workers']}")

# Get performance metrics
metrics = await worker_manager.get_performance_metrics("worker_name")
print(f"Success rate: {metrics['success_rate']}")
print(f"Average duration: {metrics['avg_duration_ms']}ms")
```

## Advanced Worker Patterns

### Error Handling

```python
@worker("robust_worker")
async def robust_worker(context):
    """Worker with comprehensive error handling."""
    try:
        result = await risky_operation(context["data"])
        return {"result": result, "status": "success"}
    
    except ValueError as e:
        # Recoverable error - return partial result
        return {"error": str(e), "status": "partial_failure"}
    
    except Exception as e:
        # Unrecoverable error - let framework handle
        raise WorkerExecutionError(f"Failed to process: {e}")
```

### Conditional Logic

```python
@worker("conditional_processor")
async def conditional_processor(context):
    """Worker with internal conditional logic."""
    data_type = context.get("data_type")
    
    if data_type == "image":
        result = await process_image(context["data"])
    elif data_type == "text":
        result = await process_text(context["data"])
    else:
        raise ValueError(f"Unsupported data type: {data_type}")
    
    return {"processed": result, "type": data_type}
```

### State Validation

```python
@worker("stateful_validator")
async def stateful_validator(context):
    """Validate based on previous step results."""
    # Access previous step results
    payment_result = context.get("payment_status")
    inventory_result = context.get("inventory_status")
    
    if payment_result != "authorized":
        raise ValueError("Cannot proceed without payment authorization")
    
    if inventory_result != "reserved":
        raise ValueError("Cannot proceed without inventory reservation")
    
    return {"validation": "passed", "ready_for_fulfillment": True}
```

### Parallel Data Processing

```python
@worker("parallel_processor")
async def parallel_processor(context):
    """Process multiple items in parallel."""
    items = context["items"]
    
    # Process items concurrently
    tasks = [process_single_item(item) for item in items]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Handle results and exceptions
    processed = []
    errors = []
    
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            errors.append(f"Item {i}: {result}")
        else:
            processed.append(result)
    
    return {
        "processed_items": processed,
        "error_count": len(errors),
        "errors": errors
    }
```

## Integration with Monitoring

Workers automatically integrate with the monitoring system:

```python
# Worker performance is automatically tracked
from multiagents.monitoring import WorkerMonitor

# Get worker statistics
stats = await worker_monitor.get_worker_performance("worker_name")
print(f"Executions: {stats['total_executions']}")
print(f"Success rate: {stats['success_rate']}%")
print(f"Avg duration: {stats['avg_duration_ms']}ms")

# Health status
health = await worker_monitor.check_worker_health("worker_name")
print(f"Status: {health['status']}")  # healthy, degraded, failed
```

## Best Practices

### Worker Design

1. **Keep workers stateless** - All state should be in context
2. **Make workers idempotent** - Safe to retry
3. **Use descriptive names** - Clear purpose and functionality
4. **Handle errors gracefully** - Return partial results when possible
5. **Validate inputs** - Check required context keys

### Performance

1. **Use async functions** - Better concurrency
2. **Configure timeouts** - Prevent hanging workflows
3. **Implement retries** - Handle transient failures
4. **Monitor performance** - Track execution metrics

### Testing

```python
# Unit test workers independently
async def test_my_worker():
    context = {"input": "test_data"}
    result = await my_worker_function(context)
    assert result["status"] == "processed"

# Integration test with framework
async def test_worker_in_workflow():
    workflow = WorkflowBuilder("test").add_step("test", "my_worker").build()
    # Run workflow and verify results
```