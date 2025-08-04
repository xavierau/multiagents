# Monitoring API Reference

The monitoring system provides comprehensive observability for the MultiAgents Framework with event tracking, worker performance monitoring, and metrics collection.

## Core Components

### `EventMonitor`

Tracks event lifecycle and performance metrics.

#### Constructor

```python
EventMonitor(
    logger: Optional[ILogger] = None,
    trace_retention_hours: int = 24,
    cleanup_interval_minutes: int = 60
)
```

**Parameters:**
- `logger` (Optional[ILogger]): Logger for monitoring events
- `trace_retention_hours` (int): How long to keep event traces
- `cleanup_interval_minutes` (int): Cleanup frequency

#### Methods

##### `track_event_lifecycle(event: BaseEvent, stage: str) -> None`

Track an event through its lifecycle stages.

**Parameters:**
- `event` (BaseEvent): Event to track
- `stage` (str): Lifecycle stage ('published', 'received', 'processing', 'completed', 'failed')

**Example:**
```python
await event_monitor.track_event_lifecycle(command_event, 'published')
await event_monitor.track_event_lifecycle(command_event, 'processing')
await event_monitor.track_event_lifecycle(result_event, 'completed')
```

##### `get_event_metrics(time_window_minutes: int = 60) -> Dict[str, Any]`

Get aggregated event metrics for a time window.

**Parameters:**
- `time_window_minutes` (int): Time window for metrics

**Returns:**
- `Dict[str, Any]`: Event metrics including:
  - `total_events` (int): Total events processed
  - `success_rate` (float): Success percentage
  - `avg_latency_ms` (float): Average processing latency
  - `error_rate` (float): Error percentage
  - `throughput_per_minute` (float): Events per minute

**Example:**
```python
metrics = await event_monitor.get_event_metrics(time_window_minutes=30)
print(f"Success rate: {metrics['success_rate']:.1f}%")
print(f"Throughput: {metrics['throughput_per_minute']:.1f} events/min")
```

##### `get_event_type_metrics(event_type: str, time_window_minutes: int = 60) -> Dict[str, Any]`

Get metrics for a specific event type.

**Parameters:**
- `event_type` (str): Event type to analyze
- `time_window_minutes` (int): Time window for metrics

**Returns:**
- `Dict[str, Any]`: Type-specific metrics

##### `get_transaction_trace(transaction_id: str) -> List[Dict[str, Any]]`

Get complete event trace for a transaction.

**Parameters:**
- `transaction_id` (str): Transaction to trace

**Returns:**
- `List[Dict[str, Any]]`: Chronological list of events

**Example:**
```python
trace = await event_monitor.get_transaction_trace("tx-123")
for event in trace:
    print(f"{event['timestamp']}: {event['event_type']} - {event['stage']}")
```

### `WorkerMonitor`

Monitors worker performance and health.

#### Constructor

```python
WorkerMonitor(
    logger: Optional[ILogger] = None,
    health_check_interval_seconds: int = 30,
    performance_window_minutes: int = 60
)
```

#### Methods

##### `track_worker_execution(worker_name: str, execution_time_ms: float, success: bool, error: Optional[str] = None) -> None`

Track a worker execution.

**Parameters:**
- `worker_name` (str): Name of worker
- `execution_time_ms` (float): Execution duration
- `success` (bool): Whether execution succeeded
- `error` (Optional[str]): Error message if failed

##### `get_worker_performance(worker_name: str, time_window_minutes: int = 60) -> Dict[str, Any]`

Get performance metrics for a specific worker.

**Parameters:**
- `worker_name` (str): Worker to analyze
- `time_window_minutes` (int): Time window for metrics

**Returns:**
- `Dict[str, Any]`: Worker performance metrics:
  - `total_executions` (int): Total executions
  - `success_rate` (float): Success percentage
  - `avg_duration_ms` (float): Average execution time
  - `p95_duration_ms` (float): 95th percentile duration
  - `error_rate` (float): Error percentage
  - `last_execution` (datetime): Last execution timestamp

**Example:**
```python
perf = await worker_monitor.get_worker_performance("payment_processor")
print(f"Success rate: {perf['success_rate']:.1f}%")
print(f"P95 duration: {perf['p95_duration_ms']:.1f}ms")
```

##### `get_worker_performance_summary(time_window_minutes: int = 60) -> Dict[str, Any]`

Get performance summary for all workers.

**Parameters:**
- `time_window_minutes` (int): Time window for metrics

