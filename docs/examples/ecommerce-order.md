# E-commerce Order Processing Example

**Files**: `examples/ecommerce_order/`

This comprehensive example demonstrates a real-world e-commerce order processing workflow with advanced patterns including compensations, DSPy integration, and comprehensive monitoring.

## Purpose

Learn advanced framework patterns:
- Complex multi-step workflows
- Saga pattern with compensations
- DSPy-powered LLM workers
- Production-ready monitoring
- Error handling and recovery
- Real-world business logic

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                 E-COMMERCE ORDER PROCESSING FLOW                   │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  Order Input                                                        │
│       │                                                             │
│       ▼                                                             │
│  ┌─────────────────┐                                               │
│  │ Validate Order  │────┐ (validation fails)                      │
│  │                 │    │                                          │
│  │ • Check format  │    ▼                                          │
│  │ • Validate data │   ❌ End (Failed)                             │
│  │ • Business rules│                                               │
│  └─────────────────┘                                               │
│           │ (valid)                                                 │
│           ▼                                                         │
│  ┌─────────────────┐    ┌─────────────────┐                       │
│  │ Check Inventory │────┤ Release         │ (compensation)          │
│  │                 │    │ Inventory       │                       │
│  │ • Reserve items │    │                 │                       │
│  │ • Check stock   │    │ • Undo reserve  │                       │
│  │ • Generate res# │    │ • Update stock  │                       │
│  └─────────────────┘    └─────────────────┘                       │
│           │                       ▲                                │
│           ▼                       │ (if later step fails)          │
│  ┌─────────────────┐    ┌─────────────────┐                       │
│  │ Process Payment │────┤ Refund Payment  │ (compensation)          │
│  │                 │    │                 │                       │
│  │ • Charge card   │    │ • Reverse charge│                       │
│  │ • Handle gateway│    │ • Update records│                       │
│  │ • Record txn    │    │ • Notify customer│                      │
│  └─────────────────┘    └─────────────────┘                       │
│           │                       ▲                                │
│           ▼                       │ (if later step fails)          │
│  ┌─────────────────┐              │                                │
│  │ Generate        │              │                                │
│  │ Confirmation    │──────────────┘                                │
│  │                 │                                               │
│  │ • DSPy LLM      │                                               │
│  │ • Personalized  │                                               │
│  │ • Email content │                                               │
│  └─────────────────┘                                               │
│           │                                                         │
│           ▼                                                         │
│  ┌─────────────────┐                                               │
│  │ Fulfill Order   │                                               │
│  │                 │                                               │
│  │ • Create shipment│                                              │
│  │ • Generate label │                                              │
│  │ • Update status │                                               │
│  └─────────────────┘                                               │
│           │                                                         │
│           ▼                                                         │
│  ┌─────────────────┐                                               │
│  │ Notify Customer │                                               │
│  │                 │                                               │
│  │ • Send email    │                                               │
│  │ • Update CRM    │                                               │
│  │ • Log completion│                                               │
│  └─────────────────┘                                               │
│           │                                                         │
│           ▼                                                         │
│      ✅ Success                                                     │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

## Key Components

### Project Structure

```
examples/ecommerce_order/
├── __init__.py
├── main.py              # Main execution entry point
├── workflow.py          # Workflow definitions
├── workers.py           # All worker implementations
├── diagram_demo.py      # Workflow visualization
└── generated_diagrams/  # Auto-generated workflow diagrams
    ├── ecommerce_workflow.mmd
    ├── ecommerce_architecture.mmd
    └── *.ascii.txt
```

### Workflow Definition

```python
def create_ecommerce_workflow():
    """Create the main e-commerce order processing workflow."""
    return (WorkflowBuilder("ecommerce_order_processing")
        # Core processing steps
        .add_step("validate_order", "validate_order")
        .add_step("check_inventory", "check_inventory", 
                 compensation="release_inventory")
        .add_step("process_payment", "process_payment", 
                 compensation="refund_payment")
        
        # DSPy-powered step
        .add_step("generate_confirmation", "generate_confirmation")
        
        # Fulfillment steps
        .add_step("fulfill_order", "fulfill_order")
        .add_step("notify_customer", "notify_customer")
        .build())
```

### Workers Deep Dive

#### 1. Order Validation Worker

