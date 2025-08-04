# MultiAgents Framework - Quick Reference

## Essential Code Snippets

### Basic Worker

```python
from multiagents import worker
from typing import Dict, Any

@worker("worker_name")
async def worker_function(context: Dict[str, Any]) -> Dict[str, Any]:
    # Input validation
    required_field = context.get("required_field")
    if not required_field:
        raise ValueError("Missing required field")
    
    # Worker logic
    result = process_data(required_field)
    
    # Return result
    return {
        "output": result,
        "status": "success",
        "timestamp": datetime.utcnow().isoformat()
    }
```

### DSPy Worker

```python
import dspy
from multiagents import dspy_worker

class WorkerSignature(dspy.Signature):
    """Description for LLM."""
    input_field = dspy.InputField(desc="Input description")
    output_field = dspy.OutputField(desc="Output description")

@dspy_worker("llm_worker", signature=WorkerSignature)
async def llm_worker(context: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "input_field": context.get("input"),
        "processing_type": "llm"
    }

@llm_worker.post_process
async def validate_output(dspy_result: Dict[str, Any], original_context: Dict[str, Any]) -> Dict[str, Any]:
    # Validate and enhance LLM output
    return {**dspy_result, "validated": True}
```

### Workflow Definition

```python
from multiagents.orchestrator.workflow import WorkflowBuilder

def create_workflow():
    return (WorkflowBuilder("workflow_name")
        .add_step("step1", "worker1")
        .add_step("step2", "worker2", compensation="comp_worker2")
        .add_step("step3", "worker3", compensation="comp_worker3")
        .build())
```

### Framework Setup

```python
from multiagents.core.factory import create_simple_framework

async def setup_and_run():
    workflow = create_workflow()
    event_bus, worker_manager, orchestrator = await create_simple_framework(workflow)
    
    try:
        # Start framework
        await event_bus.start()
        
        # Register workers
        workers = [worker1, worker2, worker3, comp_worker2, comp_worker3]
        for worker_func in workers:
            worker_manager.register(worker_func)
        
        await worker_manager.start()
        await orchestrator.start()
        
        # Execute workflow
        transaction_id = await orchestrator.execute_workflow("workflow_name", input_data)
        
        # Monitor execution
        while True:
            status = await orchestrator.get_status(transaction_id)
            if status['state'] in {"completed", "failed", "compensated", "cancelled"}:
                return status
            await asyncio.sleep(1)
            
    finally:
        await worker_manager.stop()
        await orchestrator.stop()
        await event_bus.stop()
```

### Error Handling

```python
from multiagents.core.exceptions import WorkerExecutionError

@worker("error_handling_worker")
async def error_handling_worker(context: Dict[str, Any]) -> Dict[str, Any]:
    try:
        result = risky_operation(context)
        return {"result": result}
        
    except ValueError as e:
        # Validation error - don't retry
        raise ValueError(f"Invalid input: {e}")
        
    except ConnectionError as e:
        # Retryable error
        raise WorkerExecutionError(f"Connection failed: {e}")
        
    except Exception as e:
        # Unexpected error
        raise WorkerExecutionError(f"Unexpected error: {e}")
```

### Compensation Worker

```python
@worker("compensation_worker")
async def compensation_worker(context: Dict[str, Any]) -> Dict[str, Any]:
    resource_id = context.get("resource_id")
    
    if not resource_id:
        return {"status": "no_action_needed"}
    
    try:
        release_resource(resource_id)
        return {
            "status": "success",
            "resource_released": resource_id,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        # Don't raise in compensation workers
        return {
            "status": "failed",
            "error": str(e),
            "requires_manual_intervention": True
        }
```

## Common Patterns

### Input Validation

```python
def validate_context(context: Dict[str, Any], required_fields: list) -> None:
    """Validate required fields in context."""
    missing = [field for field in required_fields if field not in context]
    if missing:
        raise ValueError(f"Missing required fields: {missing}")

@worker("validated_worker")
async def validated_worker(context: Dict[str, Any]) -> Dict[str, Any]:
    validate_context(context, ["field1", "field2"])
    # Worker logic...
```

