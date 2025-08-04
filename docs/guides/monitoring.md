# Monitoring & Observability Guide

Comprehensive guide to implementing production-ready monitoring and observability for the MultiAgents Framework.

## Table of Contents

- [Monitoring Overview](#monitoring-overview)
- [Configuration](#configuration)
- [Event Monitoring](#event-monitoring)
- [Worker Performance Monitoring](#worker-performance-monitoring)
- [System Metrics](#system-metrics)
- [Custom Monitoring](#custom-monitoring)
- [Alerting](#alerting)
- [Integration with External Systems](#integration-with-external-systems)
- [Best Practices](#best-practices)

## Monitoring Overview

The MultiAgents Framework provides comprehensive observability through multiple monitoring layers:

```
┌─────────────────────────────────────────────────────────────────────┐
│                    MONITORING ARCHITECTURE                         │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐ │
│  │  Application    │    │   Framework     │    │    System       │ │
│  │   Metrics       │    │    Metrics      │    │   Metrics       │ │
│  │                 │    │                 │    │                 │ │
│  │ • Business KPIs │    │ • Event flow    │    │ • CPU/Memory    │ │
│  │ • User actions  │    │ • Worker perf   │    │ • Network I/O   │ │
│  │ • Custom events │    │ • Error rates   │    │ • Disk usage    │ │
│  └─────────────────┘    └─────────────────┘    └─────────────────┘ │
│           │                       │                       │         │
│           └───────────────────────┼───────────────────────┘         │
│                                   │                                 │
│                    ┌─────────────────┐                              │
│                    │ MONITORING CORE │                              │
│                    │                 │                              │
│                    │ • EventMonitor  │                              │
│                    │ • WorkerMonitor │                              │
│                    │ • MetricsCollect│                              │
│                    │ • Structured Log│                              │
│                    └─────────────────┘                              │
│                                   │                                 │
│           ┌───────────────────────┼───────────────────────┐         │
│           │                       │                       │         │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐ │
│  │    Storage      │    │   Analytics     │    │    Alerting     │ │
│  │                 │    │                 │    │                 │ │
│  │ • Time series   │    │ • Dashboards    │    │ • Thresholds    │ │
│  │ • Log files     │    │ • Reports       │    │ • Notifications │ │
│  │ • Event traces  │    │ • Trends        │    │ • Escalation    │ │
│  └─────────────────┘    └─────────────────┘    └─────────────────┘ │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### Core Monitoring Components

1. **EventMonitor**: Tracks event lifecycle and performance
2. **WorkerMonitor**: Monitors worker performance and health
3. **MetricsCollector**: Collects system and custom metrics
4. **Structured Logging**: Provides detailed, queryable logs

## Configuration

### Basic Configuration

Create a monitoring configuration file:

```yaml
# monitoring.yaml
logging:
  default_logger: "composite"
  level: "INFO"
  file_path: "./logs/multiagents.log"
  max_file_size_mb: 100
  backup_count: 5
  json_format: true
  include_caller_info: true

event_monitoring:
  enabled: true
  trace_retention_hours: 24
  cleanup_interval_minutes: 60
  track_payload_size: true
  detailed_timing: true
  max_traces_per_transaction: 1000

worker_monitoring:
  enabled: true
  health_check_interval_seconds: 30
  performance_window_minutes: 60
  alert_on_high_error_rate: true
  error_rate_threshold: 0.1
  slow_execution_threshold_ms: 5000
  track_resource_usage: true

metrics_collection:
  enabled: true
  collection_interval_seconds: 60
  retention_hours: 168  # 7 days
  include_system_metrics: true
  custom_metrics_enabled: true
  export_prometheus: true
  export_port: 9090
```

### Programmatic Configuration

```python
from multiagents.monitoring import MonitoringConfig

# Create configuration from dictionary
config = MonitoringConfig({
    "logging": {
        "default_logger": "file",
        "level": "DEBUG",
        "file_path": "./logs/debug.log"
    },
    "event_monitoring": {
        "enabled": True,
        "detailed_timing": True
    },
    "worker_monitoring": {
        "enabled": True,
        "alert_on_high_error_rate": True
    }
})

# Or load from file
config = MonitoringConfig.from_file("monitoring.yaml")

# Create logger
logger = config.create_logger()
```

### Environment-Specific Configuration

```python
import os

def create_environment_config():
    """Create monitoring config based on environment."""
    
    env = os.getenv("ENVIRONMENT", "development")
    
    if env == "production":
        return MonitoringConfig({
            "logging": {
                "level": "INFO",
                "default_logger": "composite",
                "json_format": True
            },
            "event_monitoring": {
                "trace_retention_hours": 48,
                "detailed_timing": True
            },
            "worker_monitoring": {
                "health_check_interval_seconds": 15,
                "error_rate_threshold": 0.05  # Stricter in prod
            }
        })
    
    elif env == "staging":
        return MonitoringConfig({
            "logging": {
                "level": "DEBUG",
                "default_logger": "composite"
            },
            "event_monitoring": {
                "trace_retention_hours": 12
            }
        })
    
    else:  # development
        return MonitoringConfig({
            "logging": {
                "level": "DEBUG",
                "default_logger": "console"
            },
            "event_monitoring": {
                "trace_retention_hours": 2
            }
        })
```

## Event Monitoring

### Event Lifecycle Tracking

The EventMonitor tracks events through their complete lifecycle:

```python
from multiagents.monitoring import EventMonitor

# Create event monitor
event_monitor = EventMonitor(
    logger=logger,
    trace_retention_hours=24,
    cleanup_interval_minutes=60
)

# Events are automatically tracked when integrated with framework
event_bus = RedisEventBus(event_monitor=event_monitor)

# Manual event tracking (if needed)
await event_monitor.track_event_lifecycle(command_event, "published")
await event_monitor.track_event_lifecycle(command_event, "received")
await event_monitor.track_event_lifecycle(result_event, "completed")
```

### Event Metrics Analysis

```python
# Get comprehensive event metrics
event_metrics = await event_monitor.get_event_metrics(time_window_minutes=60)

print(f"Event Summary (Last Hour):")
print(f"  Total Events: {event_metrics['total_events']}")
print(f"  Success Rate: {event_metrics['success_rate']:.1f}%")
print(f"  Error Rate: {event_metrics['error_rate']:.1f}%")
print(f"  Average Latency: {event_metrics['avg_latency_ms']:.1f}ms")
print(f"  P95 Latency: {event_metrics['p95_latency_ms']:.1f}ms")
print(f"  Throughput: {event_metrics['throughput_per_minute']:.1f} events/min")

# Get event type breakdown
event_type_metrics = await event_monitor.get_event_type_metrics("CommandEvent")
print(f"Command Events: {event_type_metrics['count']} ({event_type_metrics['percentage']:.1f}%)")
```

### Transaction Tracing

```python
# Get complete trace for a transaction
transaction_trace = await event_monitor.get_transaction_trace("TX-123")

print("Transaction Trace:")
for event in transaction_trace:
    print(f"  {event['timestamp']}: {event['event_type']} -> {event['stage']}")
    if event.get('duration_ms'):
        print(f"    Duration: {event['duration_ms']:.1f}ms")
    if event.get('error'):
        print(f"    Error: {event['error']}")
```

### Custom Event Tracking

```python
# Track custom business events
async def track_business_event(event_monitor, event_name: str, data: dict):
    """Track custom business events."""
    
    custom_event = {
        "event_name": event_name,
        "timestamp": datetime.utcnow().isoformat(),
        "data": data,
        "correlation_id": data.get("correlation_id"),
        "transaction_id": data.get("transaction_id")
    }
    
    await event_monitor.track_custom_event(custom_event)

# Usage
await track_business_event(event_monitor, "order_completed", {
    "order_id": "ORDER-123",
    "customer_id": "CUST-456",
    "total_value": 299.99,
    "transaction_id": "TX-789"
})
```

## Worker Performance Monitoring

### Worker Performance Tracking

```python
from multiagents.monitoring import WorkerMonitor

# Create worker monitor
worker_monitor = WorkerMonitor(
    logger=logger,
    health_check_interval_seconds=30,
    performance_window_minutes=60
)

# Integrate with WorkerManager
worker_manager = WorkerManager(
    event_bus,
    worker_monitor=worker_monitor,
    logger=logger
)

# Manual performance tracking (if needed)
start_time = time.time()
try:
    result = await worker_function(context)
    execution_time = (time.time() - start_time) * 1000
    await worker_monitor.track_worker_execution(
        worker_name="my_worker",
        execution_time_ms=execution_time,
        success=True
    )
except Exception as e:
    execution_time = (time.time() - start_time) * 1000
    await worker_monitor.track_worker_execution(
        worker_name="my_worker",
        execution_time_ms=execution_time,
        success=False,
        error=str(e)
    )
```

### Performance Analysis

```python
# Get individual worker performance
worker_perf = await worker_monitor.get_worker_performance("payment_processor")

print(f"Payment Processor Performance:")
print(f"  Total Executions: {worker_perf['total_executions']}")
print(f"  Success Rate: {worker_perf['success_rate']:.1f}%")
print(f"  Average Duration: {worker_perf['avg_duration_ms']:.1f}ms")
print(f"  P95 Duration: {worker_perf['p95_duration_ms']:.1f}ms")
print(f"  Error Rate: {worker_perf['error_rate']:.1f}%")
print(f"  Last Execution: {worker_perf['last_execution']}")

# Get aggregated performance summary
summary = await worker_monitor.get_worker_performance_summary()

print(f"Overall Worker Performance:")
print(f"  Total Workers: {summary['total_workers']}")
print(f"  Total Commands: {summary['aggregated_metrics']['total_commands']}")
print(f"  Average Success Rate: {summary['aggregated_metrics']['average_success_rate']:.1f}%")
print(f"  Average Duration: {summary['aggregated_metrics']['average_duration_ms']:.1f}ms")

# Performance by worker
for worker_name, metrics in summary['worker_metrics'].items():
    print(f"  {worker_name}: {metrics['success_rate']:.1f}% success, {metrics['avg_duration_ms']:.1f}ms avg")
```

### Health Monitoring

```python
# Check individual worker health
health = await worker_monitor.check_worker_health("inventory_service")

print(f"Inventory Service Health:")
print(f"  Status: {health['status']}")  # healthy, degraded, failed
print(f"  Last Seen: {health['last_seen']}")
print(f"  Recent Error Rate: {health['recent_error_rate']:.1f}%")

if health['issues']:
    print(f"  Issues:")
    for issue in health['issues']:
        print(f"    - {issue}")

# Get health for all workers
all_health = await worker_monitor.get_all_workers_health()

for worker_name, health in all_health.items():
    status_icon = "🟢" if health['status'] == 'healthy' else "🟡" if health['status'] == 'degraded' else "🔴"
    print(f"  {status_icon} {worker_name}: {health['status']}")
```

## System Metrics

### System Resource Monitoring

```python
from multiagents.monitoring import MetricsCollector

# Create metrics collector
metrics_collector = MetricsCollector(
    logger=logger,
    collection_interval_seconds=60,
    retention_hours=24
)

# Collect current system metrics
current_metrics = await metrics_collector.collect_system_metrics()

print(f"Current System Metrics:")
print(f"  CPU Usage: {current_metrics['cpu_usage_percent']:.1f}%")
print(f"  Memory Usage: {current_metrics['memory_usage_percent']:.1f}%")
print(f"  Disk Usage: {current_metrics['disk_usage_percent']:.1f}%")
print(f"  Active Connections: {current_metrics['active_connections']}")
print(f"  Event Queue Size: {current_metrics['event_queue_size']}")

# Get historical metrics
historical_metrics = await metrics_collector.get_system_metrics(time_window_minutes=60)

print(f"System Metrics (Last Hour):")
print(f"  Average CPU: {historical_metrics['avg_cpu_usage']:.1f}%")
print(f"  Peak CPU: {historical_metrics['peak_cpu_usage']:.1f}%")
print(f"  Average Memory: {historical_metrics['avg_memory_usage']:.1f}%")
print(f"  Peak Memory: {historical_metrics['peak_memory_usage']:.1f}%")
```

### Custom Metrics Collection

```python
class CustomMetricsCollector:
    """Custom metrics collector for business-specific monitoring."""
    
    def __init__(self, logger):
        self.logger = logger
        self.metrics_store = {}
    
    async def record_metric(self, metric_name: str, value: float, tags: dict = None):
        """Record a custom metric with tags."""
        
        timestamp = datetime.utcnow()
        metric_key = f"{metric_name}:{hash(str(sorted((tags or {}).items())))}"
        
        if metric_key not in self.metrics_store:
            self.metrics_store[metric_key] = []
        
        self.metrics_store[metric_key].append({
            "timestamp": timestamp,
            "value": value,
            "tags": tags or {}
        })
        
        await self.logger.info("Custom metric recorded",
                              metric_name=metric_name,
                              value=value,
                              tags=tags)
    
    async def get_metric_aggregations(self, metric_name: str, time_window_minutes: int = 60):
        """Get aggregated metrics for the specified time window."""
        
        cutoff_time = datetime.utcnow() - timedelta(minutes=time_window_minutes)
        matching_metrics = []
        
        for key, metrics in self.metrics_store.items():
            if metric_name in key:
                recent_metrics = [m for m in metrics if m["timestamp"] >= cutoff_time]
                matching_metrics.extend(recent_metrics)
        
        if not matching_metrics:
            return {"count": 0, "avg": 0, "min": 0, "max": 0, "sum": 0}
        
        values = [m["value"] for m in matching_metrics]
        
        return {
            "count": len(values),
            "avg": sum(values) / len(values),
            "min": min(values),
            "max": max(values),
            "sum": sum(values),
            "latest": values[-1] if values else 0
        }

# Usage
custom_metrics = CustomMetricsCollector(logger)

# Record business metrics
await custom_metrics.record_metric("order_value", 299.99, {"customer_tier": "premium"})
await custom_metrics.record_metric("order_value", 49.99, {"customer_tier": "standard"})
await custom_metrics.record_metric("processing_time", 1.2, {"worker": "payment_processor"})

# Get aggregations
order_stats = await custom_metrics.get_metric_aggregations("order_value")
print(f"Order Value Stats: avg=${order_stats['avg']:.2f}, total=${order_stats['sum']:.2f}")
```

## Custom Monitoring

### Business Logic Monitoring

```python
class BusinessMetricsMonitor:
    """Monitor business-specific metrics and KPIs."""
    
    def __init__(self, logger, metrics_collector):
        self.logger = logger
        self.metrics_collector = metrics_collector
        self.business_rules = {}
    
    async def track_workflow_completion(self, workflow_id: str, transaction_id: str, 
                                      duration_ms: float, status: str):
        """Track workflow completion metrics."""
        
        await self.metrics_collector.record_metric(
            "workflow_completion",
            1,
            tags={
                "workflow_id": workflow_id,
                "status": status,
                "duration_bucket": self._get_duration_bucket(duration_ms)
            }
        )
        
        await self.metrics_collector.record_metric(
            "workflow_duration",
            duration_ms,
            tags={"workflow_id": workflow_id}
        )
        
        # Business rule checks
        if duration_ms > 30000:  # 30 seconds
            await self.logger.warning("Slow workflow detected",
                                     workflow_id=workflow_id,
                                     transaction_id=transaction_id,
                                     duration_ms=duration_ms)
    
    async def track_error_pattern(self, error_type: str, worker_name: str, 
                                context: dict):
        """Track error patterns for analysis."""
        
        await self.metrics_collector.record_metric(
            "error_occurrence",
            1,
            tags={
                "error_type": error_type,
                "worker_name": worker_name,
                "hour": datetime.utcnow().strftime("%Y-%m-%d-%H")
            }
        )
        
        # Check for error spikes
        recent_errors = await self.metrics_collector.get_metric_aggregations(
            "error_occurrence",
            time_window_minutes=5
        )
        
        if recent_errors["count"] > 10:  # More than 10 errors in 5 minutes
            await self.logger.error("Error spike detected",
                                   error_count=recent_errors["count"],
                                   worker_name=worker_name,
                                   error_type=error_type)
    
    def _get_duration_bucket(self, duration_ms: float) -> str:
        """Categorize duration into buckets for analysis."""
        if duration_ms < 100:
            return "fast"
        elif duration_ms < 1000:
            return "normal"
        elif duration_ms < 5000:
            return "slow"
        else:
            return "very_slow"

# Usage in workflow monitoring
business_monitor = BusinessMetricsMonitor(logger, custom_metrics)

# Track workflow completion
await business_monitor.track_workflow_completion(
    "order_processing",
    "TX-123",
    2500.0,
    "completed"
)

# Track errors
await business_monitor.track_error_pattern(
    "PaymentDeclinedError",
    "payment_processor",
    {"order_id": "ORDER-456"}
)
```

## Alerting

### Alert Configuration

```python
from dataclasses import dataclass
from typing import List, Callable, Any

@dataclass
class AlertRule:
    """Configuration for an alert rule."""
    name: str
    condition: Callable[[dict], bool]
    severity: str  # "info", "warning", "error", "critical"
    cooldown_minutes: int = 15
    description: str = ""

class AlertManager:
    """Manage alerts and notifications."""
    
    def __init__(self, logger):
        self.logger = logger
        self.alert_rules: List[AlertRule] = []
        self.alert_history = {}
        self.notification_handlers = []
    
    def add_alert_rule(self, rule: AlertRule):
        """Add an alert rule."""
        self.alert_rules.append(rule)
    
    def add_notification_handler(self, handler: Callable[[dict], None]):
        """Add a notification handler."""
        self.notification_handlers.append(handler)
    
    async def check_alerts(self, metrics: dict):
        """Check all alert rules against current metrics."""
        
        triggered_alerts = []
        
        for rule in self.alert_rules:
            try:
                if rule.condition(metrics):
                    # Check cooldown
                    last_triggered = self.alert_history.get(rule.name)
                    if last_triggered:
                        time_since = datetime.utcnow() - last_triggered
                        if time_since.total_seconds() < rule.cooldown_minutes * 60:
                            continue  # Still in cooldown
                    
                    # Trigger alert
                    alert = {
                        "rule_name": rule.name,
                        "severity": rule.severity,
                        "description": rule.description,
                        "timestamp": datetime.utcnow().isoformat(),
                        "metrics": metrics
                    }
                    
                    triggered_alerts.append(alert)
                    self.alert_history[rule.name] = datetime.utcnow()
                    
                    # Send notifications
                    for handler in self.notification_handlers:
                        try:
                            await handler(alert)
                        except Exception as e:
                            await self.logger.error("Notification handler failed",
                                                   handler=str(handler),
                                                   error=str(e))
            
            except Exception as e:
                await self.logger.error("Alert rule evaluation failed",
                                       rule_name=rule.name,
                                       error=str(e))
        
        return triggered_alerts

# Define alert rules
alert_manager = AlertManager(logger)

# High error rate alert
alert_manager.add_alert_rule(AlertRule(
    name="high_error_rate",
    condition=lambda metrics: metrics.get("error_rate", 0) > 0.1,
    severity="warning",
    description="Error rate exceeded 10%"
))

# High latency alert
alert_manager.add_alert_rule(AlertRule(
    name="high_latency",
    condition=lambda metrics: metrics.get("avg_latency_ms", 0) > 5000,
    severity="warning",
    description="Average latency exceeded 5 seconds"
))

# Critical system resources alert
alert_manager.add_alert_rule(AlertRule(
    name="critical_cpu_usage",
    condition=lambda metrics: metrics.get("cpu_usage_percent", 0) > 90,
    severity="critical",
    description="CPU usage exceeded 90%"
))

# Worker failure alert
alert_manager.add_alert_rule(AlertRule(
    name="worker_failure",
    condition=lambda metrics: any(
        health.get("status") == "failed" 
        for health in metrics.get("worker_health", {}).values()
    ),
    severity="error",
    description="One or more workers have failed"
))
```

### Notification Handlers

```python
import aiohttp
import smtplib
from email.mime.text import MIMEText

async def slack_notification_handler(alert: dict):
    """Send alert to Slack."""
    
    webhook_url = os.getenv("SLACK_WEBHOOK_URL")
    if not webhook_url:
        return
    
    severity_colors = {
        "info": "#36a64f",
        "warning": "#ff9500", 
        "error": "#ff0000",
        "critical": "#8b0000"
    }
    
    message = {
        "attachments": [{
            "color": severity_colors.get(alert["severity"], "#cccccc"),
            "title": f"🚨 {alert['rule_name']}",
            "text": alert["description"],
            "fields": [
                {"title": "Severity", "value": alert["severity"], "short": True},
                {"title": "Time", "value": alert["timestamp"], "short": True}
            ]
        }]
    }
    
    async with aiohttp.ClientSession() as session:
        await session.post(webhook_url, json=message)

async def email_notification_handler(alert: dict):
    """Send alert via email."""
    
    smtp_server = os.getenv("SMTP_SERVER", "localhost")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    smtp_user = os.getenv("SMTP_USER")
    smtp_password = os.getenv("SMTP_PASSWORD")
    
    from_email = os.getenv("ALERT_FROM_EMAIL", "alerts@company.com")
    to_emails = os.getenv("ALERT_TO_EMAILS", "").split(",")
    
    if not to_emails or not to_emails[0]:
        return
    
    subject = f"[{alert['severity'].upper()}] {alert['rule_name']}"
    body = f"""
    Alert: {alert['rule_name']}
    Severity: {alert['severity']}
    Description: {alert['description']}
    Time: {alert['timestamp']}
    
    Metrics:
    {json.dumps(alert['metrics'], indent=2)}
    """
    
    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = from_email
    msg['To'] = ", ".join(to_emails)
    
    try:
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            if smtp_user and smtp_password:
                server.starttls()
                server.login(smtp_user, smtp_password)
            server.send_message(msg)
    except Exception as e:
        print(f"Failed to send email alert: {e}")

async def pagerduty_notification_handler(alert: dict):
    """Send critical alerts to PagerDuty."""
    
    if alert["severity"] not in ["error", "critical"]:
        return
    
    integration_key = os.getenv("PAGERDUTY_INTEGRATION_KEY")
    if not integration_key:
        return
    
    payload = {
        "routing_key": integration_key,
        "event_action": "trigger",
        "payload": {
            "summary": f"{alert['rule_name']}: {alert['description']}",
            "severity": alert["severity"],
            "source": "multiagents-framework",
            "timestamp": alert["timestamp"],
            "custom_details": alert["metrics"]
        }
    }
    
    async with aiohttp.ClientSession() as session:
        await session.post("https://events.pagerduty.com/v2/enqueue", json=payload)

# Register notification handlers
alert_manager.add_notification_handler(slack_notification_handler)
alert_manager.add_notification_handler(email_notification_handler)
alert_manager.add_notification_handler(pagerduty_notification_handler)
```

## Integration with External Systems

### Prometheus Integration

```python
from prometheus_client import CollectorRegistry, Gauge, Counter, Histogram, start_http_server
import asyncio

class PrometheusExporter:
    """Export MultiAgents metrics to Prometheus."""
    
    def __init__(self, event_monitor, worker_monitor, metrics_collector, port=9090):
        self.event_monitor = event_monitor
        self.worker_monitor = worker_monitor
        self.metrics_collector = metrics_collector
        self.port = port
        
        # Create registry
        self.registry = CollectorRegistry()
        
        # Define metrics
        self.event_total = Counter('multiagents_events_total', 'Total events processed', 
                                 ['event_type', 'status'], registry=self.registry)
        
        self.event_duration = Histogram('multiagents_event_duration_seconds', 'Event processing duration',
                                      ['event_type'], registry=self.registry)
        
        self.worker_executions = Counter('multiagents_worker_executions_total', 'Worker executions',
                                       ['worker_name', 'status'], registry=self.registry)
        
        self.worker_duration = Histogram('multiagents_worker_duration_seconds', 'Worker execution duration',
                                       ['worker_name'], registry=self.registry)
        
        self.system_cpu = Gauge('multiagents_system_cpu_percent', 'CPU usage percentage',
                              registry=self.registry)
        
        self.system_memory = Gauge('multiagents_system_memory_percent', 'Memory usage percentage',
                                 registry=self.registry)
        
        self.active_workflows = Gauge('multiagents_active_workflows', 'Number of active workflows',
                                    registry=self.registry)
    
    async def start_server(self):
        """Start Prometheus metrics server."""
        start_http_server(self.port, registry=self.registry)
        
        # Start metrics update loop
        asyncio.create_task(self._update_metrics_loop())
    
    async def _update_metrics_loop(self):
        """Continuously update Prometheus metrics."""
        while True:
            try:
                await self._update_metrics()
                await asyncio.sleep(30)  # Update every 30 seconds
            except Exception as e:
                print(f"Error updating Prometheus metrics: {e}")
                await asyncio.sleep(60)  # Wait longer on error
    
    async def _update_metrics(self):
        """Update all Prometheus metrics."""
        
        # Event metrics
        event_metrics = await self.event_monitor.get_event_metrics(time_window_minutes=5)
        
        for event_type in ['CommandEvent', 'ResultEvent', 'ErrorEvent']:
            type_metrics = await self.event_monitor.get_event_type_metrics(event_type)
            self.event_total.labels(event_type=event_type, status='success').inc(
                type_metrics.get('success_count', 0)
            )
            self.event_total.labels(event_type=event_type, status='error').inc(
                type_metrics.get('error_count', 0)
            )
        
        # Worker metrics
        worker_summary = await self.worker_monitor.get_worker_performance_summary(time_window_minutes=5)
        
        for worker_name, metrics in worker_summary.get('worker_metrics', {}).items():
            self.worker_executions.labels(worker_name=worker_name, status='success').inc(
                metrics.get('success_count', 0)
            )
            self.worker_executions.labels(worker_name=worker_name, status='error').inc(
                metrics.get('error_count', 0)
            )
            
            if metrics.get('avg_duration_ms'):
                self.worker_duration.labels(worker_name=worker_name).observe(
                    metrics['avg_duration_ms'] / 1000  # Convert to seconds
                )
        
        # System metrics
        system_metrics = await self.metrics_collector.collect_system_metrics()
        self.system_cpu.set(system_metrics.get('cpu_usage_percent', 0))
        self.system_memory.set(system_metrics.get('memory_usage_percent', 0))

# Usage
prometheus_exporter = PrometheusExporter(event_monitor, worker_monitor, metrics_collector)
await prometheus_exporter.start_server()
```

### OpenTelemetry Integration

```python
from opentelemetry import trace, metrics
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader

class OpenTelemetryIntegration:
    """Integration with OpenTelemetry for distributed tracing."""
    
    def __init__(self, service_name="multiagents-framework", endpoint="http://localhost:4317"):
        # Set up tracing
        trace.set_tracer_provider(TracerProvider())
        tracer_provider = trace.get_tracer_provider()
        
        span_exporter = OTLPSpanExporter(endpoint=endpoint)
        span_processor = BatchSpanProcessor(span_exporter)
        tracer_provider.add_span_processor(span_processor)
        
        self.tracer = trace.get_tracer(service_name)
        
        # Set up metrics
        metric_exporter = OTLPMetricExporter(endpoint=endpoint)
        metric_reader = PeriodicExportingMetricReader(metric_exporter, export_interval_millis=30000)
        
        metrics.set_meter_provider(MeterProvider(metric_readers=[metric_reader]))
        self.meter = metrics.get_meter(service_name)
        
        # Create metrics
        self.workflow_counter = self.meter.create_counter(
            "multiagents_workflows_total",
            description="Total number of workflows executed"
        )
        
        self.workflow_duration = self.meter.create_histogram(
            "multiagents_workflow_duration",
            description="Workflow execution duration in milliseconds"
        )
    
    def trace_workflow_execution(self, workflow_id: str, transaction_id: str):
        """Create a trace span for workflow execution."""
        
        return self.tracer.start_span(
            f"workflow.{workflow_id}",
            attributes={
                "workflow.id": workflow_id,
                "workflow.transaction_id": transaction_id,
                "service.name": "multiagents-framework"
            }
        )
    
    def trace_worker_execution(self, worker_name: str, transaction_id: str):
        """Create a trace span for worker execution."""
        
        return self.tracer.start_span(
            f"worker.{worker_name}",
            attributes={
                "worker.name": worker_name,
                "workflow.transaction_id": transaction_id
            }
        )
    
    def record_workflow_metrics(self, workflow_id: str, duration_ms: float, status: str):
        """Record workflow metrics."""
        
        self.workflow_counter.add(1, {"workflow_id": workflow_id, "status": status})
        self.workflow_duration.record(duration_ms, {"workflow_id": workflow_id})

# Usage in framework integration
otel = OpenTelemetryIntegration()

# In orchestrator
with otel.trace_workflow_execution("order_processing", transaction_id) as span:
    # Execute workflow
    span.set_attribute("workflow.status", "running")
    # ... workflow execution ...
    span.set_attribute("workflow.status", "completed")

# Record metrics
otel.record_workflow_metrics("order_processing", 2500.0, "completed")
```

## Best Practices

### 1. Monitoring Strategy

**Layer Your Monitoring**
- **Infrastructure**: CPU, memory, disk, network
- **Application**: Framework metrics, event flow, worker performance
- **Business**: KPIs, user actions, business outcomes

**Set Appropriate Retention**
- **Real-time**: Current state and recent metrics (1-24 hours)
- **Historical**: Trends and analysis (7-30 days)
- **Archive**: Long-term storage for compliance (months/years)

### 2. Alerting Strategy

**Alert Hierarchy**
- **Info**: Informational events, no action needed
- **Warning**: Potential issues, monitor closely
- **Error**: Issues requiring attention, not immediately critical
- **Critical**: Immediate action required, potential outage

**Avoid Alert Fatigue**
- Use appropriate thresholds and cooldown periods
- Implement alert escalation paths
- Group related alerts together
- Provide actionable alert descriptions

### 3. Performance Optimization

**Efficient Metrics Collection**
```python
# Batch metrics collection
async def collect_metrics_batch():
    """Collect multiple metrics efficiently."""
    
    # Collect all metrics concurrently
    tasks = [
        event_monitor.get_event_metrics(5),
        worker_monitor.get_worker_performance_summary(5),
        metrics_collector.collect_system_metrics()
    ]
    
    event_metrics, worker_metrics, system_metrics = await asyncio.gather(*tasks)
    
    return {
        "events": event_metrics,
        "workers": worker_metrics,
        "system": system_metrics,
        "timestamp": datetime.utcnow().isoformat()
    }
```

**Sampling for High-Volume Systems**
```python
class SamplingEventMonitor(EventMonitor):
    """Event monitor with sampling for high-volume systems."""
    
    def __init__(self, sample_rate=0.1, **kwargs):
        super().__init__(**kwargs)
        self.sample_rate = sample_rate
    
    async def track_event_lifecycle(self, event, stage):
        """Track events with sampling."""
        
        # Always track errors and critical events
        if stage == "error" or event.priority == "critical":
            await super().track_event_lifecycle(event, stage)
            return
        
        # Sample other events
        if random.random() < self.sample_rate:
            await super().track_event_lifecycle(event, stage)
```

### 4. Security and Privacy

**Sensitive Data Handling**
```python
def sanitize_context_for_logging(context: dict) -> dict:
    """Remove sensitive data from context before logging."""
    
    sensitive_keys = {"password", "token", "api_key", "credit_card", "ssn"}
    sanitized = {}
    
    for key, value in context.items():
        if any(sensitive in key.lower() for sensitive in sensitive_keys):
            sanitized[key] = "***REDACTED***"
        elif isinstance(value, dict):
            sanitized[key] = sanitize_context_for_logging(value)
        else:
            sanitized[key] = value
    
    return sanitized
```

**Access Control**
```python
class SecureLogger:
    """Logger with access control and data sanitization."""
    
    def __init__(self, base_logger, access_level="standard"):
        self.base_logger = base_logger
        self.access_level = access_level
    
    async def log(self, level, message, **kwargs):
        """Log with data sanitization based on access level."""
        
        if self.access_level == "restricted":
            # Remove all context data for restricted access
            kwargs = {"message": message, "timestamp": datetime.utcnow().isoformat()}
        else:
            # Sanitize sensitive data
            kwargs = {k: sanitize_context_for_logging(v) if isinstance(v, dict) else v 
                     for k, v in kwargs.items()}
        
        await self.base_logger.log(level, message, **kwargs)
```

This comprehensive monitoring guide ensures you can implement production-ready observability for your MultiAgents Framework deployments!