```python
@worker("validate_order")
async def validate_order_worker(context):
    """Comprehensive order validation with business rules."""
    
    order = context.get("order", {})
    
    # Required field validation
    required_fields = ["id", "customer_id", "items", "total_amount"]
    missing_fields = [field for field in required_fields if not order.get(field)]
    
    if missing_fields:
        raise ValidationError(f"Missing required fields: {missing_fields}")
    
    # Business rule validation
    items = order.get("items", [])
    if not items:
        raise ValidationError("Order must contain at least one item")
    
    # Calculate and verify total
    calculated_total = sum(item["price"] * item["quantity"] for item in items)
    declared_total = order["total_amount"]
    
    if abs(calculated_total - declared_total) > 0.01:
        raise ValidationError(
            f"Total mismatch: calculated {calculated_total}, declared {declared_total}"
        )
    
    # Validate item details
    for i, item in enumerate(items):
        if item["quantity"] <= 0:
            raise ValidationError(f"Item {i}: quantity must be positive")
        if item["price"] <= 0:
            raise ValidationError(f"Item {i}: price must be positive")
        if not item.get("product_id"):
            raise ValidationError(f"Item {i}: missing product_id")
    
    return {
        "validated_order": order,
        "item_count": len(items),
        "total_amount": calculated_total,
        "validation_timestamp": datetime.utcnow().isoformat(),
        "validation_status": "passed"
    }
```

**Features**:
- Comprehensive field validation
- Business rule enforcement
- Financial calculation verification
- Detailed error reporting

#### 2. Inventory Management Worker

```python
@worker("check_inventory")
async def check_inventory_worker(context):
    """Check and reserve inventory with detailed tracking."""
    
    order = context["validated_order"]
    items = order["items"]
    reservation_id = f"RES-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}-{order['id']}"
    
    reserved_items = []
    total_reserved_value = 0
    
    try:
        for item in items:
            product_id = item["product_id"]
            quantity = item["quantity"]
            
            # Simulate inventory check (replace with real inventory service)
            available_stock = await get_available_stock(product_id)
            
            if available_stock < quantity:
                # Insufficient stock - release what we've reserved
                for reserved in reserved_items:
                    await release_reservation(reserved["reservation_id"])
                
                return {
                    "inventory_status": "insufficient",
                    "product_id": product_id,
                    "requested": quantity,
                    "available": available_stock,
                    "error": f"Insufficient stock for {product_id}"
                }
            
            # Reserve the inventory
            item_reservation = await reserve_inventory(product_id, quantity, reservation_id)
            reserved_items.append({
                "product_id": product_id,
                "quantity": quantity,
                "reservation_id": item_reservation["id"],
                "reserved_at": item_reservation["timestamp"]
            })
            
            total_reserved_value += item["price"] * quantity
        
        return {
            "inventory_status": "reserved",
            "reservation_id": reservation_id,
            "reserved_items": reserved_items,
            "total_items_reserved": len(reserved_items),
            "total_reserved_value": total_reserved_value,
            "reservation_timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        # Clean up partial reservations
        for reserved in reserved_items:
            try:
                await release_reservation(reserved["reservation_id"])
            except Exception:
                pass  # Log but don't fail the cleanup
        
        raise InventoryError(f"Inventory reservation failed: {str(e)}")

@worker("release_inventory")
async def release_inventory_worker(context):
    """Compensation worker: release reserved inventory."""
    
    reservation_id = context.get("reservation_id")
    
    if not reservation_id:
        return {"compensation_status": "no_reservation_to_release"}
    
    try:
        # Release the entire reservation
        release_result = await release_reservation(reservation_id)
        
        return {
            "compensation_status": "success",
            "released_reservation_id": reservation_id,
            "released_items": release_result.get("released_items", []),
            "release_timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        # Log error but don't fail compensation
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

**Features**:
- Atomic reservation with rollback
- Detailed inventory tracking
- Graceful failure handling
- Compensation pattern implementation

#### 3. Payment Processing Worker

```python
@worker("process_payment")
async def process_payment_worker(context):
    """Process payment with comprehensive error handling."""
    
    order = context["validated_order"]
    payment_info = order["payment_info"]
    total_amount = context["total_amount"]
    
    payment_request = {
        "amount": total_amount,
        "currency": "USD",
        "payment_method": payment_info["method"],
        "customer_id": order["customer_id"],
        "order_id": order["id"],
        "idempotency_key": f"pay-{order['id']}-{int(time.time())}"
    }
    
    try:
        # Simulate payment gateway call
        payment_response = await process_payment_gateway(payment_request)
        
        if payment_response["status"] == "succeeded":
            return {
                "payment_status": "charged",
                "payment_id": payment_response["payment_id"],
                "transaction_id": payment_response["transaction_id"],
                "amount_charged": payment_response["amount"],
                "gateway_fee": payment_response.get("fee", 0),
                "payment_method": payment_response["payment_method"],
                "charged_at": payment_response["timestamp"]
            }
        else:
            return {
                "payment_status": "failed",
                "error_code": payment_response.get("error_code"),
                "error_message": payment_response.get("error_message"),
                "gateway_response": payment_response,
                "retry_recommended": payment_response.get("retryable", False)
            }
            
    except PaymentGatewayTimeout:
        return {
            "payment_status": "timeout",
            "error_message": "Payment gateway timeout",
            "retry_recommended": True
        }
    except PaymentGatewayError as e:
        return {
            "payment_status": "gateway_error",
            "error_message": str(e),
            "retry_recommended": e.retryable
        }

