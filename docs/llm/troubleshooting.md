# MultiAgents Framework - Troubleshooting Guide

## Common Issues and Solutions

### 1. Worker Registration Issues

#### Problem: Worker not found error
```
Error: Worker 'my_worker' not found
```

**Causes and Solutions:**

1. **Worker not registered**
   ```python
   # Problem: Worker defined but not registered
   @worker("my_worker")
   async def my_worker(context):
       pass
   
   # Solution: Register the worker
   worker_manager.register(my_worker)
   ```

2. **Name mismatch**
   ```python
   # Problem: Decorator name doesn't match workflow step
   @worker("worker_name")  # Decorated name
   async def my_function(context):
       pass
   
   workflow = (WorkflowBuilder("test")
       .add_step("step1", "my_worker")  # Different name
       .build())
   
   # Solution: Match names exactly
   @worker("my_worker")
   async def my_function(context):
       pass
   ```

3. **Worker registration timing**
   ```python
   # Problem: Using worker before registration
   transaction_id = await orchestrator.execute_workflow("test", {})
   worker_manager.register(my_worker)  # Too late
   
   # Solution: Register before execution
   worker_manager.register(my_worker)
   await worker_manager.start()
   transaction_id = await orchestrator.execute_workflow("test", {})
   ```

#### Problem: Duplicate worker registration
```
Warning: Worker 'my_worker' already registered
```

**Solution:**
```python
# Check if worker is already registered
if not worker_manager.is_registered("my_worker"):
    worker_manager.register(my_worker)

# Or use force registration
worker_manager.register(my_worker, force=True)
```

### 2. DSPy Integration Issues

#### Problem: DSPy not configured
```
Error: No language model configured in DSPy
```

**Solution:**
```python
import dspy
import os

# Configure DSPy before using dspy_worker
def setup_dspy():
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY environment variable not set")
    
    lm = dspy.OpenAI(
        model="gpt-3.5-turbo",
        api_key=api_key,
        max_tokens=300
    )
    dspy.settings.configure(lm=lm)

# Call before creating DSPy workers
setup_dspy()
```

#### Problem: DSPy signature errors
```
Error: DSPy signature validation failed
```

**Common causes and solutions:**

1. **Missing signature class**
   ```python
   # Problem: Using signature without defining it
   @dspy_worker("worker", signature=UndefinedSignature)
   async def worker(context):
       pass
   
   # Solution: Define the signature first
   class WorkerSignature(dspy.Signature):
       """Worker description."""
       input_field = dspy.InputField(desc="Input description")
       output_field = dspy.OutputField(desc="Output description")
   
   @dspy_worker("worker", signature=WorkerSignature)
   async def worker(context):
       pass
   ```

2. **Invalid signature structure**
   ```python
   # Problem: Incorrect signature definition
   class BadSignature(dspy.Signature):
       # Missing docstring
       input_field = "invalid"  # Should be InputField
   
   # Solution: Proper signature structure
   class GoodSignature(dspy.Signature):
       """Clear description of what this signature does."""
       input_field = dspy.InputField(desc="Input description")
       output_field = dspy.OutputField(desc="Output description")
   ```

#### Problem: DSPy post-processing errors
```
Error in post-processing: 'NoneType' object has no attribute 'get'
```

**Solution:**
```python
@dspy_worker.post_process
async def safe_post_process(dspy_result: Dict[str, Any], original_context: Dict[str, Any]) -> Dict[str, Any]:
    """Safe post-processing with null checks."""
    
    # Handle None result
    if dspy_result is None:
        return {
            "error": "DSPy returned None result",
            "status": "failed",
            "original_context": original_context
        }
    
    # Handle missing fields safely
    output_field = dspy_result.get("output_field", "")
    confidence = dspy_result.get("confidence", 0.0)
    
    # Validate and convert types safely
    try:
        confidence = float(confidence) if confidence is not None else 0.0
        confidence = max(0.0, min(1.0, confidence))
    except (ValueError, TypeError):
        confidence = 0.0
    
    return {
        **dspy_result,
        "output_field": output_field,
        "confidence": confidence,
        "post_processed": True
    }
```

### 3. Workflow Execution Issues

#### Problem: Workflow stuck in "running" state
```
Workflow state: running (no progress for 5 minutes)
```

**Diagnostic steps:**

1. **Check worker health**
   ```python
   # Get worker status
   health_status = worker_manager.get_health_status()
   print("Worker health:", health_status)
   
   # Check specific worker
   worker_stats = worker_monitor.get_worker_statistics()
   print("Worker stats:", worker_stats)
   ```

