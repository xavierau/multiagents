# Monitoring Demonstration Example

**File**: `examples/monitoring_example.py`

This example provides a comprehensive demonstration of the MultiAgents Framework's monitoring capabilities, showing event tracking, worker performance monitoring, error handling, and system metrics collection.

## Purpose

Learn monitoring and observability features:
- Event lifecycle tracking
- Worker performance monitoring  
- Error pattern detection
- System metrics collection
- Custom monitoring configuration
- Real-time monitoring dashboards

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                    MONITORING DEMONSTRATION                        │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐ │
│  │   Test Data     │    │   Test Workers  │    │ Test Workflows  │ │
│  │                 │    │                 │    │                 │ │
│  │ • Success cases │    │ • Fast workers  │    │ • Simple flow   │ │
│  │ • Failure cases │    │ • Slow workers  │    │ • Complex flow  │ │
│  │ • Edge cases    │    │ • Error workers │    │ • Error flow    │ │
│  │ • Load patterns │    │ • CPU intensive │    │ • Load test     │ │
│  └─────────────────┘    └─────────────────┘    └─────────────────┘ │
│           │                       │                       │         │
│           └───────────────────────┼───────────────────────┘         │
│                                   │                                 │
│                          ┌─────────────────┐                       │
│                          │ MONITORING CORE │                       │
│                          └─────────────────┘                       │
│                                   │                                 │
│           ┌───────────────────────┼───────────────────────┐         │
│           │                       │                       │         │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐ │
│  │ Event Monitor   │    │ Worker Monitor  │    │Metrics Collector│ │
│  │                 │    │                 │    │                 │ │
│  │ • Event traces  │    │ • Performance   │    │ • System stats  │ │
│  │ • Latency       │    │ • Success rates │    │ • Resource use  │ │
│  │ • Throughput    │    │ • Error patterns│    │ • Trends        │ │
│  │ • Error rates   │    │ • Health status │    │ • Alerts        │ │
│  └─────────────────┘    └─────────────────┘    └─────────────────┘ │
│           │                       │                       │         │
│           └───────────────────────┼───────────────────────┘         │
│                                   │                                 │
│                          ┌─────────────────┐                       │
│                          │ OUTPUT FORMATS  │                       │
│                          │                 │                       │
│                          │ • Console logs  │                       │
│                          │ • JSON logs     │                       │
│                          │ • Metrics       │                       │
│                          │ • Health status │                       │
│                          │ • Reports       │                       │
│                          └─────────────────┘                       │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

## Key Components

### Test Workers for Monitoring

#### 1. Fast Processing Worker
```python
@worker("fast_processor")
async def fast_processor_worker(context):
    """Worker that completes quickly - demonstrates normal performance."""
    data = context.get("data", "")
    
    # Quick processing (10-50ms)
    await asyncio.sleep(random.uniform(0.01, 0.05))
    
    return {
        "processed": data.upper(),
        "processing_time": "fast",
        "worker_type": "fast_processor"
    }
```

#### 2. Slow Processing Worker
```python
@worker("slow_processor") 
async def slow_processor_worker(context):
    """Worker that takes longer - demonstrates performance monitoring."""
    data = context.get("data", "")
    
    # Slower processing (500ms-2s)
    processing_time = random.uniform(0.5, 2.0)
    await asyncio.sleep(processing_time)
    
    return {
        "processed": data.lower(),
        "processing_time": f"{processing_time:.2f}s",
        "worker_type": "slow_processor"
    }
```

#### 3. Intermittently Failing Worker
```python
@worker("flaky_processor")
async def flaky_processor_worker(context):
    """Worker that fails randomly - demonstrates error monitoring."""
    data = context.get("data", "")
    
    # 30% chance of failure
    if random.random() < 0.3:
        error_types = [
            "NetworkError: Connection timeout",
            "ValidationError: Invalid input format", 
            "ServiceUnavailable: External service down",
            "RateLimitError: Too many requests"
        ]
        raise Exception(random.choice(error_types))
    
    # Variable processing time
    await asyncio.sleep(random.uniform(0.1, 0.8))
    
    return {
        "processed": data.title(),
        "success": True,
        "worker_type": "flaky_processor"
    }
```