@worker("refund_payment")
async def refund_payment_worker(context):
    """Compensation worker: refund processed payment."""
    
    payment_id = context.get("payment_id")
    transaction_id = context.get("transaction_id")
    amount_charged = context.get("amount_charged", 0)
    
    if not payment_id:
        return {"compensation_status": "no_payment_to_refund"}
    
    try:
        refund_request = {
            "payment_id": payment_id,
            "amount": amount_charged,
            "reason": "order_cancelled_during_processing",
            "idempotency_key": f"refund-{payment_id}-{int(time.time())}"
        }
        
        refund_response = await process_refund_gateway(refund_request)
        
        return {
            "compensation_status": "success",
            "refund_id": refund_response["refund_id"],
            "refunded_amount": refund_response["amount"],
            "original_payment_id": payment_id,
            "refund_timestamp": refund_response["timestamp"]
        }
        
    except Exception as e:
        await logger.error(
            "Failed to process refund",
            payment_id=payment_id,
            amount=amount_charged,
            error=str(e),
            transaction_id=context.get("transaction_id")
        )
        
        return {
            "compensation_status": "failed",
            "error": str(e),
            "payment_id": payment_id,
            "requires_manual_refund": True
        }
```

**Features**:
- Gateway integration simulation
- Comprehensive error categorization
- Idempotency handling
- Automatic refund compensation

#### 4. DSPy-Powered Confirmation Generator

```python
@dspy_worker("generate_confirmation")
async def generate_confirmation_worker(context):
    """Generate personalized order confirmation using DSPy."""
    
    order = context["validated_order"]
    customer_name = context.get("customer_name", "Valued Customer")
    order_details = context.get("order_details", "")
    
    # Enhanced context for DSPy processing
    confirmation_context = {
        "customer_name": customer_name,
        "order_id": order["id"],
        "order_details": order_details,
        "total_amount": context["total_amount"],
        "item_count": context["item_count"],
        "estimated_delivery": "3-5 business days",
        "payment_method": order["payment_info"]["method"],
        "shipping_address": order["shipping_info"],
        "confirmation_type": "order_confirmation",
        "tone": "professional_friendly",
        "include_tracking": True,
        "include_support_info": True
    }
    
    # DSPy will process this context and generate structured confirmation content
    return confirmation_context

# Post-processing hook for DSPy results
@generate_confirmation_worker.post_process
async def post_process_confirmation(dspy_result, original_context):
    """Post-process the DSPy-generated confirmation."""
    
    # Add metadata and formatting
    dspy_result.update({
        "generated_at": datetime.utcnow().isoformat(),
        "generation_model": "dspy-confirmation-v1",
        "personalization_level": "high" if len(dspy_result.get("customer_name", "")) > 0 else "standard",
        "content_length": len(dspy_result.get("confirmation_text", "")),
        "includes_tracking": "tracking_number" in dspy_result,
    })
    
    # Validate generated content
    required_elements = ["greeting", "order_summary", "next_steps"]
    missing_elements = [elem for elem in required_elements if elem not in dspy_result]
    
    if missing_elements:
        dspy_result["validation_warnings"] = f"Missing elements: {missing_elements}"
    
    return dspy_result
