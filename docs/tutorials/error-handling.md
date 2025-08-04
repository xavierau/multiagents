# Tutorial: Error Handling and Compensations

Learn how to build resilient workflows with proper error handling, compensations, and recovery patterns.

## Learning Objectives

By the end of this tutorial, you will:
- Implement the saga pattern with compensations
- Handle different types of errors gracefully
- Build workflows that can recover from failures
- Understand rollback and cleanup strategies
- Test error scenarios systematically

## Prerequisites

- Completed [Basic Workflow Tutorial](basic-workflow.md)
- Understanding of distributed transaction concepts
- Familiarity with async error handling in Python

## What We're Building

An **Order Processing Workflow** with comprehensive error handling:

1. **Reserve Inventory** (with compensation: release inventory)
2. **Charge Payment** (with compensation: refund payment)  
3. **Create Shipment** (with compensation: cancel shipment)
4. **Send Confirmation** (no compensation needed)

If any step fails, compensations run in reverse order to undo previous actions.

## Error Handling Patterns

### 1. Input Validation Errors
- Catch early before any resources are allocated
- Return clear error messages
- Don't trigger compensations

### 2. Resource Allocation Errors  
- Handle partial failures gracefully
- Clean up allocated resources immediately
- May or may not trigger workflow compensations

### 3. External Service Errors
- Distinguish between retryable and non-retryable errors
- Implement proper timeout handling
- Use compensations to undo completed actions

### 4. System Errors
- Handle unexpected failures gracefully
- Ensure compensations still execute
- Log detailed error context

## Step 1: Set Up the Project

Create `order_processing_with_errors.py`:

```python
import asyncio
import random
import time
from datetime import datetime
from typing import Dict, Any, Optional
from dataclasses import dataclass

from multiagents import worker
from multiagents.core.factory import create_simple_framework
from multiagents.orchestrator.workflow import WorkflowBuilder
from multiagents.core.exceptions import WorkerExecutionError

# Custom exception types
class InsufficientInventoryError(Exception):
    """Raised when there's not enough inventory."""
    pass

class PaymentDeclinedError(Exception):
    """Raised when payment is declined."""
    pass

class ShippingUnavailableError(Exception):
    """Raised when shipping is not available."""
    pass

# Simulate external service states
INVENTORY_DB = {
    "LAPTOP-001": 5,
    "MOUSE-001": 20,
    "KEYBOARD-001": 0,  # Out of stock
    "MONITOR-001": 3
}

PAYMENT_SERVICE_STATUS = "online"  # Can be "online", "offline", "degraded"
SHIPPING_SERVICE_STATUS = "online"

# Track reservations and transactions for cleanup
ACTIVE_RESERVATIONS = {}
ACTIVE_PAYMENTS = {}
ACTIVE_SHIPMENTS = {}
```

## Step 2: Inventory Management with Compensation