#### 4. Resource Intensive Worker
```python
@worker("cpu_intensive")
async def cpu_intensive_worker(context):
    """CPU-intensive worker - demonstrates resource monitoring."""
    data = context.get("data", "")
    complexity = context.get("complexity", 1000)
    
    # CPU-intensive calculation in thread pool
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(
        None,
        cpu_bound_calculation,
        data,
        complexity
    )
    
    return {
        "calculation_result": result,
        "complexity": complexity,
        "worker_type": "cpu_intensive"
    }

def cpu_bound_calculation(data: str, complexity: int) -> dict:
    """CPU-bound calculation for monitoring resource usage."""
    # Simulate complex computation
    total = 0
    for i in range(complexity):
        total += hash(f"{data}-{i}") % 1000
    
    return {
        "hash_sum": total,
        "iterations": complexity,
        "computational_load": "high"
    }
```

### Test Workflows

#### 1. Simple Monitoring Workflow
```python
def create_simple_monitoring_workflow():
    """Simple linear workflow for basic monitoring demonstration."""
    return (WorkflowBuilder("simple_monitoring")
        .add_step("fast_step", "fast_processor")
        .add_step("slow_step", "slow_processor") 
        .add_step("flaky_step", "flaky_processor")
        .build())
```

#### 2. Parallel Processing Workflow
```python
def create_parallel_monitoring_workflow():
    """Parallel workflow for concurrent execution monitoring."""
    return (WorkflowBuilder("parallel_monitoring")
        .add_step("prepare", "fast_processor")
        .add_parallel_steps([
            {"name": "process_a", "worker_name": "fast_processor"},
            {"name": "process_b", "worker_name": "slow_processor"},
            {"name": "process_c", "worker_name": "flaky_processor"},
            {"name": "process_d", "worker_name": "cpu_intensive"}
        ])
        .add_step("combine", "fast_processor")
        .build())
```

#### 3. Error-Prone Workflow
```python
def create_error_monitoring_workflow():
    """Workflow designed to fail for error monitoring demonstration."""
    return (WorkflowBuilder("error_monitoring")
        .add_step("validate", "fast_processor")
        .add_step("risky_process", "flaky_processor")  # Will likely fail
        .add_step("cleanup", "fast_processor")
        .build())
```

## Monitoring Configuration

### Custom Configuration File
```yaml
# examples/monitoring_config.yaml
logging:
  default_logger: "composite"
  level: "DEBUG"  # Verbose logging for demo
  file_path: "./logs/monitoring_demo.log"
  max_file_size_mb: 100
  backup_count: 3
  json_format: true

event_monitoring:
  enabled: true
  trace_retention_hours: 2
  cleanup_interval_minutes: 30
  track_payload_size: true
  detailed_timing: true

worker_monitoring:
  enabled: true
  health_check_interval_seconds: 10
  performance_window_minutes: 30
  alert_on_high_error_rate: true
  error_rate_threshold: 0.2  # Alert if >20% errors
  slow_execution_threshold_ms: 1000

metrics_collection:
  enabled: true
  collection_interval_seconds: 15
  retention_hours: 4
  include_system_metrics: true
  custom_metrics:
    - name: "workflow_completion_rate"
      type: "gauge"
    - name: "average_step_duration"
      type: "histogram"
```

### Programmatic Configuration
```python
def create_custom_monitoring_config():
    """Create monitoring configuration programmatically."""
    return MonitoringConfig({
        "logging": {
            "default_logger": "composite",
            "level": "INFO",
            "file_path": "./logs/custom_monitoring.log"
        },
        "event_monitoring": {
            "enabled": True,
            "trace_retention_hours": 6,
            "detailed_event_tracking": True
        },
        "worker_monitoring": {
            "enabled": True,
            "performance_alerts": True,
            "health_check_interval_seconds": 5
        }
    })
```

## Monitoring Demonstrations

### 1. Event Lifecycle Tracking

