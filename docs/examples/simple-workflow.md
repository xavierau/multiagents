# Simple Workflow Example

**File**: `examples/simple_workflow.py`

This example demonstrates the fundamental concepts of the MultiAgents Framework through a basic data processing workflow.

## Purpose

Learn the core framework concepts:
- Creating workers with decorators
- Building workflows with sequential steps
- Framework component setup and lifecycle
- Basic monitoring and result handling

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                    SIMPLE WORKFLOW ARCHITECTURE                    │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  Input: "hello world"                                              │
│       │                                                             │
│       ▼                                                             │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐ │
│  │  validate_data  │───►│  process_data   │───►│  save_result    │ │
│  │                 │    │                 │    │                 │ │
│  │ • Validate      │    │ • Transform     │    │ • Store         │ │
│  │ • Check length  │    │ • Uppercase     │    │ • Generate ID   │ │
│  │ • Return status │    │ • Replace spaces│    │ • Return saved  │ │
│  └─────────────────┘    └─────────────────┘    └─────────────────┘ │
│           │                       │                       │         │
│           ▼                       ▼                       ▼         │
│  Result:                 Result:                 Result:             │
│  {                       {                       {                   │
│    "data": "hello world"   "original": "hello"    "result": "HELLO"  │
│    "status": "validated"   "processed": "HELLO"   "saved_id": "123"  │
│    "length": 11           "status": "processed"   "status": "saved"   │
│  }                       }                       }                   │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

## Key Components

### Workers

#### 1. Data Validation Worker
```python
@worker("validate_data")
async def validate_data_worker(context):
    """Validate input data."""
    data = context.get("data", "")
    
    if not data:
        raise ValueError("No data provided")
    
    if not isinstance(data, str) or len(data) < 3:
        raise ValueError("Data must be a string with at least 3 characters")
    
    return {
        "data": data,
        "status": "validated", 
        "length": len(data)
    }
```

**Purpose**: Ensures input data meets business requirements
**Input**: Raw string data
**Output**: Validated data with metadata

#### 2. Data Processing Worker
```python
@worker("process_data")
async def process_data_worker(context):
    """Process the validated data."""
    data = context["data"]  # From previous step
    
    # Simulate processing
    processed = data.upper().replace(" ", "_")
    
    return {
        "original": data,
        "processed": processed,
        "status": "processed"
    }
```

**Purpose**: Transforms data according to business logic
**Input**: Validated data
**Output**: Original and processed data

#### 3. Result Storage Worker
```python
@worker("save_result")
async def save_result_worker(context):
    """Save the final result."""
    result = context["processed"]  # From previous step
    
    # Simulate saving to database
    saved_id = f"SAVED_{hash(result) % 10000}"
    
    return {
        "result": result,
        "saved_id": saved_id,
        "status": "saved"
    }
```

**Purpose**: Persists processed data
**Input**: Processed data
**Output**: Storage confirmation with ID

### Workflow Definition

```python
def create_simple_workflow():
    """Create a basic data processing workflow."""
    return (WorkflowBuilder("data_processing")
        .add_step("validate", "validate_data")
        .add_step("process", "process_data")
        .add_step("save", "save_result")
        .build())
```

**Sequential Flow**: validate → process → save
**No Branching**: Linear execution path
**No Compensations**: Simple success/failure handling

## Code Walkthrough

### 1. Framework Setup

```python
async def main():
    print("🚀 Running Simple Workflow")
    
    # Create workflow definition
    workflow = create_simple_workflow()
    
    # Create framework components with automatic monitoring
    event_bus, worker_manager, orchestrator = await create_simple_framework(workflow)
```

The `create_simple_framework()` factory function creates all necessary components:
- **Event Bus**: Redis-based communication
- **Worker Manager**: Worker lifecycle management
- **Orchestrator**: Workflow execution engine
- **Monitoring**: Automatic observability setup

### 2. Component Startup

```python
try:
    # Start the framework components
    await event_bus.start()        # Connect to Redis
    
    # Register workers with manager
    worker_manager.register(validate_data_worker)
    worker_manager.register(process_data_worker)
    worker_manager.register(save_result_worker)
    
    await worker_manager.start()   # Start listening for commands
    await orchestrator.start()     # Start workflow engine
```

**Startup Sequence**:
1. Event bus connects to Redis
2. Workers registered with manager
3. Worker manager starts command listening
4. Orchestrator starts workflow processing

### 3. Workflow Execution

```python
    # Execute workflow with initial data
    print("📊 Executing workflow...")
    transaction_id = await orchestrator.execute_workflow(
        "data_processing",
        {"data": "hello world"}
    )
    
    print(f"✓ Workflow started with transaction ID: {transaction_id}")
```

**Execution Process**:
1. Orchestrator creates workflow instance
2. Generates unique transaction ID
3. Creates first CommandEvent
4. Publishes event to event bus

### 4. Progress Monitoring

```python
    # Monitor workflow progress
    while True:
        status = await orchestrator.get_status(transaction_id)
        print(f"State: {status['state']}, Step: {status['current_step']}")
        
        if status['state'] in {"completed", "failed"}:
            print(f"✅ Final state: {status['state']}")
            if status['step_results']:
                print("📋 Results:")
                for step, result in status['step_results'].items():
                    print(f"  {step}: {result}")
            break
            
        await asyncio.sleep(1)
```

**Monitoring Loop**:
1. Polls orchestrator for status
2. Displays current state and step
3. Exits when workflow completes
4. Shows final results

### 5. Graceful Shutdown