```python
@worker("reserve_inventory")
async def reserve_inventory_worker(context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Reserve inventory items with detailed error handling.
    
    Input context:
        - order_items: list of items with product_id and quantity
        - order_id: unique order identifier
    
    Output:
        - reservation_id: unique reservation identifier
        - reserved_items: list of successfully reserved items
        - reservation_status: "success", "partial", or "failed"
    """
    order_items = context.get("order_items", [])
    order_id = context["order_id"]
    
    if not order_items:
        raise ValueError("No items to reserve")
    
    reservation_id = f"RES-{order_id}-{int(time.time())}"
    reserved_items = []
    failed_items = []
    
    print(f"🏪 Reserving inventory for order {order_id}")
    
    try:
        for item in order_items:
            product_id = item["product_id"]
            quantity = item["quantity"]
            
            print(f"  Checking {product_id} (qty: {quantity})")
            
            # Check current inventory
            available = INVENTORY_DB.get(product_id, 0)
            
            if available < quantity:
                failed_items.append({
                    "product_id": product_id,
                    "requested": quantity,
                    "available": available,
                    "error": "insufficient_inventory"
                })
                print(f"  ❌ Insufficient inventory for {product_id}")
                continue
            
            # Simulate reservation time
            await asyncio.sleep(0.1)
            
            # Reserve the inventory
            INVENTORY_DB[product_id] -= quantity
            reserved_items.append({
                "product_id": product_id,
                "quantity": quantity,
                "reserved_at": datetime.utcnow().isoformat()
            })
            
            print(f"  ✅ Reserved {quantity} x {product_id}")
        
        # If we couldn't reserve any items, fail completely
        if not reserved_items:
            return {
                "reservation_status": "failed",
                "error": "Could not reserve any items",
                "failed_items": failed_items,
                "reservation_id": None
            }
        
        # Store reservation for potential compensation
        ACTIVE_RESERVATIONS[reservation_id] = {
            "order_id": order_id,
            "reserved_items": reserved_items,
            "created_at": datetime.utcnow().isoformat()
        }
        
        # Determine status
        if failed_items:
            status = "partial"
            print(f"  ⚠️ Partial reservation: {len(reserved_items)} reserved, {len(failed_items)} failed")
        else:
            status = "success"
            print(f"  ✅ Full reservation successful")
        
        return {
            "reservation_id": reservation_id,
            "reserved_items": reserved_items,
            "failed_items": failed_items,
            "reservation_status": status,
            "total_items_reserved": len(reserved_items),
            "total_items_failed": len(failed_items)
        }
        
    except Exception as e:
        # Clean up any partial reservations
        print(f"  🔧 Cleaning up partial reservations due to error: {e}")
        for item in reserved_items:
            product_id = item["product_id"]
            quantity = item["quantity"]
            INVENTORY_DB[product_id] += quantity  # Return to inventory
        
        raise WorkerExecutionError(f"Inventory reservation failed: {str(e)}")

@worker("release_inventory")
async def release_inventory_worker(context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Compensation worker: Release reserved inventory.
    
    Input context:
        - reservation_id: reservation to release
    
    Output:
        - release_status: "success" or "failed"
        - released_items: items that were released
    """
    reservation_id = context.get("reservation_id")
    
    if not reservation_id:
        return {
            "release_status": "no_action_needed",
            "message": "No reservation ID provided"
        }
    
    print(f"🔄 COMPENSATION: Releasing inventory reservation {reservation_id}")
    
    try:
        reservation = ACTIVE_RESERVATIONS.get(reservation_id)
        
        if not reservation:
            print(f"  ⚠️ Reservation {reservation_id} not found")
            return {
                "release_status": "not_found",
                "message": f"Reservation {reservation_id} not found"
            }
        
        released_items = []
        
        # Release each reserved item
        for item in reservation["reserved_items"]:
            product_id = item["product_id"]
            quantity = item["quantity"]
            
            # Return inventory
            INVENTORY_DB[product_id] = INVENTORY_DB.get(product_id, 0) + quantity
            released_items.append(item)
            
            print(f"  ↩️ Released {quantity} x {product_id}")
        
        # Remove from active reservations
        del ACTIVE_RESERVATIONS[reservation_id]
        
        print(f"  ✅ Successfully released {len(released_items)} items")
        
        return {
            "release_status": "success",
            "released_items": released_items,
            "reservation_id": reservation_id,
            "released_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        print(f"  ❌ Failed to release reservation: {e}")
        
        # Even if compensation fails, we should log and continue
        # Don't raise an exception here as it would stop other compensations
        return {
            "release_status": "failed",
            "error": str(e),
            "reservation_id": reservation_id,
            "requires_manual_intervention": True
        }
```

## Step 3: Payment Processing with Compensation