```python
async def demonstrate_event_tracking():
    """Show detailed event lifecycle tracking."""
    
    print("\n🔍 EVENT LIFECYCLE TRACKING DEMO")
    print("=" * 50)
    
    # Execute a simple workflow
    transaction_id = await orchestrator.execute_workflow(
        "simple_monitoring",
        {"data": "monitoring_test"}
    )
    
    # Monitor in real-time
    while True:
        status = await orchestrator.get_status(transaction_id)
        
        # Get real-time event metrics
        event_metrics = await event_monitor.get_event_metrics(time_window_minutes=1)
        
        print(f"State: {status['state']} | "
              f"Events: {event_metrics['total_events']} | "
              f"Latency: {event_metrics.get('avg_latency_ms', 0):.1f}ms")
        
        if status['state'] in ['completed', 'failed']:
            break
        
        await asyncio.sleep(0.5)
    
    # Show detailed event trace
    transaction_trace = await event_monitor.get_transaction_trace(transaction_id)
    
    print("\n📊 Event Trace:")
    for event in transaction_trace:
        print(f"  {event['timestamp']}: {event['event_type']} -> {event['stage']}")
```

### 2. Worker Performance Analysis

```python
async def demonstrate_worker_performance():
    """Show worker performance monitoring and analysis."""
    
    print("\n⚡ WORKER PERFORMANCE DEMO")
    print("=" * 50)
    
    # Execute multiple workflows to generate performance data
    workflows = [
        ("simple_monitoring", {"data": f"test_{i}"})
        for i in range(10)
    ]
    
    # Execute workflows concurrently
    tasks = [
        orchestrator.execute_workflow(workflow_name, context)
        for workflow_name, context in workflows
    ]
    
    transaction_ids = await asyncio.gather(*tasks)
    
    # Wait for all to complete
    await wait_for_workflows_completion(transaction_ids)
    
    # Analyze worker performance
    print("\n📈 Worker Performance Analysis:")
    
    for worker_name in ['fast_processor', 'slow_processor', 'flaky_processor']:
        perf = await worker_monitor.get_worker_performance(worker_name, time_window_minutes=5)
        
        print(f"\n{worker_name}:")
        print(f"  Executions: {perf['total_executions']}")
        print(f"  Success Rate: {perf['success_rate']:.1f}%")
        print(f"  Avg Duration: {perf['avg_duration_ms']:.1f}ms")
        print(f"  P95 Duration: {perf['p95_duration_ms']:.1f}ms")
        print(f"  Error Rate: {perf['error_rate']:.1f}%")
        
        # Health status
        health = await worker_monitor.check_worker_health(worker_name)
        print(f"  Health: {health['status']}")
        if health['issues']:
            print(f"  Issues: {', '.join(health['issues'])}")
```

### 3. Error Pattern Detection

```python
async def demonstrate_error_monitoring():
    """Show error detection and pattern analysis."""
    
    print("\n🚨 ERROR MONITORING DEMO")
    print("=" * 50)
    
    # Execute error-prone workflows
    error_workflows = []
    for i in range(20):
        try:
            transaction_id = await orchestrator.execute_workflow(
                "error_monitoring", 
                {"data": f"error_test_{i}"}
            )
            error_workflows.append(transaction_id)
        except Exception as e:
            print(f"Workflow {i} failed to start: {e}")
    
    # Wait for completion
    await wait_for_workflows_completion(error_workflows)
    
    # Analyze error patterns
    print("\n📊 Error Analysis:")
    
    # Overall error metrics
    error_metrics = await event_monitor.get_event_metrics(time_window_minutes=5)
    print(f"Total Events: {error_metrics['total_events']}")
    print(f"Error Rate: {error_metrics['error_rate']:.1f}%")
    print(f"Success Rate: {error_metrics['success_rate']:.1f}%")
    
    # Worker-specific error analysis
    flaky_perf = await worker_monitor.get_worker_performance("flaky_processor", time_window_minutes=5)
    print(f"\nFlaky Processor:")
    print(f"  Error Rate: {flaky_perf['error_rate']:.1f}%")
    print(f"  Failed Executions: {flaky_perf.get('failed_executions', 0)}")
    
    # Error categorization (if available)
    error_patterns = await event_monitor.get_error_patterns(time_window_minutes=5)
    if error_patterns:
        print(f"\nError Patterns:")
        for pattern in error_patterns:
            print(f"  {pattern['error_type']}: {pattern['count']} occurrences")
```