```

**Features**:
- LLM-powered content generation
- Rich context for personalization
- Post-processing validation
- Metadata tracking

## Monitoring Integration

### Comprehensive Metrics Collection

```python
async def main():
    """Main execution with detailed monitoring."""
    
    # Framework automatically sets up monitoring
    event_bus, worker_manager, orchestrator = await create_simple_framework(workflow)
    
    # Access monitoring components
    event_monitor = event_bus.event_monitor
    worker_monitor = worker_manager.worker_monitor
    metrics_collector = event_bus.metrics_collector
    logger = event_bus.monitoring_logger
    
    try:
        # ... execute workflow ...
        
        # Comprehensive monitoring summary
        print("\n📈 MONITORING SUMMARY")
        print("=" * 50)
        
        # Event metrics
        event_metrics = await event_monitor.get_event_metrics(time_window_minutes=10)
        print(f"📨 Total Events: {event_metrics['total_events']}")
        print(f"✅ Success Rate: {event_metrics['success_rate']:.1f}%")
        print(f"⚡ Avg Latency: {event_metrics.get('avg_latency_ms', 0):.1f}ms")
        
        # Worker performance
        worker_summary = await worker_monitor.get_worker_performance_summary(time_window_minutes=10)
        print(f"👷 Worker Commands: {worker_summary['aggregated_metrics']['total_commands']}")
        print(f"🎯 Worker Success Rate: {worker_summary['aggregated_metrics']['average_success_rate']:.1f}%")
        
        # Individual worker stats
        for worker_name in ['validate_order', 'check_inventory', 'process_payment']:
            worker_perf = await worker_monitor.get_worker_performance(worker_name, time_window_minutes=10)
            print(f"  {worker_name}: {worker_perf['success_rate']:.1f}% success, {worker_perf['avg_duration_ms']:.1f}ms avg")
        
        # System metrics
        system_metrics = await metrics_collector.get_system_metrics(time_window_minutes=10)
        print(f"💻 System Load: CPU {system_metrics.get('avg_cpu_usage', 0):.1f}%, Memory {system_metrics.get('avg_memory_usage', 0):.1f}%")
        
    finally:
        # Graceful shutdown with monitoring
        await logger.info("E-commerce workflow completed", 
                         transaction_id=transaction_id,
                         final_status=status['state'])
```

## Error Scenarios and Recovery

### Validation Failure

```python
# Test with invalid order
invalid_order = {
    "order": {
        "id": "ORDER-INVALID",
        "customer_id": "",  # Missing customer ID
        "items": [],        # No items
        "total_amount": -100  # Negative amount
    }
}

transaction_id = await orchestrator.execute_workflow(
    "ecommerce_order_processing",
    invalid_order
)

# Expected: Workflow fails at validation step
# No compensations needed since no resources were allocated
```

### Inventory Failure with Compensation

```python
# Test with insufficient inventory
insufficient_order = {
    "order": {
        "id": "ORDER-INSUFFICIENT",
        "customer_id": "CUST-123",
        "items": [
            {"product_id": "OUT-OF-STOCK", "quantity": 100, "price": 10.0}
        ],
        "total_amount": 1000.0
    }
}

# Expected: Validation passes, inventory check fails
# No compensation needed since reservation wasn't successful
```

### Payment Failure with Inventory Compensation

```python
# Test with payment failure after successful inventory reservation
payment_fail_order = {
    "order": {
        "id": "ORDER-PAYMENT-FAIL",
        "customer_id": "CUST-123",
        "items": [
            {"product_id": "LAPTOP", "quantity": 1, "price": 999.99}
        ],
        "total_amount": 999.99,
        "payment_info": {
            "method": "credit_card",
            "card_last4": "0000"  # Test card that will fail
        }
    }
}

# Expected: 
# 1. Validation passes
# 2. Inventory reserved successfully  
# 3. Payment fails
# 4. Compensation triggered: release_inventory executes
# 5. Workflow ends in "compensated" state
```

## Configuration Options

### Monitoring Configuration

```yaml
# examples/ecommerce_order/monitoring_config.yaml
logging:
  default_logger: "composite"
  level: "INFO"
  file_path: "./logs/ecommerce.log"
  max_file_size_mb: 50
  
event_monitoring:
  enabled: true
  trace_retention_hours: 48  # Keep traces longer for analysis
  track_payload_size: true
  
