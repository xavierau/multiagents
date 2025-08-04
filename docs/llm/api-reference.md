# MultiAgents Framework - API Reference for LLMs

## Core API Patterns

### Worker Registration and Decoration

```python
# Basic worker decoration
from multiagents import worker

@worker("worker_name")
async def worker_function(context: Dict[str, Any]) -> Dict[str, Any]:
    """Worker function signature."""
    pass

# DSPy worker decoration  
from multiagents import dspy_worker
import dspy

@dspy_worker("dspy_worker_name", signature=CustomSignature)
async def dspy_worker_function(context: Dict[str, Any]) -> Dict[str, Any]:
    """DSPy worker with LLM integration."""
    pass

# Post-processing hooks for DSPy workers
@dspy_worker_function.post_process
async def post_process_function(dspy_result: Dict[str, Any], original_context: Dict[str, Any]) -> Dict[str, Any]:
    """Post-process DSPy results."""
    pass
```

### Workflow Builder API

```python
from multiagents.orchestrator.workflow import WorkflowBuilder

# Fluent API for workflow construction
workflow = (WorkflowBuilder("workflow_name")
    .add_step("step_name", "worker_name")
    .add_step("step_with_compensation", "worker_name", compensation="compensation_worker")
    .build())

# Alternative method-based construction
builder = WorkflowBuilder("workflow_name")
builder.add_step("step1", "worker1")
builder.add_step("step2", "worker2", compensation="comp_worker2") 
workflow = builder.build()
```

### Framework Factory API

```python
from multiagents.core.factory import create_simple_framework

# Create framework components
event_bus, worker_manager, orchestrator = await create_simple_framework(workflow)

# Alternative: Create with configuration
event_bus, worker_manager, orchestrator = await create_simple_framework(
    workflow,
    redis_url="redis://localhost:6379",
    monitoring_config=monitoring_config
)
```

### Event Bus API

```python
from multiagents.event_bus.redis_event_bus import RedisEventBus

# Manual event bus creation
event_bus = RedisEventBus(
    redis_url="redis://localhost:6379",
    event_monitor=event_monitor,
    logger=logger
)

# Lifecycle management
await event_bus.start()
await event_bus.stop()

# Event publishing (typically used internally)
await event_bus.publish("channel", event_data)

# Event subscription (typically used internally)
async def event_handler(event):
    pass

await event_bus.subscribe("channel", event_handler)
```

### Worker Manager API

```python
from multiagents.worker.worker_manager import WorkerManager

# Worker registration
worker_manager.register(worker_function)

# Bulk registration
workers = [worker1, worker2, worker3]
for worker in workers:
    worker_manager.register(worker)

# Lifecycle management
await worker_manager.start()
await worker_manager.stop()

# Worker health monitoring
health_status = worker_manager.get_health_status()
```

### Orchestrator API

```python
from multiagents.orchestrator.orchestrator import Orchestrator

# Workflow execution
transaction_id = await orchestrator.execute_workflow("workflow_name", input_data)

# Status monitoring
status = await orchestrator.get_status(transaction_id)
# Returns: {
#   "state": str,
#   "current_step": Optional[str],
#   "step_results": Dict[str, Any],
#   "error": Optional[str],
#   "timestamp": str
# }

# Cancel workflow
await orchestrator.cancel_workflow(transaction_id)

# Lifecycle management
await orchestrator.start()
await orchestrator.stop()
```

## Data Structures and Types

### Context Structure

```python
# Input context for workers
context: Dict[str, Any] = {
    "transaction_id": str,        # Workflow transaction ID
    "correlation_id": str,        # Event correlation ID
    "step_name": str,            # Current step name
    "workflow_name": str,        # Workflow name
    # ... user-defined fields
}

# Worker result structure
result: Dict[str, Any] = {
    # User-defined output fields
    "output_field": Any,
    "status": str,               # Optional: success/failed/partial
    "timestamp": str,            # Optional: ISO timestamp
    # ... additional fields
}
```

### DSPy Signature Patterns