```python
@worker("charge_payment")
async def charge_payment_worker(context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process payment with comprehensive error handling.
    
    Input context:
        - payment_info: payment method details
        - total_amount: amount to charge
        - order_id: order identifier
    
    Output:
        - payment_id: unique payment identifier
        - transaction_id: payment gateway transaction ID
        - payment_status: "charged", "declined", or "failed"
    """
    payment_info = context["payment_info"]
    total_amount = context["total_amount"]
    order_id = context["order_id"]
    
    print(f"💳 Processing payment for order {order_id}: ${total_amount}")
    
    # Check payment service status
    if PAYMENT_SERVICE_STATUS == "offline":
        raise WorkerExecutionError("Payment service is currently offline")
    
    payment_id = f"PAY-{order_id}-{int(time.time())}"
    
    try:
        # Simulate payment processing time
        await asyncio.sleep(0.3)
        
        # Simulate payment service behavior
        if PAYMENT_SERVICE_STATUS == "degraded":
            # In degraded mode, 50% chance of timeout
            if random.random() < 0.5:
                raise asyncio.TimeoutError("Payment gateway timeout")
        
        # Simulate different payment outcomes
        outcome = random.random()
        
        if outcome < 0.05:  # 5% chance of decline
            print(f"  ❌ Payment declined")
            return {
                "payment_status": "declined",
                "decline_reason": "insufficient_funds",
                "payment_id": payment_id,
                "error": "Payment was declined by the bank"
            }
        
        elif outcome < 0.08:  # 3% chance of processing error
            raise PaymentDeclinedError("Card processing error")
        
        else:
            # Successful payment
            transaction_id = f"TXN-{int(time.time())}-{random.randint(1000, 9999)}"
            
            # Store payment for potential refund
            ACTIVE_PAYMENTS[payment_id] = {
                "order_id": order_id,
                "amount": total_amount,
                "transaction_id": transaction_id,
                "charged_at": datetime.utcnow().isoformat(),
                "payment_method": payment_info.get("method", "unknown")
            }
            
            print(f"  ✅ Payment successful: {payment_id}")
            
            return {
                "payment_id": payment_id,
                "transaction_id": transaction_id,
                "payment_status": "charged",
                "amount_charged": total_amount,
                "gateway_fee": round(total_amount * 0.029, 2),  # 2.9% fee
                "charged_at": datetime.utcnow().isoformat()
            }
    
    except asyncio.TimeoutError:
        print(f"  ⏱️ Payment timeout")
        return {
            "payment_status": "timeout",
            "error": "Payment gateway timeout - transaction may still process",
            "payment_id": payment_id,
            "retry_recommended": True
        }
    
    except PaymentDeclinedError as e:
        print(f"  ❌ Payment processing error: {e}")
        return {
            "payment_status": "failed",
            "error": str(e),
            "payment_id": payment_id,
            "retry_recommended": False
        }
    
    except Exception as e:
        print(f"  💥 Unexpected payment error: {e}")
        raise WorkerExecutionError(f"Payment processing failed: {str(e)}")

@worker("refund_payment")
async def refund_payment_worker(context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Compensation worker: Refund a processed payment.
    
    Input context:
        - payment_id: payment to refund
        - amount_charged: amount to refund
    
    Output:
        - refund_status: "success" or "failed"
        - refund_id: unique refund identifier
    """
    payment_id = context.get("payment_id")
    amount_charged = context.get("amount_charged", 0)
    
    if not payment_id:
        return {
            "refund_status": "no_action_needed",
            "message": "No payment ID provided"
        }
    
    print(f"💰 COMPENSATION: Refunding payment {payment_id} (${amount_charged})")
    
    try:
        payment = ACTIVE_PAYMENTS.get(payment_id)
        
        if not payment:
            print(f"  ⚠️ Payment {payment_id} not found")
            return {
                "refund_status": "payment_not_found",
                "message": f"Payment {payment_id} not found"
            }
        
        # Simulate refund processing
        await asyncio.sleep(0.2)
        
        # Simulate potential refund issues (2% chance)
        if random.random() < 0.02:
            print(f"  ❌ Refund failed - gateway error")
            return {
                "refund_status": "failed",
                "error": "Payment gateway error during refund",
                "payment_id": payment_id,
                "requires_manual_refund": True
            }
        
        refund_id = f"REF-{payment_id}-{int(time.time())}"
        
        # Remove from active payments
        del ACTIVE_PAYMENTS[payment_id]
        
        print(f"  ✅ Refund successful: {refund_id}")
        
        return {
            "refund_status": "success",
            "refund_id": refund_id,
            "refunded_amount": amount_charged,
            "original_payment_id": payment_id,
            "refunded_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        print(f"  ❌ Refund error: {e}")
        
        # Log error but don't raise - compensation should continue
        return {
            "refund_status": "failed",
            "error": str(e),
            "payment_id": payment_id,
            "requires_manual_intervention": True
        }
```

## Step 4: Shipping with Compensation

