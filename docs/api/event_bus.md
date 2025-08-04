# Event Bus API Reference

The event bus provides decoupled communication between all framework components using asynchronous messaging.

## Interfaces

### `IEventBus`

Core event bus interface for publishing and subscribing to events.

#### Methods

##### `start() -> None`

Start the event bus and establish connections.

**Example:**
```python
await event_bus.start()
```

##### `stop() -> None`

Stop the event bus and cleanup connections.

**Example:**
```python
await event_bus.stop()
```

##### `publish(event: BaseEvent) -> None`

Publish an event to the bus.

**Parameters:**
- `event` (BaseEvent): Event to publish

**Raises:**
- `EventBusError`: Failed to publish event

**Example:**
```python
event = CommandEvent(
    transaction_id="tx-123",
    correlation_id="corr-456",
    worker_name="my_worker",
    context={"data": "value"}
)
await event_bus.publish(event)
```

##### `subscribe(event_type: str, handler: Callable[[BaseEvent], Awaitable[None]]) -> str`

Subscribe to events of a specific type.

**Parameters:**
- `event_type` (str): Type of event to listen for
- `handler` (Callable): Async function to handle events

**Returns:**
- `str`: Subscription ID for unsubscribing

**Example:**
```python
async def handle_result(event):
    print(f"Received result: {event.result}")

subscription_id = await event_bus.subscribe("ResultEvent", handle_result)
```

##### `unsubscribe(subscription_id: str) -> bool`

Unsubscribe from events.

**Parameters:**
- `subscription_id` (str): ID returned from subscribe()

**Returns:**
- `bool`: True if unsubscribed successfully

## Implementation

### `RedisEventBus`

Redis Pub/Sub implementation of the event bus.

#### Constructor

```python
RedisEventBus(
    redis_url: str = "redis://localhost:6379",
    event_monitor: Optional[EventMonitor] = None,
    metrics_collector: Optional[MetricsCollector] = None,
    logger: Optional[ILogger] = None
)
```

**Parameters:**
- `redis_url` (str): Redis connection URL
- `event_monitor` (Optional[EventMonitor]): Event tracking
- `metrics_collector` (Optional[MetricsCollector]): Metrics collection
- `logger` (Optional[ILogger]): Logger instance

#### Additional Methods

##### `get_health_status() -> Dict[str, Any]`

Get event bus health information.

**Returns:**
- `Dict[str, Any]`: Health status including connection state, message counts

**Example:**
```python
health = await event_bus.get_health_status()
print(f"Connected: {health['connected']}")
print(f"Messages sent: {health['messages_sent']}")
print(f"Messages received: {health['messages_received']}")
```

##### `get_metrics() -> Dict[str, Any]`

Get performance metrics.

**Returns:**
- `Dict[str, Any]`: Performance metrics

## Event Types

### `BaseEvent`

Base class for all events in the system.

#### Attributes

- `event_id` (str): Unique event identifier
- `event_type` (str): Type of event
- `transaction_id` (str): Workflow transaction ID
- `correlation_id` (str): Request correlation ID
- `timestamp` (datetime): Event creation time
- `metadata` (Dict[str, Any]): Additional metadata

### `CommandEvent`

Event sent to workers to execute tasks.

#### Constructor

```python
CommandEvent(
    transaction_id: str,
    correlation_id: str,
    worker_name: str,
    context: Dict[str, Any],
    step_name: Optional[str] = None,
    retry_count: int = 0
)
```

#### Attributes

- `worker_name` (str): Target worker name
- `context` (Dict[str, Any]): Execution context
- `step_name` (Optional[str]): Workflow step name
- `retry_count` (int): Number of retries attempted

**Example:**
```python
command = CommandEvent(
    transaction_id="tx-123",
    correlation_id="corr-456",
    worker_name="process_payment",
    context={"amount": 100.0, "card": "****1234"},
    step_name="payment"
)
```

### `ResultEvent`

Event containing worker execution results.

#### Constructor

```python
ResultEvent(
    transaction_id: str,
    correlation_id: str,
    worker_name: str,
    result: Dict[str, Any],
    step_name: Optional[str] = None,
    execution_time_ms: Optional[float] = None
)
```

#### Attributes

- `worker_name` (str): Worker that produced result
- `result` (Dict[str, Any]): Worker execution result
- `step_name` (Optional[str]): Workflow step name
- `execution_time_ms` (Optional[float]): Execution duration

**Example:**
```python
result = ResultEvent(
    transaction_id="tx-123",
    correlation_id="corr-456",
    worker_name="process_payment",
    result={"payment_id": "pay-789", "status": "authorized"},
    execution_time_ms=150.5
)
```

### `ErrorEvent`

Event indicating worker or workflow errors.

#### Constructor

```python
ErrorEvent(
    transaction_id: str,
    correlation_id: str,
    error_message: str,
    error_type: str,
    worker_name: Optional[str] = None,
    step_name: Optional[str] = None,
    stack_trace: Optional[str] = None
)
```

#### Attributes

- `error_message` (str): Human-readable error description
- `error_type` (str): Error class name
- `worker_name` (Optional[str]): Worker that failed
- `step_name` (Optional[str]): Failed workflow step
- `stack_trace` (Optional[str]): Full error traceback