```python
import dspy

# Basic signature
class BasicSignature(dspy.Signature):
    """Purpose description for LLM."""
    input_field = dspy.InputField(desc="Input description")
    output_field = dspy.OutputField(desc="Output description")

# Complex signature with multiple fields
class ComplexSignature(dspy.Signature):
    """Multi-field signature for structured processing."""
    text = dspy.InputField(desc="Text to process")
    context_type = dspy.InputField(desc="Type of context")
    target_audience = dspy.InputField(desc="Target audience")
    
    summary = dspy.OutputField(desc="Generated summary")
    key_points = dspy.OutputField(desc="Key points list")
    confidence = dspy.OutputField(desc="Confidence score 0-1")
    recommendations = dspy.OutputField(desc="Action recommendations")

# Signature for analysis tasks
class AnalysisSignature(dspy.Signature):
    """Analyze content and extract insights."""
    content = dspy.InputField(desc="Content to analyze")
    analysis_type = dspy.InputField(desc="Type of analysis required")
    
    insights = dspy.OutputField(desc="Key insights discovered")
    sentiment = dspy.OutputField(desc="Overall sentiment")
    entities = dspy.OutputField(desc="Important entities mentioned")
    action_items = dspy.OutputField(desc="Actionable items")
```

### Event Structure Patterns

```python
# Command event structure
command_event = {
    "event_type": "command",
    "worker_name": "target_worker",
    "transaction_id": "TX-12345",
    "correlation_id": "CORR-67890", 
    "context": {
        "input_data": "value",
        "step_name": "current_step"
    },
    "timestamp": "2024-01-01T12:00:00Z",
    "retry_count": 0
}

# Result event structure
result_event = {
    "event_type": "result",
    "worker_name": "source_worker",
    "transaction_id": "TX-12345",
    "correlation_id": "CORR-67890",
    "result": {
        "output_field": "result_value",
        "status": "success"
    },
    "success": True,
    "timestamp": "2024-01-01T12:00:01Z"
}

# Error event structure
error_event = {
    "event_type": "error",
    "worker_name": "failed_worker",
    "transaction_id": "TX-12345", 
    "correlation_id": "CORR-67890",
    "error": "Error description",
    "error_type": "WorkerExecutionError",
    "timestamp": "2024-01-01T12:00:01Z",
    "retry_count": 1
}
```

## Monitoring API

### Logger Configuration

```python
from multiagents.monitoring import MonitoringConfig, FileLogger, ConsoleLogger

# File logging
file_logger = FileLogger(
    file_path="./logs/app.log",
    level="INFO",
    max_file_size_mb=100,
    backup_count=5
)

# Console logging
console_logger = ConsoleLogger(level="DEBUG")

# Monitoring configuration
config = MonitoringConfig(
    logging={
        "default_logger": "file",
        "level": "INFO", 
        "file_path": "./logs/app.log"
    },
    event_monitoring={
        "enabled": True,
        "trace_retention_hours": 24
    },
    worker_monitoring={
        "enabled": True,
        "health_check_interval_seconds": 30
    }
)
```

### Event Monitoring

```python
from multiagents.monitoring import EventMonitor

# Create event monitor
event_monitor = EventMonitor(logger=logger)

# Event lifecycle tracking (automatic)
# - Event dispatch recorded
# - Event pickup recorded  
# - Processing start recorded
# - Processing completion recorded
# - Latency calculated
# - Errors tracked

# Get monitoring data
event_stats = event_monitor.get_event_statistics()
# Returns: {
#   "total_events": int,
#   "events_by_type": Dict[str, int],
#   "average_latency_ms": float,
#   "error_rate": float,
#   "active_traces": int
# }
```

### Worker Monitoring

```python
from multiagents.monitoring import WorkerMonitor

# Create worker monitor
worker_monitor = WorkerMonitor(logger=logger)

# Worker performance tracking (automatic)
# - Success/failure rates
# - Processing times
# - Health status
# - Error patterns

# Get worker stats
worker_stats = worker_monitor.get_worker_statistics()
# Returns: {
#   "workers": {
#     "worker_name": {
#       "total_executions": int,
#       "successful_executions": int,
#       "failed_executions": int,
#       "average_execution_time_ms": float,
#       "last_execution": str,
#       "health_status": str,
#       "error_rate": float
#     }
#   },
#   "overall_stats": {
#     "total_workers": int,
#     "healthy_workers": int,
#     "total_executions": int,
#     "overall_success_rate": float
#   }
# }
```