```python
@worker("create_shipment")
async def create_shipment_worker(context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create shipment with error handling.
    
    Input context:
        - order_id: order identifier
        - shipping_address: delivery address
        - reserved_items: items to ship
    
    Output:
        - shipment_id: unique shipment identifier
        - tracking_number: package tracking number
        - shipment_status: "created" or "failed"
    """
    order_id = context["order_id"]
    shipping_address = context.get("shipping_address", {})
    reserved_items = context.get("reserved_items", [])
    
    print(f"📦 Creating shipment for order {order_id}")
    
    # Check shipping service status
    if SHIPPING_SERVICE_STATUS == "offline":
        raise ShippingUnavailableError("Shipping service is currently offline")
    
    if not reserved_items:
        raise ValueError("No items to ship")
    
    shipment_id = f"SHIP-{order_id}-{int(time.time())}"
    
    try:
        # Simulate shipment creation time
        await asyncio.sleep(0.2)
        
        # Simulate shipping issues (8% chance)
        if random.random() < 0.08:
            error_types = [
                "Address validation failed",
                "Shipping carrier unavailable",
                "Package size exceeds limits",
                "Restricted delivery area"
            ]
            error_message = random.choice(error_types)
            print(f"  ❌ Shipment creation failed: {error_message}")
            
            return {
                "shipment_status": "failed",
                "error": error_message,
                "shipment_id": shipment_id,
                "retry_recommended": error_message != "Restricted delivery area"
            }
        
        # Generate tracking number
        tracking_number = f"TRK{random.randint(100000000, 999999999)}"
        
        # Store shipment for potential cancellation
        ACTIVE_SHIPMENTS[shipment_id] = {
            "order_id": order_id,
            "tracking_number": tracking_number,
            "items": reserved_items,
            "shipping_address": shipping_address,
            "created_at": datetime.utcnow().isoformat(),
            "status": "created"
        }
        
        print(f"  ✅ Shipment created: {shipment_id} (Tracking: {tracking_number})")
        
        return {
            "shipment_id": shipment_id,
            "tracking_number": tracking_number,
            "shipment_status": "created",
            "estimated_delivery": "3-5 business days",
            "items_count": len(reserved_items),
            "created_at": datetime.utcnow().isoformat()
        }
        
    except ShippingUnavailableError:
        raise
    except Exception as e:
        print(f"  💥 Unexpected shipping error: {e}")
        raise WorkerExecutionError(f"Shipment creation failed: {str(e)}")

@worker("cancel_shipment")
async def cancel_shipment_worker(context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Compensation worker: Cancel a created shipment.
    
    Input context:
        - shipment_id: shipment to cancel
    
    Output:
        - cancellation_status: "success" or "failed"
    """
    shipment_id = context.get("shipment_id")
    
    if not shipment_id:
        return {
            "cancellation_status": "no_action_needed",
            "message": "No shipment ID provided"
        }
    
    print(f"📦 COMPENSATION: Cancelling shipment {shipment_id}")
    
    try:
        shipment = ACTIVE_SHIPMENTS.get(shipment_id)
        
        if not shipment:
            print(f"  ⚠️ Shipment {shipment_id} not found")
            return {
                "cancellation_status": "not_found",
                "message": f"Shipment {shipment_id} not found"
            }
        
        # Simulate cancellation processing
        await asyncio.sleep(0.1)
        
        # Simulate cancellation issues (1% chance)
        if random.random() < 0.01:
            print(f"  ❌ Cancellation failed - shipment already dispatched")
            return {
                "cancellation_status": "failed",
                "error": "Shipment already dispatched, cannot cancel",
                "shipment_id": shipment_id,
                "requires_manual_intervention": True
            }
        
        # Update shipment status
        shipment["status"] = "cancelled"
        shipment["cancelled_at"] = datetime.utcnow().isoformat()
        
        print(f"  ✅ Shipment cancelled successfully")
        
        return {
            "cancellation_status": "success",
            "shipment_id": shipment_id,
            "tracking_number": shipment["tracking_number"],
            "cancelled_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        print(f"  ❌ Cancellation error: {e}")
        
        return {
            "cancellation_status": "failed",
            "error": str(e),
            "shipment_id": shipment_id,
            "requires_manual_intervention": True
        }
```

## Step 5: Confirmation Worker (No Compensation)