**Returns:**
- `Dict[str, Any]`: Aggregated performance summary

##### `check_worker_health(worker_name: str) -> Dict[str, Any]`

Check health status of a specific worker.

**Parameters:**
- `worker_name` (str): Worker to check

**Returns:**
- `Dict[str, Any]`: Health status:
  - `status` (str): 'healthy', 'degraded', 'failed'
  - `last_seen` (datetime): Last execution time
  - `recent_error_rate` (float): Recent error percentage
  - `issues` (List[str]): Identified issues

**Example:**
```python
health = await worker_monitor.check_worker_health("order_processor")
if health['status'] != 'healthy':
    print(f"Worker issues: {health['issues']}")
```

##### `get_all_workers_health() -> Dict[str, Dict[str, Any]]`

Get health status for all monitored workers.

**Returns:**
- `Dict[str, Dict[str, Any]]`: Health status per worker

### `MetricsCollector`

Collects system-wide metrics and performance data.

#### Constructor

```python
MetricsCollector(
    logger: Optional[ILogger] = None,
    collection_interval_seconds: int = 60,
    retention_hours: int = 24
)
```

#### Methods

##### `collect_system_metrics() -> Dict[str, Any]`

Collect current system metrics.

**Returns:**
- `Dict[str, Any]`: System metrics:
  - `cpu_usage_percent` (float): CPU utilization
  - `memory_usage_percent` (float): Memory utilization
  - `disk_usage_percent` (float): Disk utilization
  - `active_connections` (int): Redis connections
  - `event_queue_size` (int): Pending events

##### `get_system_metrics(time_window_minutes: int = 60) -> Dict[str, Any]`

Get historical system metrics.

**Parameters:**
- `time_window_minutes` (int): Time window for metrics

**Returns:**
- `Dict[str, Any]`: Historical metrics with trends

**Example:**
```python
metrics = await metrics_collector.get_system_metrics(30)
print(f"Avg CPU: {metrics['avg_cpu_usage']:.1f}%")
print(f"Peak memory: {metrics['peak_memory_usage']:.1f}%")
```

## Configuration

### `MonitoringConfig`

Configuration class for monitoring components.

#### Constructor

```python
MonitoringConfig(
    logging: Optional[Dict[str, Any]] = None,
    event_monitoring: Optional[Dict[str, Any]] = None,
    worker_monitoring: Optional[Dict[str, Any]] = None,
    metrics_collection: Optional[Dict[str, Any]] = None
)
```

#### Class Methods

##### `from_file(file_path: str) -> MonitoringConfig`

Load configuration from YAML file.

**Example:**
```python
config = MonitoringConfig.from_file("monitoring.yaml")
```

##### `from_dict(config_dict: Dict[str, Any]) -> MonitoringConfig`

Create configuration from dictionary.

#### Instance Methods

##### `create_logger() -> ILogger`

Create logger instance based on configuration.

**Returns:**
- `ILogger`: Configured logger

**Example:**
```python
config = MonitoringConfig.from_file("monitoring.yaml")
logger = config.create_logger()
```

### Configuration File Format

```yaml
# monitoring.yaml
logging:
  default_logger: "composite"  # file, console, or composite
  level: "INFO"
  file_path: "./logs/multiagents.log"
  max_file_size_mb: 100
  backup_count: 5
  json_format: true

event_monitoring:
  enabled: true
  trace_retention_hours: 24
  cleanup_interval_minutes: 60
  track_payload_size: true

worker_monitoring:
  enabled: true
  health_check_interval_seconds: 30
  performance_window_minutes: 60
  alert_on_high_error_rate: true
  error_rate_threshold: 0.1

metrics_collection:
  enabled: true
  collection_interval_seconds: 60
  retention_hours: 24
  include_system_metrics: true
```

## Logger Interfaces

### `ILogger`

Interface for structured logging.

#### Methods

##### `debug(message: str, **kwargs) -> None`

Log debug message with context.

##### `info(message: str, **kwargs) -> None`

Log info message with context.

##### `warning(message: str, **kwargs) -> None`

Log warning message with context.

##### `error(message: str, **kwargs) -> None`

Log error message with context.

##### `close() -> None`

Close logger and flush buffers.

### Logger Implementations

#### `FileLogger`

Logs to rotating files with JSON formatting.

```python
from multiagents.monitoring.loggers import FileLogger

logger = FileLogger(
    file_path="./logs/app.log",
    level="INFO",
    max_file_size_mb=100,
    backup_count=5,
    json_format=True
)
```