## Exception Handling

### Exception Types

```python
from multiagents.core.exceptions import (
    WorkerExecutionError,    # Retryable worker error
    WorkflowExecutionError,  # Workflow-level error
    EventBusError,          # Event bus communication error
    ConfigurationError,     # Configuration/setup error
    TimeoutError           # Operation timeout
)

# Worker exception handling pattern
@worker("error_prone_worker")
async def error_prone_worker(context: Dict[str, Any]) -> Dict[str, Any]:
    try:
        # Worker logic
        result = await risky_operation(context)
        return {"result": result}
        
    except ValueError as e:
        # Validation error - don't retry
        raise ValueError(f"Invalid input: {e}")
        
    except ConnectionError as e:
        # Retryable error
        raise WorkerExecutionError(f"Connection failed: {e}")
        
    except Exception as e:
        # Unexpected error - let framework decide
        raise WorkerExecutionError(f"Unexpected error: {e}")
```

### Error Recovery Patterns

```python
# Graceful error handling in workers
@worker("resilient_worker")
async def resilient_worker(context: Dict[str, Any]) -> Dict[str, Any]:
    """Worker with comprehensive error handling."""
    
    # Input validation
    if not context.get("required_field"):
        return {
            "status": "validation_failed",
            "error": "Missing required field",
            "retry_recommended": False
        }
    
    try:
        # Main operation
        result = await main_operation(context)
        return {
            "status": "success",
            "result": result
        }
        
    except TemporaryError as e:
        # Temporary issue - return status for orchestrator to handle
        return {
            "status": "temporary_failure", 
            "error": str(e),
            "retry_recommended": True,
            "retry_after_seconds": 30
        }
        
    except PermanentError as e:
        # Permanent issue - don't retry
        return {
            "status": "permanent_failure",
            "error": str(e),
            "retry_recommended": False
        }
```

## DSPy Integration Patterns

### DSPy Configuration

```python
import dspy
import os

# Environment-based configuration
def setup_dspy():
    """Configure DSPy based on environment."""
    env = os.getenv("ENVIRONMENT", "development")
    
    if env == "production":
        lm = dspy.OpenAI(
            model="gpt-3.5-turbo",
            api_key=os.getenv("OPENAI_API_KEY"),
            max_tokens=300,
            temperature=0.3,
            request_timeout=30
        )
    elif env == "development": 
        lm = dspy.OpenAI(
            model="gpt-3.5-turbo",
            api_key=os.getenv("OPENAI_API_KEY"),
            max_tokens=500,
            temperature=0.7
        )
    else:  # testing
        lm = MockLLM()  # Mock for testing
    
    dspy.settings.configure(lm=lm)
    return lm

# Alternative providers
def setup_anthropic():
    """Configure with Anthropic Claude."""
    lm = dspy.Anthropic(
        model="claude-3-sonnet-20240229",
        api_key=os.getenv("ANTHROPIC_API_KEY"),
        max_tokens=500
    )
    dspy.settings.configure(lm=lm)
    return lm

def setup_azure_openai():
    """Configure with Azure OpenAI."""
    lm = dspy.AzureOpenAI(
        api_base=os.getenv("AZURE_OPENAI_ENDPOINT"),
        api_key=os.getenv("AZURE_OPENAI_KEY"),
        api_version="2023-12-01-preview",
        model="gpt-35-turbo"
    )
    dspy.settings.configure(lm=lm)
    return lm
```

### DSPy Worker Implementation Patterns

