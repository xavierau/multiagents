# Worker Development Guide

This comprehensive guide covers everything you need to know about developing workers for the MultiAgents Framework.

## Table of Contents

- [Worker Fundamentals](#worker-fundamentals)
- [Creating Your First Worker](#creating-your-first-worker)
- [Advanced Worker Patterns](#advanced-worker-patterns)
- [DSPy Integration](#dspy-integration)
- [Error Handling](#error-handling)
- [Testing Workers](#testing-workers)
- [Performance Optimization](#performance-optimization)
- [Best Practices](#best-practices)

## Worker Fundamentals

### What is a Worker?

Workers are stateless, single-purpose functions that execute specific business logic within workflows. They are the building blocks of the MultiAgents Framework.

**Key Characteristics:**
- **Stateless**: No persistent state between executions
- **Single Purpose**: Each worker does one thing well
- **Async-First**: Designed for concurrent execution
- **Context-Driven**: Receive all data through context parameter
- **Result-Oriented**: Return data for subsequent steps

### Worker Lifecycle

```
┌─────────────────────────────────────────────────────────────────────┐
│                         WORKER LIFECYCLE                           │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  1. Registration                                                    │
│     ┌─────────────────────────────────────────────┐                │
│     │ @worker("my_worker")                        │                │
│     │ async def my_worker(context):               │                │
│     │     return {"result": "processed"}         │                │
│     │                                             │                │
│     │ worker_manager.register(my_worker)          │                │
│     └─────────────────────────────────────────────┘                │
│                           │                                         │
│                           ▼                                         │
│  2. Command Reception                                               │
│     ┌─────────────────────────────────────────────┐                │
│     │ • Worker Manager receives CommandEvent      │                │
│     │ • Routes to appropriate worker              │                │
│     │ • Validates input context                   │                │
│     └─────────────────────────────────────────────┘                │
│                           │                                         │
│                           ▼                                         │
│  3. Execution                                                       │
│     ┌─────────────────────────────────────────────┐                │
│     │ • Worker function called with context       │                │
│     │ • Business logic executed                   │                │
│     │ • Results generated                         │                │
│     │ • Monitoring data collected                 │                │
│     └─────────────────────────────────────────────┘                │
│                           │                                         │
│                           ▼                                         │
│  4. Result Publishing                                               │
│     ┌─────────────────────────────────────────────┐                │
│     │ • ResultEvent created with worker output    │                │
│     │ • Event published to event bus              │                │
│     │ • Performance metrics recorded              │                │
│     └─────────────────────────────────────────────┘                │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

## Creating Your First Worker

### Basic Worker Structure

```python
from multiagents import worker

@worker("my_first_worker")
async def my_first_worker(context):
    """
    A simple worker that processes input data.
    
    Args:
        context (Dict[str, Any]): Input context containing:
            - Original workflow input
            - Results from previous steps
            - Metadata (transaction_id, workflow_id, etc.)
    
    Returns:
        Dict[str, Any]: Worker results (merged into workflow context)
    """
    # Extract input data
    input_data = context.get("input_data", "")
    
    # Validate input
    if not input_data:
        raise ValueError("No input data provided")
    
    # Process data
    processed = input_data.upper().strip()
    
    # Return results
    return {
        "processed_data": processed,
        "processing_timestamp": datetime.utcnow().isoformat(),
        "original_length": len(input_data),
        "processed_length": len(processed)
    }
```

### Synchronous Workers

The framework supports both async and sync workers:

```python
@worker("sync_calculator")
def calculate_total(context):
    """Synchronous worker for CPU-intensive calculations."""
    items = context.get("items", [])
    
    # CPU-intensive calculation
    total = sum(item["price"] * item["quantity"] for item in items)
    tax = total * 0.08  # 8% tax
    
    return {
        "subtotal": total,
        "tax": tax,
        "total": total + tax
    }
```

### Worker Configuration

```python
from multiagents.worker_sdk.base_worker import WorkerConfig

# Configure worker behavior
config = WorkerConfig(
    timeout_seconds=60,              # Maximum execution time
    retry_count=3,                   # Number of retries on failure
    retry_delay_seconds=1.0,         # Initial delay between retries
    retry_backoff_factor=2.0,        # Exponential backoff multiplier
    max_retry_delay_seconds=30.0,    # Maximum delay between retries
    enable_monitoring=True,          # Enable performance monitoring
    tags=["payment", "critical"]     # Worker tags for organization
)

@worker("configured_worker", config=config)
async def configured_worker(context):
    # Implementation with custom configuration
    pass
```

## Advanced Worker Patterns

### 1. Data Validation Worker

```python
from pydantic import BaseModel, ValidationError
from typing import List, Optional

class OrderItem(BaseModel):
    product_id: str
    quantity: int
    price: float

class Order(BaseModel):
    order_id: str
    customer_id: str
    items: List[OrderItem]
    total: Optional[float] = None

@worker("validate_order")
async def validate_order_worker(context):
    """Validate order data using Pydantic models."""
    try:
        # Parse and validate order
        order_data = context.get("order", {})
        order = Order(**order_data)
        
        # Additional business validation
        if not order.items:
            raise ValueError("Order must contain at least one item")
        
        # Calculate and validate total
        calculated_total = sum(item.price * item.quantity for item in order.items)
        if order.total and abs(order.total - calculated_total) > 0.01:
            raise ValueError("Order total doesn't match item prices")
        
        # Return validated order
        return {
            "validated_order": order.dict(),
            "calculated_total": calculated_total,
            "item_count": len(order.items),
            "validation_status": "passed"
        }
        
    except ValidationError as e:
        return {
            "validation_status": "failed",
            "validation_errors": [str(err) for err in e.errors],
            "error_type": "validation_error"
        }
    except ValueError as e:
        return {
            "validation_status": "failed",
            "validation_errors": [str(e)],
            "error_type": "business_rule_error"
        }
```

### 2. External API Integration Worker

```python
import aiohttp
import asyncio
from typing import Optional

@worker("payment_processor")
async def payment_processor_worker(context):
    """Process payment through external payment gateway."""
    
    # Extract payment information
    order = context["validated_order"]
    payment_info = context["payment_info"]
    total = context["calculated_total"]
    
    async with aiohttp.ClientSession() as session:
        try:
            # Call payment gateway
            payment_request = {
                "amount": total,
                "currency": "USD",
                "payment_method": payment_info["method"],
                "card_token": payment_info["card_token"],
                "customer_id": order["customer_id"],
                "order_id": order["order_id"]
            }
            
            async with session.post(
                "https://api.paymentgateway.com/v1/charges",
                json=payment_request,
                headers={"Authorization": f"Bearer {get_api_key()}"},
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                
                if response.status == 200:
                    payment_result = await response.json()
                    return {
                        "payment_id": payment_result["id"],
                        "payment_status": "charged",
                        "transaction_fee": payment_result["fee"],
                        "gateway_response": payment_result
                    }
                else:
                    error_data = await response.json()
                    return {
                        "payment_status": "failed",
                        "error_code": error_data.get("error_code"),
                        "error_message": error_data.get("message"),
                        "retry_recommended": response.status in [429, 503]
                    }
                    
        except asyncio.TimeoutError:
            return {
                "payment_status": "failed",
                "error_message": "Payment gateway timeout",
                "error_type": "timeout",
                "retry_recommended": True
            }
        except aiohttp.ClientError as e:
            return {
                "payment_status": "failed",
                "error_message": f"Network error: {str(e)}",
                "error_type": "network_error",
                "retry_recommended": True
            }
```

### 3. Parallel Processing Worker

```python
@worker("parallel_data_processor")
async def parallel_data_processor_worker(context):
    """Process multiple data items in parallel."""
    
    items = context.get("items", [])
    max_concurrency = context.get("max_concurrency", 10)
    
    if not items:
        return {"processed_items": [], "error_count": 0}
    
    # Create semaphore to limit concurrency
    semaphore = asyncio.Semaphore(max_concurrency)
    
    async def process_single_item(item):
        async with semaphore:
            try:
                # Simulate processing time
                await asyncio.sleep(0.1)
                
                # Process item (example: data enrichment)
                processed = {
                    "original": item,
                    "processed_at": datetime.utcnow().isoformat(),
                    "status": "processed",
                    "hash": hashlib.md5(str(item).encode()).hexdigest()
                }
                
                return {"success": True, "data": processed}
                
            except Exception as e:
                return {
                    "success": False, 
                    "error": str(e), 
                    "original": item
                }
    
    # Process all items concurrently
    tasks = [process_single_item(item) for item in items]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Separate successful and failed results
    processed_items = []
    errors = []
    
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            errors.append({
                "item_index": i,
                "item": items[i],
                "error": str(result)
            })
        elif result["success"]:
            processed_items.append(result["data"])
        else:
            errors.append({
                "item_index": i,
                "item": result["original"],
                "error": result["error"]
            })
    
    return {
        "processed_items": processed_items,
        "successful_count": len(processed_items),
        "error_count": len(errors),
        "errors": errors,
        "total_items": len(items)
    }
```

### 4. Conditional Logic Worker

```python
@worker("order_routing")
async def order_routing_worker(context):
    """Route order based on various conditions."""
    
    order = context["validated_order"]
    customer_tier = context.get("customer_tier", "standard")
    order_value = context["calculated_total"]
    
    # Determine routing based on business rules
    routing_decision = {
        "order_id": order["order_id"],
        "routing_timestamp": datetime.utcnow().isoformat()
    }
    
    # High-value order routing
    if order_value >= 1000:
        routing_decision.update({
            "route": "high_value",
            "priority": "high",
            "approval_required": True,
            "fulfillment_center": "premium_warehouse",
            "shipping_method": "express"
        })
    
    # Premium customer routing
    elif customer_tier in ["premium", "vip"]:
        routing_decision.update({
            "route": "premium_customer", 
            "priority": "high",
            "approval_required": False,
            "fulfillment_center": "premium_warehouse",
            "shipping_method": "expedited"
        })
    
    # Bulk order routing
    elif len(order["items"]) > 10:
        routing_decision.update({
            "route": "bulk_order",
            "priority": "medium", 
            "approval_required": False,
            "fulfillment_center": "bulk_warehouse",
            "shipping_method": "standard"
        })
    
    # Standard routing
    else:
        routing_decision.update({
            "route": "standard",
            "priority": "normal",
            "approval_required": False,
            "fulfillment_center": "standard_warehouse", 
            "shipping_method": "standard"
        })
    
    # Add additional routing metadata
    routing_decision["estimated_processing_time"] = (
        "24_hours" if routing_decision["approval_required"] 
        else "2_hours"
    )
    
    return routing_decision
```

## DSPy Integration

### Basic DSPy Worker

```python
from multiagents import dspy_worker

@dspy_worker("content_generator")
async def content_generator_worker(context):
    """Generate content using DSPy LLM integration."""
    
    # Context automatically passed to DSPy
    # Framework handles LLM interaction
    return context  # DSPy framework processes this
```

### Custom DSPy Worker with Signature

```python
@dspy_worker("email_composer", signature="customer_name, order_details, template_type -> email_subject, email_body")
async def email_composer_worker(context):
    """Compose personalized emails using DSPy."""
    
    # Extract required parameters
    customer_name = context.get("customer_name", "Valued Customer")
    order_details = context.get("order_details", "")
    template_type = context.get("template_type", "confirmation")
    
    # DSPy will use this context to generate structured output
    # matching the signature: email_subject, email_body
    return {
        "customer_name": customer_name,
        "order_details": order_details,
        "template_type": template_type,
        "personalization_data": {
            "order_value": context.get("calculated_total", 0),
            "customer_tier": context.get("customer_tier", "standard"),
            "estimated_delivery": context.get("estimated_delivery", "3-5 business days")
        }
    }
```

### Advanced DSPy Worker with Post-Processing

```python
@dspy_worker("sentiment_analyzer", signature="customer_feedback -> sentiment, confidence, key_topics")
async def sentiment_analyzer_worker(context):
    """Analyze customer sentiment with post-processing."""
    
    feedback_text = context.get("customer_feedback", "")
    
    if not feedback_text:
        return {
            "sentiment": "neutral",
            "confidence": 0.0,
            "key_topics": [],
            "analysis_status": "no_feedback_provided"
        }
    
    # Prepare context for DSPy
    dspy_context = {
        "customer_feedback": feedback_text,
        "analysis_type": "detailed",
        "include_topics": True
    }
    
    # DSPy will process this and return structured results
    # Framework automatically handles the LLM interaction
    return dspy_context

# Post-processing hook (optional)
@sentiment_analyzer_worker.post_process
async def post_process_sentiment(dspy_result, original_context):
    """Post-process DSPy results for additional validation."""
    
    # Validate confidence score
    confidence = dspy_result.get("confidence", 0.0)
    if confidence < 0.5:
        dspy_result["requires_human_review"] = True
    
    # Extract and categorize topics
    topics = dspy_result.get("key_topics", [])
    dspy_result["topic_categories"] = categorize_topics(topics)
    
    # Add metadata
    dspy_result.update({
        "analysis_timestamp": datetime.utcnow().isoformat(),
        "model_version": "dspy-v2.1",
        "processing_time_ms": (datetime.utcnow() - original_context.get("start_time", datetime.utcnow())).total_seconds() * 1000
    })
    
    return dspy_result
```

## Error Handling

### Graceful Error Handling

```python
@worker("robust_data_processor")
async def robust_data_processor_worker(context):
    """Worker with comprehensive error handling."""
    
    try:
        # Validate required inputs
        required_fields = ["data", "format", "output_type"]
        missing_fields = [field for field in required_fields if field not in context]
        
        if missing_fields:
            return {
                "status": "validation_error",
                "error_type": "missing_required_fields",
                "missing_fields": missing_fields,
                "retry_recommended": False
            }
        
        data = context["data"]
        format_type = context["format"]
        output_type = context["output_type"]
        
        # Process data based on format
        if format_type == "json":
            processed = await process_json_data(data)
        elif format_type == "csv":
            processed = await process_csv_data(data) 
        elif format_type == "xml":
            processed = await process_xml_data(data)
        else:
            return {
                "status": "error",
                "error_type": "unsupported_format",
                "supported_formats": ["json", "csv", "xml"],
                "retry_recommended": False
            }
        
        # Convert to output format
        output = await convert_to_format(processed, output_type)
        
        return {
            "status": "success",
            "processed_data": output,
            "input_size": len(str(data)),
            "output_size": len(str(output)),
            "processing_stats": {
                "records_processed": len(processed),
                "format_conversion": f"{format_type} -> {output_type}"
            }
        }
        
    except ValidationError as e:
        # Recoverable validation errors
        return {
            "status": "validation_error",
            "error_type": "data_validation",
            "validation_errors": [str(err) for err in e.errors],
            "retry_recommended": False
        }
        
    except TimeoutError:
        # Recoverable timeout - might succeed on retry
        return {
            "status": "error",
            "error_type": "timeout",
            "error_message": "Processing timeout exceeded",
            "retry_recommended": True
        }
        
    except ConnectionError as e:
        # Recoverable network errors
        return {
            "status": "error",
            "error_type": "connection_error",
            "error_message": f"Network error: {str(e)}",
            "retry_recommended": True
        }
        
    except Exception as e:
        # Unrecoverable errors - log and raise
        await logger.error(
            "Unexpected error in data processor",
            error=str(e),
            error_type=type(e).__name__,
            context_keys=list(context.keys()),
            transaction_id=context.get("transaction_id")
        )
        
        # Re-raise to trigger framework error handling
        raise WorkerExecutionError(f"Data processing failed: {str(e)}")
```

### Compensation Workers

```python
@worker("reserve_inventory")
async def reserve_inventory_worker(context):
    """Reserve inventory items for an order."""
    
    items = context["validated_order"]["items"]
    reservation_id = f"RES-{uuid.uuid4()}"
    
    try:
        reserved_items = []
        for item in items:
            # Check availability
            available = await inventory_service.check_availability(
                item["product_id"], 
                item["quantity"]
            )
            
            if not available:
                # If we can't reserve all items, we need to compensate
                # Release already reserved items
                for reserved_item in reserved_items:
                    await inventory_service.release(reserved_item["reservation_id"])
                
                return {
                    "reservation_status": "failed",
                    "error": f"Insufficient inventory for {item['product_id']}",
                    "retry_recommended": False
                }
            
            # Reserve the item
            item_reservation = await inventory_service.reserve(
                item["product_id"],
                item["quantity"],
                reservation_id
            )
            reserved_items.append(item_reservation)
        
        return {
            "reservation_status": "success",
            "reservation_id": reservation_id,
            "reserved_items": reserved_items,
            "total_items": len(reserved_items)
        }
        
    except Exception as e:
        # Clean up any partial reservations
        for reserved_item in reserved_items:
            try:
                await inventory_service.release(reserved_item["reservation_id"])
            except Exception:
                pass  # Log but don't fail compensation
        
        raise WorkerExecutionError(f"Inventory reservation failed: {str(e)}")

@worker("release_inventory") 
async def release_inventory_worker(context):
    """Compensation worker: release reserved inventory."""
    
    reservation_id = context.get("reservation_id")
    
    if not reservation_id:
        # Nothing to compensate
        return {"compensation_status": "no_action_needed"}
    
    try:
        await inventory_service.release_reservation(reservation_id)
        return {
            "compensation_status": "success",
            "released_reservation_id": reservation_id
        }
        
    except Exception as e:
        # Log compensation failure but don't raise
        # Compensation failures should not stop other compensations
        await logger.error(
            "Failed to release inventory reservation",
            reservation_id=reservation_id,
            error=str(e),
            transaction_id=context.get("transaction_id")
        )
        
        return {
            "compensation_status": "failed",
            "error": str(e),
            "reservation_id": reservation_id
        }
```

## Testing Workers

### Unit Testing

```python
import pytest
from unittest.mock import AsyncMock, patch

class TestDataProcessor:
    """Unit tests for data processor worker."""
    
    @pytest.mark.asyncio
    async def test_successful_processing(self):
        """Test successful data processing."""
        context = {
            "data": [{"id": 1, "value": "test"}],
            "format": "json",
            "output_type": "csv"
        }
        
        result = await robust_data_processor_worker(context)
        
        assert result["status"] == "success"
        assert "processed_data" in result
        assert result["processing_stats"]["records_processed"] == 1
    
    @pytest.mark.asyncio
    async def test_missing_required_fields(self):
        """Test handling of missing required fields."""
        context = {"data": []}  # Missing format and output_type
        
        result = await robust_data_processor_worker(context)
        
        assert result["status"] == "validation_error"
        assert "missing_fields" in result
        assert "format" in result["missing_fields"]
        assert "output_type" in result["missing_fields"]
        assert result["retry_recommended"] is False
    
    @pytest.mark.asyncio
    async def test_unsupported_format(self):
        """Test handling of unsupported format."""
        context = {
            "data": [{"id": 1}],
            "format": "yaml",  # Unsupported
            "output_type": "json"
        }
        
        result = await robust_data_processor_worker(context)
        
        assert result["status"] == "error"
        assert result["error_type"] == "unsupported_format"
        assert "supported_formats" in result
    
    @pytest.mark.asyncio
    @patch('your_module.process_json_data')
    async def test_timeout_handling(self, mock_process):
        """Test timeout error handling."""
        mock_process.side_effect = TimeoutError("Processing timeout")
        
        context = {
            "data": [{"id": 1}],
            "format": "json", 
            "output_type": "csv"
        }
        
        result = await robust_data_processor_worker(context)
        
        assert result["status"] == "error"
        assert result["error_type"] == "timeout"
        assert result["retry_recommended"] is True
```

### Integration Testing

```python
@pytest.mark.asyncio
async def test_worker_in_workflow():
    """Test worker within a complete workflow."""
    from multiagents.core.factory import create_simple_framework
    from multiagents.orchestrator.workflow import WorkflowBuilder
    
    # Create test workflow
    workflow = (WorkflowBuilder("test_data_processing")
        .add_step("process", "robust_data_processor")
        .build())
    
    # Set up framework
    event_bus, worker_manager, orchestrator = await create_simple_framework(workflow)
    
    try:
        # Start components
        await event_bus.start()
        worker_manager.register(robust_data_processor_worker)
        await worker_manager.start()
        await orchestrator.start()
        
        # Execute workflow
        context = {
            "data": [{"id": 1, "value": "test"}],
            "format": "json",
            "output_type": "csv"
        }
        
        transaction_id = await orchestrator.execute_workflow(
            "test_data_processing", 
            context
        )
        
        # Wait for completion
        while True:
            status = await orchestrator.get_status(transaction_id)
            if status["state"] in ["completed", "failed"]:
                break
            await asyncio.sleep(0.1)
        
        # Verify results
        assert status["state"] == "completed"
        assert "process" in status["step_results"]
        process_result = status["step_results"]["process"]
        assert process_result["status"] == "success"
        
    finally:
        # Cleanup
        await worker_manager.stop()
        await orchestrator.stop()
        await event_bus.stop()
```

### Load Testing

```python
@pytest.mark.asyncio
async def test_worker_load():
    """Test worker under load."""
    import asyncio
    from concurrent.futures import ThreadPoolExecutor
    
    # Create load test context
    context = {
        "data": [{"id": i, "value": f"test_{i}"} for i in range(1000)],
        "format": "json",
        "output_type": "csv"
    }
    
    # Run multiple workers concurrently
    start_time = time.time()
    
    tasks = [
        robust_data_processor_worker(context) 
        for _ in range(10)
    ]
    
    results = await asyncio.gather(*tasks)
    
    end_time = time.time()
    duration = end_time - start_time
    
    # Verify all succeeded
    for result in results:
        assert result["status"] == "success"
    
    # Performance assertions
    assert duration < 5.0  # Should complete within 5 seconds
    
    throughput = len(results) / duration
    assert throughput > 2.0  # Should process at least 2 requests/second
```

## Performance Optimization

### Async Best Practices

```python
# ❌ Bad: Blocking operations
@worker("slow_worker")
async def slow_worker_bad(context):
    time.sleep(5)  # Blocks the event loop!
    return {"result": "done"}

# ✅ Good: Async operations
@worker("fast_worker")
async def fast_worker_good(context):
    await asyncio.sleep(5)  # Non-blocking
    return {"result": "done"}

# ✅ Good: Using executors for CPU-bound tasks
@worker("cpu_intensive_worker")
async def cpu_intensive_worker(context):
    data = context["large_dataset"]
    
    # Run CPU-intensive work in thread pool
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(
        None,  # Use default thread pool
        process_large_dataset,  # CPU-bound function
        data
    )
    
    return {"processed": result}
```

### Connection Pooling

```python
# ✅ Good: Reuse connections
class DatabaseWorker:
    def __init__(self):
        self.connection_pool = None
    
    async def initialize(self):
        """Initialize connection pool once."""
        self.connection_pool = await asyncpg.create_pool(
            "postgresql://user:pass@localhost/db",
            min_size=5,
            max_size=20
        )
    
    @worker("database_worker")
    async def process_data(self, context):
        """Use pooled connections."""
        async with self.connection_pool.acquire() as conn:
            result = await conn.fetch("SELECT * FROM table WHERE id = $1", context["id"])
            return {"data": [dict(row) for row in result]}

# Initialize once
db_worker = DatabaseWorker()
await db_worker.initialize()
```

### Caching

```python
from functools import lru_cache
import redis.asyncio as redis

class CachedWorker:
    def __init__(self):
        self.redis = redis.from_url("redis://localhost")
        self.cache = {}
    
    @worker("cached_api_worker")
    async def fetch_data(self, context):
        """Worker with Redis caching."""
        key = context["api_key"]
        cache_key = f"api_data:{key}"
        
        # Try cache first
        cached_result = await self.redis.get(cache_key)
        if cached_result:
            return json.loads(cached_result)
        
        # Fetch from API
        async with aiohttp.ClientSession() as session:
            async with session.get(f"https://api.example.com/data/{key}") as response:
                data = await response.json()
        
        # Cache for 1 hour
        await self.redis.setex(cache_key, 3600, json.dumps(data))
        
        return data
    
    @staticmethod
    @lru_cache(maxsize=1000)
    def expensive_calculation(value: str) -> str:
        """In-memory cache for expensive pure functions."""
        # Expensive computation here
        return value.upper()[::-1]  # Simplified example
```

## Best Practices

### 1. Design Principles

**Single Responsibility**
```python
# ✅ Good: Single purpose
@worker("email_validator")
async def validate_email(context):
    """Only validates email addresses."""
    pass

@worker("email_sender") 
async def send_email(context):
    """Only sends emails."""
    pass

# ❌ Bad: Multiple responsibilities
@worker("email_handler")
async def handle_email(context):
    """Validates AND sends emails - too much responsibility."""
    pass
```

**Stateless Design**
```python
# ✅ Good: Stateless
@worker("order_processor")
async def process_order(context):
    """All data comes from context."""
    order = context["order"]
    return process(order)

# ❌ Bad: Stateful
class OrderProcessor:
    def __init__(self):
        self.last_order = None  # State between calls!
    
    @worker("order_processor")
    async def process_order(self, context):
        self.last_order = context["order"]  # Storing state
        return process(self.last_order)
```

### 2. Error Handling

**Graceful Degradation**
```python
@worker("resilient_worker")
async def resilient_worker(context):
    """Worker with graceful degradation."""
    primary_result = None
    fallback_result = None
    
    try:
        # Try primary method
        primary_result = await primary_service.process(context["data"])
    except Exception as e:
        logger.warning(f"Primary service failed: {e}")
        
        try:
            # Fallback to secondary method
            fallback_result = await fallback_service.process(context["data"])
        except Exception as e2:
            logger.error(f"Fallback service also failed: {e2}")
            # Return partial result or error indication
            return {
                "status": "degraded",
                "error": "Both primary and fallback services failed",
                "retry_recommended": True
            }
    
    return {
        "status": "success",
        "result": primary_result or fallback_result,
        "method_used": "primary" if primary_result else "fallback"
    }
```

### 3. Monitoring Integration

```python
@worker("monitored_worker")
async def monitored_worker(context):
    """Worker with comprehensive monitoring."""
    start_time = time.time()
    
    try:
        # Business logic
        result = await process_data(context)
        
        # Success metrics
        await metrics.increment("worker.success", tags={"worker": "monitored_worker"})
        
        return result
        
    except Exception as e:
        # Error metrics
        await metrics.increment("worker.error", tags={
            "worker": "monitored_worker",
            "error_type": type(e).__name__
        })
        
        # Re-raise for framework handling
        raise
        
    finally:
        # Duration metrics
        duration = time.time() - start_time
        await metrics.timing("worker.duration", duration, tags={"worker": "monitored_worker"})
```

### 4. Documentation

```python
@worker("well_documented_worker")
async def well_documented_worker(context):
    """
    Process customer orders with validation and enrichment.
    
    This worker performs comprehensive order processing including:
    1. Order validation against business rules
    2. Customer data enrichment from CRM
    3. Inventory availability checking
    4. Price calculation with discounts
    
    Args:
        context (Dict[str, Any]): Required context containing:
            - order (Dict): Raw order data with items, customer_id
            - customer_tier (str): Customer tier for pricing ("standard", "premium", "vip")
            - promotion_code (Optional[str]): Discount code to apply
            
    Returns:
        Dict[str, Any]: Processing results containing:
            - validated_order (Dict): Cleaned and validated order
            - enriched_customer (Dict): Customer data from CRM
            - final_price (float): Price after discounts
            - inventory_status (str): "available", "partial", or "unavailable"
            - processing_metadata (Dict): Timestamps and processing info
            
    Raises:
        ValidationError: Invalid order data or business rule violations
        CustomerNotFoundError: Customer ID not found in CRM
        InventoryUnavailableError: Insufficient inventory for order
        
    Example:
        context = {
            "order": {
                "customer_id": "CUST-123",
                "items": [{"product_id": "PROD-456", "quantity": 2}],
                "total": 99.99
            },
            "customer_tier": "premium",
            "promotion_code": "SAVE10"
        }
        
        result = await well_documented_worker(context)
        # Returns validated order with enriched customer data
    """
    # Implementation here...
    pass
```

This comprehensive guide provides everything you need to build robust, scalable, and maintainable workers for the MultiAgents Framework!