### 4. System Resource Monitoring

```python
async def demonstrate_system_monitoring():
    """Show system resource monitoring during load."""
    
    print("\n💻 SYSTEM RESOURCE MONITORING DEMO")  
    print("=" * 50)
    
    # Baseline metrics
    baseline_metrics = await metrics_collector.get_system_metrics(time_window_minutes=1)
    print(f"Baseline CPU: {baseline_metrics.get('avg_cpu_usage', 0):.1f}%")
    print(f"Baseline Memory: {baseline_metrics.get('avg_memory_usage', 0):.1f}%")
    
    # Generate CPU load with intensive workflows
    print("\n🔥 Generating CPU load...")
    
    cpu_workflows = []
    for i in range(5):
        transaction_id = await orchestrator.execute_workflow(
            "cpu_intensive_monitoring",
            {"data": f"cpu_test_{i}", "complexity": 10000}
        )
        cpu_workflows.append(transaction_id)
    
    # Monitor system resources during load
    start_time = time.time()
    while time.time() - start_time < 30:  # Monitor for 30 seconds
        current_metrics = await metrics_collector.collect_system_metrics()
        
        print(f"CPU: {current_metrics.get('cpu_usage_percent', 0):.1f}% | "
              f"Memory: {current_metrics.get('memory_usage_percent', 0):.1f}% | "
              f"Active Connections: {current_metrics.get('active_connections', 0)}")
        
        await asyncio.sleep(2)
    
    # Wait for workflows to complete
    await wait_for_workflows_completion(cpu_workflows)
    
    # Final metrics analysis
    final_metrics = await metrics_collector.get_system_metrics(time_window_minutes=2)
    print(f"\nPeak CPU: {final_metrics.get('peak_cpu_usage', 0):.1f}%")
    print(f"Peak Memory: {final_metrics.get('peak_memory_usage', 0):.1f}%")
    print(f"Avg Load: {final_metrics.get('avg_system_load', 0):.2f}")
```

## Real-time Monitoring Dashboard

### Console Dashboard
```python
async def run_monitoring_dashboard():
    """Run a real-time monitoring dashboard in the console."""
    
    print("\n📊 REAL-TIME MONITORING DASHBOARD")
    print("=" * 60)
    
    dashboard_start = time.time()
    
    while time.time() - dashboard_start < 120:  # Run for 2 minutes
        # Clear screen (works on most terminals)
        os.system('clear' if os.name == 'posix' else 'cls')
        
        print("📊 MULTIAGENTS MONITORING DASHBOARD")
        print("=" * 60)
        print(f"Runtime: {int(time.time() - dashboard_start)}s")
        
        # Event metrics
        event_metrics = await event_monitor.get_event_metrics(time_window_minutes=1)
        print(f"\n📨 EVENTS (Last 1 min)")
        print(f"  Total: {event_metrics['total_events']}")
        print(f"  Success Rate: {event_metrics['success_rate']:.1f}%")
        print(f"  Throughput: {event_metrics['throughput_per_minute']:.1f}/min")
        print(f"  Avg Latency: {event_metrics.get('avg_latency_ms', 0):.1f}ms")
        
        # Worker performance
        worker_summary = await worker_monitor.get_worker_performance_summary(time_window_minutes=1)
        print(f"\n👷 WORKERS (Last 1 min)")
        print(f"  Commands: {worker_summary['aggregated_metrics']['total_commands']}")
        print(f"  Success Rate: {worker_summary['aggregated_metrics']['average_success_rate']:.1f}%")
        print(f"  Avg Duration: {worker_summary['aggregated_metrics']['average_duration_ms']:.1f}ms")
        
        # Individual worker status
        for worker_name in ['fast_processor', 'slow_processor', 'flaky_processor']:
            health = await worker_monitor.check_worker_health(worker_name)
            status_icon = "🟢" if health['status'] == 'healthy' else "🟡" if health['status'] == 'degraded' else "🔴"
            print(f"  {status_icon} {worker_name}: {health['status']}")
        
        # System resources
        system_metrics = await metrics_collector.collect_system_metrics()
        print(f"\n💻 SYSTEM")
        print(f"  CPU: {system_metrics.get('cpu_usage_percent', 0):.1f}%")
        print(f"  Memory: {system_metrics.get('memory_usage_percent', 0):.1f}%")
        print(f"  Redis Connections: {system_metrics.get('active_connections', 0)}")
        
        # Active workflows
        print(f"\n🔄 ACTIVE WORKFLOWS")
        # Add code to track active workflows
        
        print(f"\nRefreshing in 3s... (Ctrl+C to exit)")
        await asyncio.sleep(3)
```