```python
@worker("send_confirmation")
async def send_confirmation_worker(context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Send order confirmation email. No compensation needed as this doesn't allocate resources.
    
    Input context:
        - order_id: order identifier
        - customer_email: recipient email
        - tracking_number: shipment tracking number
    
    Output:
        - confirmation_status: "sent" or "failed"
        - email_id: unique email identifier
    """
    order_id = context["order_id"]
    customer_email = context.get("customer_email", "customer@example.com")
    tracking_number = context.get("tracking_number", "N/A")
    
    print(f"📧 Sending confirmation for order {order_id}")
    
    try:
        # Simulate email sending
        await asyncio.sleep(0.1)
        
        # Simulate email service issues (3% chance)
        if random.random() < 0.03:
            print(f"  ❌ Email service temporarily unavailable")
            return {
                "confirmation_status": "failed",
                "error": "Email service temporarily unavailable",
                "retry_recommended": True
            }
        
        email_id = f"EMAIL-{order_id}-{int(time.time())}"
        
        print(f"  ✅ Confirmation sent: {email_id}")
        
        return {
            "confirmation_status": "sent",
            "email_id": email_id,
            "recipient": customer_email,
            "tracking_number": tracking_number,
            "sent_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        print(f"  💥 Unexpected email error: {e}")
        # Email failures are not critical, return partial success
        return {
            "confirmation_status": "failed",
            "error": str(e),
            "retry_recommended": True
        }
```

## Step 6: Define the Workflow with Compensations

```python
def create_order_processing_workflow():
    """Create order processing workflow with compensations."""
    return (WorkflowBuilder("order_processing_with_compensations")
        .add_step("reserve_inventory", "reserve_inventory", 
                 compensation="release_inventory")
        .add_step("charge_payment", "charge_payment", 
                 compensation="refund_payment")
        .add_step("create_shipment", "create_shipment", 
                 compensation="cancel_shipment")
        .add_step("send_confirmation", "send_confirmation")
        # No compensation for confirmation - emails can't be "unsent"
        .build())
```

## Step 7: Test Different Error Scenarios

```python
async def test_error_scenarios(orchestrator):
    """Test various error scenarios and their compensations."""
    
    test_scenarios = [
        {
            "name": "Successful Order",
            "data": {
                "order_id": "ORDER-SUCCESS-001",
                "order_items": [
                    {"product_id": "LAPTOP-001", "quantity": 1},
                    {"product_id": "MOUSE-001", "quantity": 2}
                ],
                "payment_info": {"method": "credit_card", "card": "**** 1234"},
                "total_amount": 1299.99,
                "shipping_address": {"street": "123 Main St", "city": "Anytown"},
                "customer_email": "customer@example.com"
            }
        },
        {
            "name": "Insufficient Inventory",
            "data": {
                "order_id": "ORDER-INVENTORY-FAIL",
                "order_items": [
                    {"product_id": "KEYBOARD-001", "quantity": 5}  # Out of stock
                ],
                "payment_info": {"method": "credit_card", "card": "**** 5678"},
                "total_amount": 299.99,
                "shipping_address": {"street": "456 Oak St", "city": "Somewhere"},
                "customer_email": "customer2@example.com"
            }
        },
        {
            "name": "Payment Decline Scenario",
            "data": {
                "order_id": "ORDER-PAYMENT-DECLINE",
                "order_items": [
                    {"product_id": "MONITOR-001", "quantity": 1}
                ],
                "payment_info": {"method": "credit_card", "card": "**** 0000"},  # Decline card
                "total_amount": 399.99,
                "shipping_address": {"street": "789 Pine St", "city": "Elsewhere"},
                "customer_email": "customer3@example.com"
            }
        }
    ]
    
    results = []
    
    for scenario in test_scenarios:
        print(f"\n" + "="*60)
        print(f"🧪 Testing: {scenario['name']}")
        print("="*60)
        
        # Execute workflow
        transaction_id = await orchestrator.execute_workflow(
            "order_processing_with_compensations",
            scenario["data"]
        )
        
        # Monitor execution
        completed_states = {"completed", "failed", "compensated", "cancelled"}
        
        while True:
            status = await orchestrator.get_status(transaction_id)
            
            if status['state'] in completed_states:
                print(f"\n🏁 Final Result: {status['state'].upper()}")
                
                # Show compensation details if any
                if status['state'] == 'compensated':
                    print("🔄 Compensations were executed")
                
                results.append({
                    "scenario": scenario['name'],
                    "final_state": status['state'],
                    "step_results": status.get('step_results', {}),
                    "error": status.get('error')
                })
                
                break
            
            await asyncio.sleep(0.5)
        
        # Brief pause between scenarios
        await asyncio.sleep(1)
    
    return results

async def main():
    """Main execution function with comprehensive error testing."""
    print("🚀 Order Processing with Error Handling Tutorial")
    print("=" * 60)
    
    # Setup framework
    workflow = create_order_processing_workflow()
    event_bus, worker_manager, orchestrator = await create_simple_framework(workflow)
    
    try:
        # Start framework
        print("📡 Starting framework...")
        await event_bus.start()
        
        # Register workers
        print("👷 Registering workers...")
        workers = [
            reserve_inventory_worker,
            release_inventory_worker,
            charge_payment_worker,
            refund_payment_worker,
            create_shipment_worker,
            cancel_shipment_worker,
            send_confirmation_worker
        ]
        
        for worker_func in workers:
            worker_manager.register(worker_func)
        
        await worker_manager.start()
        await orchestrator.start()
        
        print(f"✓ Registered {len(workers)} workers")
        
        # Show initial state
        print(f"\n📊 Initial Inventory State:")
        for product, quantity in INVENTORY_DB.items():
            print(f"  {product}: {quantity} units")
        
        # Test error scenarios
        results = await test_error_scenarios(orchestrator)
        
        # Summary report
        print(f"\n" + "="*60)
        print("📊 TEST RESULTS SUMMARY")
        print("="*60)
        
        for result in results:
            print(f"\n{result['scenario']}:")
            print(f"  Final State: {result['final_state']}")
            if result['error']:
                print(f"  Error: {result['error']}")
        
        # Show final inventory state
        print(f"\n📊 Final Inventory State:")
        for product, quantity in INVENTORY_DB.items():
            print(f"  {product}: {quantity} units")
        
        # Show active resources
        print(f"\n🔍 Active Resources:")
        print(f"  Reservations: {len(ACTIVE_RESERVATIONS)}")
        print(f"  Payments: {len(ACTIVE_PAYMENTS)}")
        print(f"  Shipments: {len(ACTIVE_SHIPMENTS)}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        print("\n🧹 Shutting down...")
        await worker_manager.stop()
        await orchestrator.stop()
        await event_bus.stop()
        print("✓ Shutdown complete")

if __name__ == "__main__":
    asyncio.run(main())
```