**Example:**
```python
error = ErrorEvent(
    transaction_id="tx-123",
    correlation_id="corr-456",
    error_message="Insufficient funds",
    error_type="PaymentError",
    worker_name="process_payment"
)
```

### `CompensationEvent`

Event for executing compensation actions.

#### Constructor

```python
CompensationEvent(
    transaction_id: str,
    correlation_id: str,
    compensation_worker: str,
    context: Dict[str, Any],
    failed_step: str
)
```

#### Attributes

- `compensation_worker` (str): Compensation worker name
- `context` (Dict[str, Any]): Context for compensation
- `failed_step` (str): Step that triggered compensation

### `StatusEvent`

Event for workflow status updates.

#### Constructor

```python
StatusEvent(
    transaction_id: str,
    correlation_id: str,
    status: str,
    current_step: Optional[str] = None,
    progress: Optional[float] = None
)
```

#### Attributes

- `status` (str): Workflow status
- `current_step` (Optional[str]): Current executing step
- `progress` (Optional[float]): Completion percentage (0.0-1.0)

## Event Channels

The event bus uses specific Redis channels for different event types:

### System Channels

- `multiagents:commands` - Worker command events
- `multiagents:results` - Worker result events
- `multiagents:errors` - Error events
- `multiagents:compensations` - Compensation events
- `multiagents:status` - Status update events

### Worker-Specific Channels

- `multiagents:worker:{worker_name}` - Commands for specific worker
- `multiagents:worker:{worker_name}:results` - Results from specific worker

### Workflow-Specific Channels

- `multiagents:workflow:{workflow_id}` - Events for specific workflow type
- `multiagents:transaction:{transaction_id}` - Events for specific workflow instance

## Event Ordering and Delivery

### Guarantees

1. **At-least-once delivery** - Events may be delivered multiple times
2. **Message ordering** - Events are processed in order within a channel
3. **Durability** - Events persist until processed (Redis configuration dependent)

### Handling Duplicates

Workers should be idempotent to handle duplicate events:

```python
@worker("idempotent_worker")
async def my_worker(context):
    # Check if already processed
    if context.get("processed"):
        return context  # Return previous result
    
    # Process only if not already done
    result = await do_work(context)
    result["processed"] = True
    return result
```

## Error Handling

### Event Publishing Failures

```python
try:
    await event_bus.publish(event)
except EventBusError as e:
    # Handle publication failure
    logger.error(f"Failed to publish event: {e}")
    # Implement retry logic or alternative handling
```

### Subscription Failures

```python
async def robust_handler(event):
    try:
        await process_event(event)
    except Exception as e:
        # Log error but don't crash subscription
        logger.error(f"Handler failed: {e}")
        # Optionally publish error event
        error_event = ErrorEvent(
            transaction_id=event.transaction_id,
            correlation_id=event.correlation_id,
            error_message=str(e),
            error_type=type(e).__name__
        )
        await event_bus.publish(error_event)
```

## Monitoring Integration

### Event Lifecycle Tracking

The event bus automatically tracks event lifecycles when configured with monitoring:

```python
from multiagents.monitoring import EventMonitor

event_monitor = EventMonitor()
event_bus = RedisEventBus(event_monitor=event_monitor)

# Events are automatically tracked:
# - Published events
# - Event processing times
# - Success/failure rates
# - Error patterns
```

### Metrics Collection

```python
# Get event metrics
metrics = await event_monitor.get_event_metrics(time_window_minutes=60)
print(f"Total events: {metrics['total_events']}")
print(f"Success rate: {metrics['success_rate']}%")
print(f"Average latency: {metrics['avg_latency_ms']}ms")

# Get specific event type metrics
command_metrics = await event_monitor.get_event_type_metrics("CommandEvent")
```

## Configuration

### Redis Configuration

```python
# Basic configuration
event_bus = RedisEventBus("redis://localhost:6379")

# With authentication
event_bus = RedisEventBus("redis://user:pass@localhost:6379")

# With SSL
event_bus = RedisEventBus("rediss://localhost:6380")

# Connection pooling
event_bus = RedisEventBus(
    redis_url="redis://localhost:6379",
    connection_pool_max_connections=50
)
```

### Event Serialization

Events are automatically serialized to JSON for transmission:

```python
# Custom serialization for complex objects
class CustomEvent(BaseEvent):
    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        # Custom serialization logic
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CustomEvent':
        # Custom deserialization logic
        return cls(**data)
```

## Best Practices

### Event Design

1. **Keep events small** - Large payloads slow down messaging
2. **Include correlation IDs** - Essential for tracing and debugging
3. **Use structured data** - JSON-serializable dictionaries
4. **Validate event data** - Check required fields before publishing

### Performance

1. **Batch events when possible** - Reduce network overhead
2. **Use appropriate Redis configuration** - Memory, persistence, clustering
3. **Monitor event latency** - Track end-to-end processing times
4. **Implement backpressure** - Handle high event volumes gracefully

### Reliability

1. **Implement retries** - Handle transient failures
2. **Use dead letter queues** - Handle permanently failed events
3. **Monitor event bus health** - Detect connection issues early
4. **Plan for Redis failures** - Use Redis clustering or replication