## Load Testing Integration

### Sustained Load Test
```python
async def run_load_test():
    """Run sustained load test with monitoring."""
    
    print("\n🏋️ LOAD TEST WITH MONITORING")
    print("=" * 50)
    
    load_duration = 60  # 1 minute load test
    concurrent_workflows = 5
    requests_per_second = 2
    
    load_start = time.time()
    total_requests = 0
    
    async def continuous_load():
        """Generate continuous load."""
        nonlocal total_requests
        
        while time.time() - load_start < load_duration:
            # Start multiple workflows
            tasks = []
            for i in range(concurrent_workflows):
                workflow_type = random.choice([
                    "simple_monitoring",
                    "parallel_monitoring", 
                    "error_monitoring"
                ])
                
                task = orchestrator.execute_workflow(
                    workflow_type,
                    {"data": f"load_test_{total_requests}_{i}"}
                )
                tasks.append(task)
            
            await asyncio.gather(*tasks, return_exceptions=True)
            total_requests += concurrent_workflows
            
            # Control request rate
            await asyncio.sleep(1.0 / requests_per_second)
    
    # Run load test with monitoring
    load_task = asyncio.create_task(continuous_load())
    
    # Monitor during load test
    while not load_task.done():
        current_metrics = await event_monitor.get_event_metrics(time_window_minutes=1)
        print(f"Requests: {total_requests} | "
              f"Events: {current_metrics['total_events']} | "
              f"Success: {current_metrics['success_rate']:.1f}% | "
              f"Latency: {current_metrics.get('avg_latency_ms', 0):.1f}ms")
        
        await asyncio.sleep(5)
    
    await load_task
    
    # Final load test analysis
    print(f"\n📊 Load Test Results:")
    print(f"Total Requests: {total_requests}")
    print(f"Duration: {load_duration}s")
    print(f"Average RPS: {total_requests / load_duration:.1f}")
    
    final_metrics = await event_monitor.get_event_metrics(time_window_minutes=2)
    print(f"Final Success Rate: {final_metrics['success_rate']:.1f}%")
    print(f"Peak Throughput: {final_metrics.get('peak_throughput', 0):.1f}/min")
```

## Custom Metrics and Alerts

### Custom Metrics Collection
```python
class CustomMetricsCollector:
    """Custom metrics collector for business-specific monitoring."""
    
    def __init__(self, logger):
        self.logger = logger
        self.business_metrics = {}
    
    async def track_order_value(self, order_value: float):
        """Track business metric: order values."""
        current_hour = datetime.utcnow().strftime("%Y-%m-%d-%H")
        
        if current_hour not in self.business_metrics:
            self.business_metrics[current_hour] = {
                "total_orders": 0,
                "total_value": 0.0,
                "max_value": 0.0,
                "min_value": float('inf')
            }
        
        metrics = self.business_metrics[current_hour]
        metrics["total_orders"] += 1
        metrics["total_value"] += order_value
        metrics["max_value"] = max(metrics["max_value"], order_value)
        metrics["min_value"] = min(metrics["min_value"], order_value)
        
        await self.logger.info("Business metric recorded",
                              metric_type="order_value",
                              value=order_value,
                              hour=current_hour)
    
    async def get_business_metrics(self, hours: int = 1) -> dict:
        """Get business metrics for the last N hours."""
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=hours)
        
        relevant_metrics = {}
        for hour_key, metrics in self.business_metrics.items():
            hour_time = datetime.strptime(hour_key, "%Y-%m-%d-%H")
            if start_time <= hour_time <= end_time:
                relevant_metrics[hour_key] = metrics
        
        return relevant_metrics
```