2. **Check current step**
   ```python
   status = await orchestrator.get_status(transaction_id)
   current_step = status.get('current_step')
   print(f"Stuck on step: {current_step}")
   
   # Check step results
   step_results = status.get('step_results', {})
   print("Completed steps:", list(step_results.keys()))
   ```

3. **Monitor event flow**
   ```python
   # Check event statistics
   event_stats = event_monitor.get_event_statistics()
   print("Event stats:", event_stats)
   
   # Look for stuck events
   active_traces = event_monitor.get_active_traces()
   print("Active traces:", active_traces)
   ```

**Common solutions:**

1. **Worker process died**
   ```python
   # Restart worker manager
   await worker_manager.stop()
   await worker_manager.start()
   ```

2. **Redis connection lost**
   ```python
   # Check Redis connection
   try:
       await event_bus.publish("test_channel", {"test": "message"})
       print("Redis connection OK")
   except Exception as e:
       print(f"Redis connection failed: {e}")
       # Restart event bus
       await event_bus.stop()
       await event_bus.start()
   ```

3. **Worker infinite loop**
   ```python
   # Add timeout to worker
   @worker("problematic_worker")
   async def problematic_worker(context: Dict[str, Any]) -> Dict[str, Any]:
       # Add explicit timeout
       try:
           result = await asyncio.wait_for(
               long_running_operation(context),
               timeout=300  # 5 minutes
           )
           return result
       except asyncio.TimeoutError:
           return {
               "status": "timeout",
               "error": "Operation timed out after 5 minutes"
           }
   ```

#### Problem: Workflow fails immediately
```
Workflow state: failed (within seconds of starting)
```

**Diagnostic approach:**

1. **Check workflow definition**
   ```python
   # Verify workflow structure
   workflow_dict = workflow.to_dict()
   print("Workflow definition:", workflow_dict)
   
   # Check all referenced workers are registered
   for step in workflow_dict["steps"]:
       worker_name = step["worker_name"]
       if not worker_manager.is_registered(worker_name):
           print(f"Missing worker: {worker_name}")
   ```

2. **Check input validation**
   ```python
   # Test with minimal valid input
   minimal_input = {
       "required_field": "test_value"
   }
   
   try:
       transaction_id = await orchestrator.execute_workflow("test_workflow", minimal_input)
       print("Workflow started with minimal input")
   except Exception as e:
       print(f"Failed with minimal input: {e}")
   ```

3. **Test workers individually**
   ```python
   # Test first worker directly
   try:
       result = await first_worker(test_context)
       print("First worker result:", result)
   except Exception as e:
       print(f"First worker failed: {e}")
       import traceback
       traceback.print_exc()
   ```

### 4. Compensation Issues

#### Problem: Compensations not executing
```
Workflow state: failed (but no compensations ran)
```

**Causes and solutions:**

1. **No compensations defined**
   ```python
   # Problem: Missing compensation definitions
   workflow = (WorkflowBuilder("test")
       .add_step("step1", "worker1")  # No compensation
       .add_step("step2", "worker2")  # No compensation
       .build())
   
   # Solution: Add compensations for resource-allocating steps
   workflow = (WorkflowBuilder("test")
       .add_step("step1", "worker1", compensation="comp_worker1")
       .add_step("step2", "worker2", compensation="comp_worker2")
       .build())
   ```

2. **Compensation workers not registered**
   ```python
   # Problem: Compensation worker not registered
   @worker("comp_worker1")
   async def compensation_worker(context):
       pass
   
   # Missing: worker_manager.register(compensation_worker)
   
   # Solution: Register compensation workers
   worker_manager.register(worker1)
   worker_manager.register(worker2)
   worker_manager.register(compensation_worker)  # Don't forget compensations
   ```

3. **Early failure (before compensable steps)**
   ```python
   # If workflow fails in first step, no compensations needed
   # This is normal behavior
   
   # Check which step failed
   status = await orchestrator.get_status(transaction_id)
   if status['state'] == 'failed':
       error = status.get('error')
       step_results = status.get('step_results', {})
       print(f"Failed at: {len(step_results)} steps completed")
       print(f"Error: {error}")
   ```

#### Problem: Compensation failures
```
Workflow state: compensated (but some compensations failed)
```