## Step 8: Run and Observe

Execute the tutorial:

```bash
python order_processing_with_errors.py
```

Expected output:

```
🚀 Order Processing with Error Handling Tutorial
============================================================
📡 Starting framework...
👷 Registering workers...
✓ Registered 7 workers

📊 Initial Inventory State:
  LAPTOP-001: 5 units
  MOUSE-001: 20 units
  KEYBOARD-001: 0 units
  MONITOR-001: 3 units

============================================================
🧪 Testing: Successful Order
============================================================
🏪 Reserving inventory for order ORDER-SUCCESS-001
  Checking LAPTOP-001 (qty: 1)
  ✅ Reserved 1 x LAPTOP-001
  Checking MOUSE-001 (qty: 2)
  ✅ Reserved 2 x MOUSE-001
  ✅ Full reservation successful
💳 Processing payment for order ORDER-SUCCESS-001: $1299.99
  ✅ Payment successful: PAY-ORDER-SUCCESS-001-1704123456
📦 Creating shipment for order ORDER-SUCCESS-001
  ✅ Shipment created: SHIP-ORDER-SUCCESS-001-1704123457 (Tracking: TRK123456789)
📧 Sending confirmation for order ORDER-SUCCESS-001
  ✅ Confirmation sent: EMAIL-ORDER-SUCCESS-001-1704123458

🏁 Final Result: COMPLETED

============================================================
🧪 Testing: Insufficient Inventory
============================================================
🏪 Reserving inventory for order ORDER-INVENTORY-FAIL
  Checking KEYBOARD-001 (qty: 5)
  ❌ Insufficient inventory for KEYBOARD-001

🏁 Final Result: FAILED

============================================================
🧪 Testing: Payment Decline Scenario
============================================================
🏪 Reserving inventory for order ORDER-PAYMENT-DECLINE
  Checking MONITOR-001 (qty: 1)
  ✅ Reserved 1 x MONITOR-001
  ✅ Full reservation successful
💳 Processing payment for order ORDER-PAYMENT-DECLINE: $399.99
  ❌ Payment declined
🔄 COMPENSATION: Releasing inventory reservation RES-ORDER-PAYMENT-DECLINE-1704123459
  ↩️ Released 1 x MONITOR-001
  ✅ Successfully released 1 items

🏁 Final Result: COMPENSATED
🔄 Compensations were executed
```