worker_monitoring:
  enabled: true
  health_check_interval_seconds: 15
  performance_window_minutes: 30
  alert_on_high_error_rate: true
  error_rate_threshold: 0.05  # Alert if >5% errors

metrics_collection:
  enabled: true
  collection_interval_seconds: 30
  include_system_metrics: true
```

### DSPy Configuration

```python
# Configure DSPy for content generation
import dspy

# Set up LLM backend
lm = dspy.OpenAI(model="gpt-3.5-turbo", max_tokens=500)
dspy.settings.configure(lm=lm)

# Custom DSPy signature for confirmations
class OrderConfirmationSignature(dspy.Signature):
    """Generate personalized order confirmation content."""
    
    customer_name = dspy.InputField(desc="Customer's name")
    order_details = dspy.InputField(desc="Order summary and items")
    total_amount = dspy.InputField(desc="Order total amount")
    
    greeting = dspy.OutputField(desc="Personalized greeting")
    order_summary = dspy.OutputField(desc="Formatted order summary")
    next_steps = dspy.OutputField(desc="What happens next information")
    tracking_info = dspy.OutputField(desc="Shipping and tracking details")
```

## Workflow Visualization

The example includes automatic diagram generation:

```python
# Generate workflow diagrams
python examples/ecommerce_order/diagram_demo.py
```

This creates:
- **Mermaid diagrams** (`.mmd` files) for web rendering
- **ASCII diagrams** (`.txt` files) for terminal viewing
- **Architecture diagrams** showing component relationships
- **Event flow diagrams** showing event sequences

## Performance Considerations

### Optimization Strategies

1. **Connection Pooling**
   ```python
   # Use connection pools for external services
   payment_pool = aiohttp.TCPConnector(limit=20)
   inventory_pool = asyncpg.create_pool(min_size=5, max_size=20)
   ```

2. **Parallel Processing**
   ```python
   # Process independent validations in parallel
   validation_tasks = [
       validate_customer_data(order),
       validate_inventory_availability(order),
       validate_payment_method(order)
   ]
   results = await asyncio.gather(*validation_tasks)
   ```

3. **Caching**
   ```python
   # Cache frequently accessed data
   @lru_cache(maxsize=1000)
   def get_product_details(product_id: str):
       return product_database.get(product_id)
   ```

## Production Deployment

### Environment Configuration

```bash
# Production environment variables
export MULTIAGENTS_REDIS_URL="redis://redis-cluster:6379"
export MULTIAGENTS_LOG_LEVEL="INFO"
export PAYMENT_GATEWAY_URL="https://api.stripe.com"
export INVENTORY_SERVICE_URL="https://inventory.company.com"
export DSPY_MODEL="gpt-4"
export MONITORING_CONFIG="/app/config/monitoring.yaml"
```

### Docker Deployment

```dockerfile
# Dockerfile for e-commerce workflow
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY examples/ecommerce_order/ ./ecommerce_order/
COPY multiagents/ ./multiagents/

CMD ["python", "-m", "ecommerce_order.main"]
```

## Testing

### Unit Tests

```python
# Test individual workers
@pytest.mark.asyncio
async def test_validate_order_success():
    valid_order = create_valid_order()
    result = await validate_order_worker({"order": valid_order})
    assert result["validation_status"] == "passed"

@pytest.mark.asyncio 
async def test_inventory_insufficient():
    order_with_large_quantity = create_order_with_quantity(1000)
    result = await check_inventory_worker({"validated_order": order_with_large_quantity})
    assert result["inventory_status"] == "insufficient"
```

### Integration Tests

```python
# Test complete workflow scenarios
@pytest.mark.asyncio
async def test_successful_order_flow():
    """Test complete successful order processing."""
    # Setup, execute workflow, verify final state
    pass

@pytest.mark.asyncio
async def test_payment_failure_compensation():
    """Test compensation when payment fails.""" 
    # Setup order that will fail at payment, verify compensation
    pass
```

## Next Steps

After exploring this example:

1. **Customize Business Logic** - Modify workers for your domain
2. **Add New Steps** - Extend workflow with additional processing
3. **Implement Real Integrations** - Connect to actual payment gateways and inventory systems
4. **Enhance Monitoring** - Add custom metrics and alerts
5. **Scale for Production** - Implement clustering and load balancing

This example provides a solid foundation for building production-ready distributed workflow systems!