### Partial Success Handling

```python
@worker("batch_processor")
async def batch_processor(context: Dict[str, Any]) -> Dict[str, Any]:
    items = context.get("items", [])
    processed = []
    failed = []
    
    for item in items:
        try:
            result = process_item(item)
            processed.append({"item": item, "result": result})
        except Exception as e:
            failed.append({"item": item, "error": str(e)})
    
    return {
        "processed_count": len(processed),
        "failed_count": len(failed),
        "processed_items": processed,
        "failed_items": failed,
        "status": "partial" if failed else "success"
    }
```

### Retry Logic

```python
import asyncio
from functools import wraps

def retry(max_attempts=3, delay=1.0):
    """Retry decorator for workers."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_attempts):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_attempts - 1:
                        await asyncio.sleep(delay * (2 ** attempt))
                    else:
                        raise
            
            raise last_exception
        return wrapper
    return decorator

@retry(max_attempts=3, delay=1.0)
@worker("retry_worker")
async def retry_worker(context: Dict[str, Any]) -> Dict[str, Any]:
    # Worker that might need retries
    pass
```

## DSPy Patterns

### DSPy Configuration

```python
import dspy
import os

def setup_openai():
    lm = dspy.OpenAI(
        model="gpt-3.5-turbo",
        api_key=os.getenv("OPENAI_API_KEY"),
        max_tokens=300,
        temperature=0.7
    )
    dspy.settings.configure(lm=lm)

def setup_anthropic():
    lm = dspy.Anthropic(
        model="claude-3-sonnet-20240229",
        api_key=os.getenv("ANTHROPIC_API_KEY"),
        max_tokens=500
    )
    dspy.settings.configure(lm=lm)
```

### Common DSPy Signatures

```python
# Sentiment analysis
class SentimentSignature(dspy.Signature):
    """Analyze sentiment of text."""
    text = dspy.InputField(desc="Text to analyze")
    sentiment = dspy.OutputField(desc="positive, negative, or neutral")
    confidence = dspy.OutputField(desc="Confidence score 0-1")

# Text summarization
class SummarySignature(dspy.Signature):
    """Summarize text content."""
    text = dspy.InputField(desc="Text to summarize")
    max_length = dspy.InputField(desc="Maximum summary length")
    summary = dspy.OutputField(desc="Concise summary")
    key_points = dspy.OutputField(desc="Main points")

# Content generation
class GenerationSignature(dspy.Signature):
    """Generate content based on requirements."""
    topic = dspy.InputField(desc="Content topic")
    audience = dspy.InputField(desc="Target audience")
    tone = dspy.InputField(desc="Desired tone")
    content = dspy.OutputField(desc="Generated content")
    word_count = dspy.OutputField(desc="Approximate word count")

# Translation
class TranslationSignature(dspy.Signature):
    """Translate text to target language."""
    text = dspy.InputField(desc="Text to translate")
    target_language = dspy.InputField(desc="Target language")
    translated_text = dspy.OutputField(desc="Translated text")
    quality_score = dspy.OutputField(desc="Translation quality 0-1")
```

### DSPy Post-Processing

```python
# Validate sentiment output
@sentiment_worker.post_process
async def validate_sentiment(dspy_result: Dict[str, Any], original_context: Dict[str, Any]) -> Dict[str, Any]:
    sentiment = dspy_result.get("sentiment", "neutral").lower()
    if sentiment not in ["positive", "negative", "neutral"]:
        sentiment = "neutral"
    
    confidence = float(dspy_result.get("confidence", 0.5))
    confidence = max(0.0, min(1.0, confidence))
    
    return {
        **dspy_result,
        "sentiment": sentiment,
        "confidence": confidence,
        "requires_review": confidence < 0.7
    }

# Parse list outputs
@analysis_worker.post_process  
async def parse_list_outputs(dspy_result: Dict[str, Any], original_context: Dict[str, Any]) -> Dict[str, Any]:
    # Parse key_points if string
    key_points = dspy_result.get("key_points", [])
    if isinstance(key_points, str):
        key_points = [point.strip() for point in key_points.split("\n") if point.strip()]
    
    return {
        **dspy_result,
        "key_points": key_points,
        "key_points_count": len(key_points)
    }
```