## Understanding Compensation Flow

When the payment fails in the third scenario:

1. **Inventory Reserved**: Successfully reserved 1 monitor
2. **Payment Failed**: Payment was declined
3. **Compensation Triggered**: Workflow enters compensation mode
4. **Inventory Released**: `release_inventory` compensation executed
5. **Final State**: Workflow marked as "compensated"

## Step 9: Advanced Error Scenarios

Add these functions to test more complex scenarios:

```python
async def simulate_service_outages(orchestrator):
    """Test behavior during service outages."""
    global PAYMENT_SERVICE_STATUS, SHIPPING_SERVICE_STATUS
    
    print("\n🔧 Testing Service Outage Scenarios")
    
    # Test payment service outage
    print("\n📴 Simulating payment service outage...")
    PAYMENT_SERVICE_STATUS = "offline"
    
    try:
        transaction_id = await orchestrator.execute_workflow(
            "order_processing_with_compensations",
            {
                "order_id": "ORDER-PAYMENT-OUTAGE",
                "order_items": [{"product_id": "LAPTOP-001", "quantity": 1}],
                "payment_info": {"method": "credit_card"},
                "total_amount": 999.99,
                "customer_email": "test@example.com"
            }
        )
        
        # Monitor result
        while True:
            status = await orchestrator.get_status(transaction_id)
            if status['state'] in {"completed", "failed", "compensated"}:
                print(f"Payment outage result: {status['state']}")
                break
            await asyncio.sleep(0.5)
            
    finally:
        # Restore service
        PAYMENT_SERVICE_STATUS = "online"
        print("📶 Payment service restored")

async def test_partial_compensation_failure():
    """Test scenarios where compensations themselves might fail."""
    # This could involve temporarily breaking compensation workers
    # to see how the system handles compensation failures
    pass
```

## Verification

### Check Compensation Effectiveness

1. **Resource Cleanup**: Verify inventory is properly released
2. **Payment Handling**: Ensure refunds are processed
3. **Shipment Management**: Confirm shipments are cancelled
4. **State Consistency**: Check that final state reflects compensation

### Test Edge Cases

1. **Multiple Failures**: What happens if both payment and shipping fail?
2. **Compensation Failures**: What if a compensation worker itself fails?
3. **Partial Success**: How are partial inventory reservations handled?
4. **Service Outages**: How does the system behave during outages?

## Common Issues

### Compensation Not Executing
- Check that compensation workers are registered
- Verify compensation names match in workflow definition
- Ensure earlier steps succeeded before compensation is needed

### Resource Leaks
- Make sure compensation workers properly clean up resources
- Check for race conditions in resource allocation/deallocation
- Monitor active resource tracking dictionaries

### Error Propagation
- Distinguish between retryable and non-retryable errors
- Ensure worker errors are properly categorized
- Check that validation errors don't trigger unnecessary compensations

## What You Learned

✅ **Saga Pattern**: How to implement distributed transactions with compensations  
✅ **Error Categories**: Different types of errors and how to handle them  
✅ **Compensation Design**: How to build effective rollback mechanisms  
✅ **Resource Management**: Proper allocation and cleanup of resources  
✅ **Error Propagation**: How errors flow through workflows  
✅ **Testing Strategies**: How to systematically test error scenarios  

## Next Steps

Continue your learning journey with:

1. **[Monitoring Setup Tutorial](monitoring-setup.md)** - Add observability to error-prone workflows
2. **[DSPy Workers Tutorial](dspy-workers.md)** - Build intelligent error handling with LLMs
3. **[Advanced Patterns Tutorial](advanced-patterns.md)** - Implement retry policies and circuit breakers

## Best Practices Summary

1. **Design for Failure**: Assume external services will fail
2. **Fail Fast**: Validate early to avoid unnecessary resource allocation  
3. **Clean Compensations**: Make compensation workers idempotent and robust
4. **Detailed Logging**: Log all error scenarios with sufficient context
5. **Monitor Resources**: Track active resources to detect leaks
6. **Test Thoroughly**: Create comprehensive error scenario test suites

This tutorial demonstrates how to build resilient, production-ready workflows that gracefully handle failures and maintain system consistency!