#### `ConsoleLogger`

Logs to console with colored output.

```python
from multiagents.monitoring.loggers import ConsoleLogger

logger = ConsoleLogger(level="DEBUG", colored=True)
```

#### `CompositeLogger`

Combines multiple loggers.

```python
from multiagents.monitoring.loggers import CompositeLogger, FileLogger, ConsoleLogger

file_logger = FileLogger("./logs/app.log")
console_logger = ConsoleLogger()
composite = CompositeLogger([file_logger, console_logger])
```

## Monitoring Integration

### Framework Integration

Monitoring is automatically integrated when using the factory:

```python
from multiagents.core.factory import create_simple_framework

# Monitoring is automatically set up
event_bus, worker_manager, orchestrator = await create_simple_framework(workflow)

# Access monitoring components
event_monitor = event_bus.event_monitor
worker_monitor = worker_manager.worker_monitor
metrics_collector = event_bus.metrics_collector
```

### Manual Integration

```python
from multiagents.monitoring import MonitoringConfig, EventMonitor, WorkerMonitor
from multiagents.event_bus.redis_bus import RedisEventBus
from multiagents.worker_sdk import WorkerManager

# Create monitoring components
config = MonitoringConfig.from_file("monitoring.yaml")
logger = config.create_logger()
event_monitor = EventMonitor(logger=logger)
worker_monitor = WorkerMonitor(logger=logger)

# Integrate with framework components
event_bus = RedisEventBus(event_monitor=event_monitor, logger=logger)
worker_manager = WorkerManager(event_bus, worker_monitor=worker_monitor, logger=logger)
```

## Alerts and Notifications

### Health Check Alerts

```python
# Check for unhealthy workers
health_summary = await worker_monitor.get_all_workers_health()
for worker_name, health in health_summary.items():
    if health['status'] != 'healthy':
        await send_alert(f"Worker {worker_name} is {health['status']}: {health['issues']}")
```

### Performance Alerts

```python
# Monitor system performance
metrics = await metrics_collector.get_system_metrics(15)  # Last 15 minutes
if metrics['avg_cpu_usage'] > 80:
    await send_alert(f"High CPU usage: {metrics['avg_cpu_usage']:.1f}%")

# Monitor event processing
event_metrics = await event_monitor.get_event_metrics(10)  # Last 10 minutes
if event_metrics['error_rate'] > 0.05:  # More than 5% errors
    await send_alert(f"High error rate: {event_metrics['error_rate']:.1%}")
```

## Metrics Export

### Prometheus Integration

```python
# Export metrics in Prometheus format
def export_prometheus_metrics():
    # Worker performance metrics
    for worker_name in worker_monitor.get_tracked_workers():
        perf = await worker_monitor.get_worker_performance(worker_name)
        prometheus_gauge(f"worker_success_rate", perf['success_rate'], labels={"worker": worker_name})
        prometheus_histogram(f"worker_duration_ms", perf['avg_duration_ms'], labels={"worker": worker_name})

    # Event metrics
    event_metrics = await event_monitor.get_event_metrics()
    prometheus_gauge("event_throughput", event_metrics['throughput_per_minute'])
    prometheus_gauge("event_error_rate", event_metrics['error_rate'])
```

### Custom Metrics Dashboard

```python
async def generate_dashboard_data():
    """Generate data for monitoring dashboard."""
    return {
        "system": await metrics_collector.get_system_metrics(60),
        "events": await event_monitor.get_event_metrics(60),
        "workers": {
            worker: await worker_monitor.get_worker_performance(worker)
            for worker in worker_monitor.get_tracked_workers()
        },
        "health": await worker_monitor.get_all_workers_health(),
        "timestamp": datetime.utcnow().isoformat()
    }
```

## Best Practices

### Monitoring Strategy

1. **Monitor at multiple levels** - System, framework, application
2. **Set appropriate retention** - Balance storage vs. history needs
3. **Use structured logging** - Enable automated analysis
4. **Alert on trends** - Not just current values

### Performance Optimization

1. **Batch monitoring data** - Reduce overhead
2. **Use appropriate collection intervals** - Balance accuracy vs. performance
3. **Clean up old data** - Prevent unbounded growth
4. **Monitor the monitors** - Ensure monitoring systems are healthy

### Troubleshooting

1. **Use correlation IDs** - Track requests across components
2. **Capture full context** - Include relevant metadata
3. **Monitor error patterns** - Identify systemic issues
4. **Track performance trends** - Detect degradation early