## Monitoring Setup

```python
from multiagents.monitoring import MonitoringConfig, EventMonitor, WorkerMonitor

# Configuration
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

# Create monitors
logger = config.create_logger()
event_monitor = EventMonitor(logger=logger)
worker_monitor = WorkerMonitor(logger=logger)

# Use with framework
event_bus = RedisEventBus(event_monitor=event_monitor, logger=logger)
worker_manager = WorkerManager(event_bus, worker_monitor=worker_monitor, logger=logger)
```

## Workflow Execution Patterns

### Basic Execution

```python
async def execute_workflow(orchestrator, workflow_name, input_data):
    transaction_id = await orchestrator.execute_workflow(workflow_name, input_data)
    
    while True:
        status = await orchestrator.get_status(transaction_id)
        if status['state'] in {"completed", "failed", "compensated", "cancelled"}:
            return status
        await asyncio.sleep(1)
```

### Execution with Progress Monitoring

```python
async def execute_with_progress(orchestrator, workflow_name, input_data):
    transaction_id = await orchestrator.execute_workflow(workflow_name, input_data)
    
    last_step = None
    while True:
        status = await orchestrator.get_status(transaction_id)
        
        # Show progress
        current_step = status.get('current_step')
        if current_step and current_step != last_step:
            print(f"Processing: {current_step}")
            last_step = current_step
        
        if status['state'] in {"completed", "failed", "compensated", "cancelled"}:
            print(f"Final state: {status['state']}")
            return status
            
        await asyncio.sleep(0.5)
```

### Batch Processing

```python
async def process_batch(orchestrator, workflow_name, batch_items):
    """Process multiple items in parallel."""
    tasks = []
    
    for item in batch_items:
        task = execute_workflow(orchestrator, workflow_name, item)
        tasks.append(task)
    
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    successful = [r for r in results if not isinstance(r, Exception)]
    failed = [r for r in results if isinstance(r, Exception)]
    
    return {
        "successful_count": len(successful),
        "failed_count": len(failed),
        "results": successful,
        "errors": failed
    }
```

## Testing Patterns

### Unit Testing Workers

```python
import pytest

@pytest.mark.asyncio
async def test_worker():
    context = {"input": "test_value"}
    result = await worker_function(context)
    
    assert result["status"] == "success"
    assert "output" in result

@pytest.mark.asyncio
async def test_worker_validation():
    context = {}  # Missing required field
    
    with pytest.raises(ValueError):
        await worker_function(context)
```

### Integration Testing

```python
@pytest.mark.asyncio
async def test_workflow():
    workflow = create_test_workflow()
    event_bus, worker_manager, orchestrator = await create_simple_framework(workflow)
    
    try:
        await event_bus.start()
        
        # Register test workers
        for worker in test_workers:
            worker_manager.register(worker)
        
        await worker_manager.start()
        await orchestrator.start()
        
        # Execute workflow
        transaction_id = await orchestrator.execute_workflow("test_workflow", test_data)
        status = await wait_for_completion(orchestrator, transaction_id)
        
        assert status['state'] == 'completed'
        assert 'step1' in status['step_results']
        
    finally:
        await worker_manager.stop()
        await orchestrator.stop()
        await event_bus.stop()
```

### Error Scenario Testing

```python
@pytest.mark.asyncio
async def test_compensation():
    # Test workflow with failing step
    failing_data = {"cause_failure": True}
    
    transaction_id = await orchestrator.execute_workflow("test_workflow", failing_data)
    status = await wait_for_completion(orchestrator, transaction_id)
    
    assert status['state'] == 'compensated'
    # Verify compensation effects
```

## Environment Configuration

```python
import os
from dataclasses import dataclass

@dataclass
class Config:
    redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379")
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    environment: str = os.getenv("ENVIRONMENT", "development")

def load_config():
    return Config()

# Usage
config = load_config()
```

This quick reference provides essential patterns and code snippets for rapid development with the MultiAgents Framework.