```python
finally:
    # Cleanup resources
    await worker_manager.stop()
    await orchestrator.stop()
    await event_bus.stop()
```

**Cleanup Process**:
1. Stop worker manager (no new commands)
2. Stop orchestrator (finish current workflows)
3. Stop event bus (close Redis connections)

## Expected Output

```
🚀 Running Simple Workflow
📊 Executing workflow...
✓ Workflow started with transaction ID: TX-20240103-123456-abc123
State: running, Step: validate
State: running, Step: process
State: running, Step: save
✅ Final state: completed
📋 Results:
  validate: {'data': 'hello world', 'status': 'validated', 'length': 11}
  process: {'original': 'hello world', 'processed': 'HELLO_WORLD', 'status': 'processed'}
  save: {'result': 'HELLO_WORLD', 'saved_id': 'SAVED_1234', 'status': 'saved'}
```

## Configuration Options

### Custom Input Data

```python
# Try different inputs
test_cases = [
    {"data": "hello world"},           # Normal case
    {"data": "hi"},                    # Minimum length
    {"data": ""},                      # Invalid: empty
    {"data": None},                    # Invalid: not string
    {"data": "a" * 1000}              # Large input
]

for test_case in test_cases:
    transaction_id = await orchestrator.execute_workflow(
        "data_processing", 
        test_case
    )
    # Monitor results...
```

### Custom Processing Logic

```python
@worker("process_data")
async def custom_process_data_worker(context):
    """Custom processing logic."""
    data = context["data"]
    
    # Different processing options
    processing_type = context.get("processing_type", "uppercase")
    
    if processing_type == "uppercase":
        processed = data.upper()
    elif processing_type == "lowercase":
        processed = data.lower()
    elif processing_type == "reverse":
        processed = data[::-1]
    else:
        processed = data
    
    return {
        "original": data,
        "processed": processed,
        "processing_type": processing_type,
        "status": "processed"
    }
```

### Monitoring Configuration

```python
# Custom monitoring setup
from multiagents.monitoring import MonitoringConfig

config = MonitoringConfig({
    "logging": {
        "level": "DEBUG",  # More verbose logging
        "file_path": "./logs/simple_workflow.log"
    },
    "event_monitoring": {
        "enabled": True,
        "trace_retention_hours": 1  # Keep traces for 1 hour
    }
})

logger = config.create_logger()
# Use logger in framework setup...
```

## Error Scenarios

### Validation Failure

```python
# Test validation error
transaction_id = await orchestrator.execute_workflow(
    "data_processing",
    {"data": ""}  # Empty string - will fail validation
)

# Expected outcome: workflow fails at validation step
# Error is logged and workflow state becomes "failed"
```

### Processing Failure

```python
@worker("process_data")
async def failing_process_worker(context):
    """Worker that demonstrates error handling."""
    data = context["data"]
    
    if "error" in data.lower():
        raise ValueError("Processing failed for test data")
    
    return {"processed": data.upper()}

# Test with error-triggering input
transaction_id = await orchestrator.execute_workflow(
    "data_processing",
    {"data": "hello error world"}
)
```

## Extensions and Modifications

### Adding Conditional Logic

```python
def create_conditional_workflow():
    """Workflow with conditional processing."""
    return (WorkflowBuilder("conditional_processing")
        .add_step("validate", "validate_data")
        .add_conditional_step(
            "special_process", 
            "special_processor",
            condition=lambda ctx: len(ctx.get("data", "")) > 10
        )
        .add_step("save", "save_result")
        .build())
```

### Adding Parallel Processing

```python
def create_parallel_workflow():
    """Workflow with parallel steps."""
    return (WorkflowBuilder("parallel_processing")
        .add_step("validate", "validate_data")
        .add_parallel_steps([
            {"name": "process_upper", "worker_name": "uppercase_processor"},
            {"name": "process_lower", "worker_name": "lowercase_processor"}
        ])
        .add_step("combine", "result_combiner")
        .build())
```

### Adding Compensation

```python
def create_compensated_workflow():
    """Workflow with compensation pattern."""
    return (WorkflowBuilder("compensated_processing")
        .add_step("validate", "validate_data")
        .add_step("process", "process_data", compensation="undo_processing")
        .add_step("save", "save_result", compensation="delete_saved")
        .build())
```

## Common Issues

### Redis Connection Error
```
ConnectionError: Error 61 connecting to localhost:6379. Connection refused.
```
**Solution**: Start Redis server
```bash
redis-server
# or
brew services start redis
```

### Import Error
```
ModuleNotFoundError: No module named 'multiagents'
```
**Solution**: Run from project root or adjust Python path
```python
import sys
sys.path.insert(0, '.')
```

### Worker Not Found
```
ValueError: Worker 'validate_data' not found
```
**Solution**: Ensure worker is registered before starting
```python
worker_manager.register(validate_data_worker)
await worker_manager.start()
```

## Learning Objectives

After completing this example, you should understand:

1. **Worker Creation** - How to create and configure workers
2. **Workflow Building** - How to define sequential workflows
3. **Framework Setup** - How to initialize and start components
4. **Event Flow** - How events flow between components
5. **Monitoring** - How to track workflow progress
6. **Error Handling** - How errors are propagated and handled
7. **Resource Management** - How to properly shutdown components

## Next Steps

1. **Modify the Example** - Change worker logic and see the effects
2. **Add Error Handling** - Implement custom error scenarios
3. **Try Different Inputs** - Test with various data types and sizes
4. **Add Monitoring** - Implement custom logging and metrics
5. **Move to Complex Examples** - Explore the e-commerce order processing example