**Solution pattern:**
```python
@worker("robust_compensation")
async def robust_compensation(context: Dict[str, Any]) -> Dict[str, Any]:
    """Compensation worker with robust error handling."""
    
    resource_id = context.get("resource_id")
    
    # Always return a result, never raise exceptions
    if not resource_id:
        return {
            "compensation_status": "no_action_needed",
            "message": "No resource to release"
        }
    
    try:
        release_resource(resource_id)
        return {
            "compensation_status": "success",
            "resource_released": resource_id,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    except ResourceNotFoundError:
        # Resource already released - this is OK
        return {
            "compensation_status": "already_released",
            "resource_id": resource_id,
            "message": "Resource was already released"
        }
    
    except Exception as e:
        # Log error but don't raise - continue with other compensations
        return {
            "compensation_status": "failed",
            "error": str(e),
            "resource_id": resource_id,
            "requires_manual_intervention": True,
            "escalation_needed": True
        }
```

### 5. Performance Issues

#### Problem: Slow workflow execution
```
Workflow taking much longer than expected
```

**Diagnostic steps:**

1. **Profile individual workers**
   ```python
   import time
   
   @worker("timed_worker")
   async def timed_worker(context: Dict[str, Any]) -> Dict[str, Any]:
       start_time = time.time()
       
       # Worker logic here
       result = await worker_operation(context)
       
       execution_time = time.time() - start_time
       
       return {
           **result,
           "execution_time_seconds": execution_time,
           "performance_data": {
               "start_time": start_time,
               "end_time": time.time()
           }
       }
   ```

2. **Check event bus latency**
   ```python
   # Monitor event processing times
   event_stats = event_monitor.get_event_statistics()
   avg_latency = event_stats.get("average_latency_ms", 0)
   
   if avg_latency > 1000:  # More than 1 second
       print(f"High event latency: {avg_latency}ms")
       # Check Redis performance, network, etc.
   ```

3. **Identify bottlenecks**
   ```python
   # Add timing to workflow steps
   status = await orchestrator.get_status(transaction_id)
   step_results = status.get('step_results', {})
   
   for step_name, result in step_results.items():
       if 'execution_time_seconds' in result:
           print(f"{step_name}: {result['execution_time_seconds']:.2f}s")
   ```

**Common performance solutions:**

1. **Optimize slow workers**
   ```python
   # Add caching
   from functools import lru_cache
   
   @lru_cache(maxsize=100)
   def expensive_computation(input_data):
       # Cached computation
       pass
   
   # Use connection pooling
   import aioredis
   
   redis_pool = aioredis.ConnectionPool.from_url("redis://localhost:6379")
   
   async def get_redis_connection():
       return aioredis.Redis(connection_pool=redis_pool)
   ```

2. **Parallel processing simulation**
   ```python
   @worker("batch_processor")
   async def batch_processor(context: Dict[str, Any]) -> Dict[str, Any]:
       """Process items in parallel using asyncio.gather."""
       items = context["items"]
       
       # Process items concurrently
       tasks = [process_single_item(item) for item in items]
       results = await asyncio.gather(*tasks, return_exceptions=True)
       
       successful = [r for r in results if not isinstance(r, Exception)]
       failed = [r for r in results if isinstance(r, Exception)]
       
       return {
           "successful_count": len(successful),
           "failed_count": len(failed),
           "results": successful,
           "errors": [str(e) for e in failed]
       }
   ```

### 6. Resource Management Issues

#### Problem: Memory leaks
```
Memory usage continuously increasing
```

**Diagnostic and solutions:**

1. **Monitor memory usage**
   ```python
   import psutil
   import os
   
   @worker("memory_monitored_worker")
   async def memory_monitored_worker(context: Dict[str, Any]) -> Dict[str, Any]:
       process = psutil.Process(os.getpid())
       initial_memory = process.memory_info().rss / 1024 / 1024  # MB
       
       # Worker logic
       result = await worker_operation(context)
       
       final_memory = process.memory_info().rss / 1024 / 1024  # MB
       memory_delta = final_memory - initial_memory
       
       if memory_delta > 100:  # More than 100MB increase
           print(f"High memory usage in worker: {memory_delta:.2f}MB")
       
       return {
           **result,
           "memory_usage_mb": final_memory,
           "memory_delta_mb": memory_delta
       }
   ```

2. **Clean up resources**
   ```python
   @worker("resource_cleanup_worker")
   async def resource_cleanup_worker(context: Dict[str, Any]) -> Dict[str, Any]:
       temp_files = []
       connections = []
       
       try:
           # Resource allocation
           temp_file = create_temp_file()
           temp_files.append(temp_file)
           
           connection = await create_db_connection()
           connections.append(connection)
           
           # Worker logic
           result = await process_with_resources(temp_file, connection)
           
           return result
       
       finally:
           # Always clean up
           for temp_file in temp_files:
               try:
                   os.remove(temp_file)
               except OSError:
                   pass
           
           for connection in connections:
               try:
                   await connection.close()
               except Exception:
                   pass
   ```