```python
# Simple DSPy worker
@dspy_worker("simple_analysis")
async def simple_analysis(context: Dict[str, Any]) -> Dict[str, Any]:
    """Simple DSPy worker without custom signature."""
    text = context.get("text", "")
    analysis_type = context.get("analysis_type", "general")
    
    return {
        "text": text,
        "analysis_type": analysis_type,
        "timestamp": datetime.utcnow().isoformat()
    }

# DSPy worker with signature
@dspy_worker("structured_analysis", signature=AnalysisSignature)
async def structured_analysis(context: Dict[str, Any]) -> Dict[str, Any]:
    """DSPy worker with structured input/output."""
    return {
        "content": context.get("content", ""),
        "analysis_type": context.get("analysis_type", "general")
    }

# Post-processing for validation
@structured_analysis.post_process
async def validate_analysis_output(dspy_result: Dict[str, Any], original_context: Dict[str, Any]) -> Dict[str, Any]:
    """Validate and enhance DSPy output."""
    
    # Validate sentiment
    sentiment = dspy_result.get("sentiment", "neutral").lower()
    if sentiment not in ["positive", "negative", "neutral"]:
        sentiment = "neutral"
    
    # Parse entities if string
    entities = dspy_result.get("entities", [])
    if isinstance(entities, str):
        entities = [e.strip() for e in entities.split(",") if e.strip()]
    
    return {
        **dspy_result,
        "sentiment": sentiment,
        "entities": entities,
        "processed_at": datetime.utcnow().isoformat(),
        "validation_passed": True
    }
```

## Complete Application Template

```python
import asyncio
from datetime import datetime
from typing import Dict, Any
import dspy

from multiagents import worker, dspy_worker
from multiagents.core.factory import create_simple_framework
from multiagents.orchestrator.workflow import WorkflowBuilder
from multiagents.monitoring import MonitoringConfig

# Configure DSPy
def setup_llm():
    lm = dspy.OpenAI(
        model="gpt-3.5-turbo",
        api_key="your-api-key",
        max_tokens=300
    )
    dspy.settings.configure(lm=lm)

# Define workers
@worker("data_validation")
async def validate_data(context: Dict[str, Any]) -> Dict[str, Any]:
    """Validate input data."""
    data = context.get("data")
    if not data:
        raise ValueError("No data provided")
    
    return {
        "validated_data": data,
        "validation_status": "passed",
        "timestamp": datetime.utcnow().isoformat()
    }

class ProcessingSignature(dspy.Signature):
    """Process data with LLM analysis."""
    data = dspy.InputField(desc="Data to process")
    analysis_type = dspy.InputField(desc="Type of analysis")
    result = dspy.OutputField(desc="Processing result")
    confidence = dspy.OutputField(desc="Confidence score")

@dspy_worker("llm_processing", signature=ProcessingSignature)
async def process_with_llm(context: Dict[str, Any]) -> Dict[str, Any]:
    """Process data using LLM."""
    return {
        "data": context.get("validated_data"),
        "analysis_type": "comprehensive"
    }

@worker("save_results")
async def save_results(context: Dict[str, Any]) -> Dict[str, Any]:
    """Save processing results."""
    result = context.get("result")
    
    # Simulate saving
    saved_id = f"RESULT-{int(datetime.utcnow().timestamp())}"
    
    return {
        "saved_id": saved_id,
        "result": result,
        "saved_at": datetime.utcnow().isoformat()
    }

# Define workflow
def create_processing_workflow():
    return (WorkflowBuilder("data_processing")
        .add_step("validate", "data_validation")
        .add_step("process", "llm_processing")
        .add_step("save", "save_results")
        .build())

# Main application
async def main():
    """Complete application example."""
    
    # Setup
    setup_llm()
    workflow = create_processing_workflow()
    
    # Create framework
    event_bus, worker_manager, orchestrator = await create_simple_framework(workflow)
    
    try:
        # Start framework
        await event_bus.start()
        
        # Register workers
        workers = [validate_data, process_with_llm, save_results]
        for worker_func in workers:
            worker_manager.register(worker_func)
        
        await worker_manager.start()
        await orchestrator.start()
        
        # Execute workflow
        input_data = {"data": "Sample data to process"}
        transaction_id = await orchestrator.execute_workflow("data_processing", input_data)
        
        # Monitor execution
        while True:
            status = await orchestrator.get_status(transaction_id)
            if status['state'] in {"completed", "failed", "compensated"}:
                print(f"Workflow {status['state']}")
                if status.get('step_results'):
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

This API reference provides comprehensive patterns for implementing MultiAgents Framework applications with proper error handling, monitoring, and LLM integration.