### Alert System
```python
class MonitoringAlerts:
    """Alert system for monitoring thresholds."""
    
    def __init__(self, event_monitor, worker_monitor, logger):
        self.event_monitor = event_monitor
        self.worker_monitor = worker_monitor  
        self.logger = logger
        self.alert_history = []
    
    async def check_alerts(self):
        """Check all alert conditions."""
        alerts = []
        
        # Check error rate alerts
        event_metrics = await self.event_monitor.get_event_metrics(time_window_minutes=5)
        if event_metrics['error_rate'] > 0.1:  # >10% error rate
            alerts.append({
                "type": "high_error_rate",
                "severity": "warning",
                "message": f"Error rate {event_metrics['error_rate']:.1%} exceeds threshold",
                "value": event_metrics['error_rate'],
                "threshold": 0.1
            })
        
        # Check latency alerts
        if event_metrics.get('avg_latency_ms', 0) > 5000:  # >5s average latency
            alerts.append({
                "type": "high_latency",
                "severity": "warning", 
                "message": f"Average latency {event_metrics['avg_latency_ms']:.0f}ms exceeds threshold",
                "value": event_metrics['avg_latency_ms'],
                "threshold": 5000
            })
        
        # Check worker health alerts
        worker_health = await self.worker_monitor.get_all_workers_health()
        for worker_name, health in worker_health.items():
            if health['status'] == 'failed':
                alerts.append({
                    "type": "worker_failed",
                    "severity": "critical",
                    "message": f"Worker {worker_name} has failed",
                    "worker": worker_name,
                    "issues": health.get('issues', [])
                })
        
        # Process alerts
        for alert in alerts:
            await self.handle_alert(alert)
        
        return alerts
    
    async def handle_alert(self, alert):
        """Handle a triggered alert."""
        # Log alert
        await self.logger.warning("Alert triggered",
                                 alert_type=alert["type"],
                                 severity=alert["severity"],
                                 message=alert["message"])
        
        # Store in history
        alert["timestamp"] = datetime.utcnow().isoformat()
        self.alert_history.append(alert)
        
        # Send notifications (implement based on your needs)
        if alert["severity"] == "critical":
            await self.send_critical_notification(alert)
    
    async def send_critical_notification(self, alert):
        """Send critical alert notification."""
        # Implement notification logic (email, Slack, PagerDuty, etc.)
        print(f"🚨 CRITICAL ALERT: {alert['message']}")
```

## Production Monitoring Setup

### Prometheus Integration
```python
async def export_prometheus_metrics():
    """Export metrics in Prometheus format."""
    
    # Event metrics
    event_metrics = await event_monitor.get_event_metrics(time_window_minutes=5)
    prometheus_metrics = [
        f"multiagents_events_total {event_metrics['total_events']}",
        f"multiagents_success_rate {event_metrics['success_rate'] / 100}",
        f"multiagents_avg_latency_seconds {event_metrics.get('avg_latency_ms', 0) / 1000}",
        f"multiagents_error_rate {event_metrics['error_rate']}",
    ]
    
    # Worker metrics
    for worker_name in await worker_monitor.get_tracked_workers():
        perf = await worker_monitor.get_worker_performance(worker_name, time_window_minutes=5)
        prometheus_metrics.extend([
            f'multiagents_worker_executions_total{{worker="{worker_name}"}} {perf["total_executions"]}',
            f'multiagents_worker_success_rate{{worker="{worker_name}"}} {perf["success_rate"] / 100}',
            f'multiagents_worker_avg_duration_seconds{{worker="{worker_name}"}} {perf["avg_duration_ms"] / 1000}',
        ])
    
    return "\n".join(prometheus_metrics)
```

This comprehensive monitoring example demonstrates how to implement production-ready observability for distributed workflow systems using the MultiAgents Framework!