#### Problem: Connection pool exhaustion
```
Error: Cannot acquire connection from pool
```

**Solutions:**

1. **Configure connection limits**
   ```python
   # Redis connection pool
   redis_pool = aioredis.ConnectionPool.from_url(
       "redis://localhost:6379",
       max_connections=20,
       retry_on_timeout=True
   )
   
   # Database connection pool
   import asyncpg
   
   db_pool = await asyncpg.create_pool(
       "postgresql://user:pass@localhost/db",
       min_size=5,
       max_size=20,
       command_timeout=60
   )
   ```

2. **Proper connection management**
   ```python
   @worker("connection_managed_worker")
   async def connection_managed_worker(context: Dict[str, Any]) -> Dict[str, Any]:
       async with db_pool.acquire() as connection:
           # Use connection
           result = await connection.fetch("SELECT * FROM table")
           
           return {"data": result}
       # Connection automatically returned to pool
   ```

### 7. Configuration Issues

#### Problem: Environment-specific failures
```
Works in development, fails in production
```

**Common configuration issues:**

1. **Missing environment variables**
   ```python
   import os
   
   def validate_environment():
       """Validate required environment variables."""
       required_vars = [
           "REDIS_URL",
           "OPENAI_API_KEY",
           "DATABASE_URL"
       ]
       
       missing = [var for var in required_vars if not os.getenv(var)]
       
       if missing:
           raise ValueError(f"Missing environment variables: {missing}")
       
       return True
   
   # Call at startup
   validate_environment()
   ```

2. **Configuration file issues**
   ```python
   # Use configuration validation
   from dataclasses import dataclass
   from typing import Optional
   
   @dataclass
   class FrameworkConfig:
       redis_url: str
       openai_api_key: str
       log_level: str = "INFO"
       worker_timeout: int = 300
       max_retries: int = 3
       
       def __post_init__(self):
           if not self.redis_url:
               raise ValueError("redis_url is required")
           if not self.openai_api_key:
               raise ValueError("openai_api_key is required")
   
   # Load and validate configuration
   config = FrameworkConfig(
       redis_url=os.getenv("REDIS_URL"),
       openai_api_key=os.getenv("OPENAI_API_KEY"),
       log_level=os.getenv("LOG_LEVEL", "INFO")
   )
   ```

### 8. Debugging Strategies

#### Enable comprehensive logging
```python
import logging

# Configure detailed logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('multiagents.log'),
        logging.StreamHandler()
    ]
)

# Enable framework debug logging
framework_logger = logging.getLogger('multiagents')
framework_logger.setLevel(logging.DEBUG)
```

#### Add debugging workers
```python
@worker("debug_worker")
async def debug_worker(context: Dict[str, Any]) -> Dict[str, Any]:
    """Worker for debugging context and state."""
    
    import json
    import sys
    
    debug_info = {
        "context_keys": list(context.keys()),
        "context_values": {k: str(v)[:100] for k, v in context.items()},
        "context_size": len(json.dumps(context)),
        "python_version": sys.version,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    print(f"DEBUG - Context: {debug_info}")
    
    return {
        "debug_info": debug_info,
        "original_context": context
    }
```

#### Monitor workflow progress
```python
async def monitor_workflow_execution(orchestrator, transaction_id):
    """Monitor and log workflow execution progress."""
    
    last_step = None
    step_times = {}
    start_time = time.time()
    
    while True:
        status = await orchestrator.get_status(transaction_id)
        current_step = status.get('current_step')
        
        # Log step transitions
        if current_step and current_step != last_step:
            now = time.time()
            if last_step:
                step_times[last_step] = now - step_times.get(f"{last_step}_start", now)
            step_times[f"{current_step}_start"] = now
            
            print(f"Workflow step: {current_step}")
            last_step = current_step
        
        # Check for completion
        if status['state'] in {"completed", "failed", "compensated", "cancelled"}:
            total_time = time.time() - start_time
            print(f"Workflow {status['state']} in {total_time:.2f}s")
            print(f"Step timings: {step_times}")
            
            if status['state'] == 'failed':
                print(f"Error: {status.get('error')}")
            
            return status
        
        await asyncio.sleep(0.5)
```

This troubleshooting guide covers the most common issues encountered when working with the MultiAgents Framework and provides practical solutions for diagnosing and resolving them.