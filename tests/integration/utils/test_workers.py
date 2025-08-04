"""
Test workers for integration testing.
These workers simulate real business logic for testing workflows.
"""
from typing import Dict, Any
import asyncio
import random

from multiagents.worker_sdk import worker


@worker("order_validator", timeout=30)
async def validate_order_worker(context: Dict[str, Any]) -> Dict[str, Any]:
    """Validates order data."""
    order_id = context.get("order_id")
    items = context.get("items", [])
    total = context.get("total", 0)
    
    # Simulate validation logic
    await asyncio.sleep(0.1)  # Simulate processing time
    
    # Validate required fields
    if not order_id:
        raise ValueError("Order ID is required")
    
    if not items:
        raise ValueError("Order must contain at least one item")
    
    # Calculate expected subtotal from items
    items_subtotal = sum(item["quantity"] * item["price"] for item in items)
    
    # Get other components from context
    subtotal = context.get("subtotal", items_subtotal)
    tax = context.get("tax", 0)
    shipping = context.get("shipping", 0)
    
    # Calculate expected total
    expected_total = subtotal + tax + shipping
    
    if abs(expected_total - total) > 0.01:  # Allow small floating point differences
        raise ValueError(f"Order total mismatch: expected {expected_total} (subtotal: {subtotal} + tax: {tax} + shipping: {shipping}), got {total}")
    
    return {
        "validated": True,
        "order_id": order_id,
        "item_count": len(items),
        "validation_timestamp": asyncio.get_event_loop().time()
    }


@worker("inventory_checker", timeout=30)
async def check_inventory_worker(context: Dict[str, Any]) -> Dict[str, Any]:
    """Checks inventory availability."""
    items = context.get("items", [])
    
    # Simulate inventory check
    await asyncio.sleep(0.2)
    
    inventory_status = {}
    reserved_items = []
    
    for item in items:
        sku = item["sku"]
        quantity = item["quantity"]
        
        # Always succeed for deterministic testing
        available = True
        
        if available:
            inventory_status[sku] = {
                "available": True,
                "reserved": quantity
            }
            reserved_items.append({
                "sku": sku,
                "quantity": quantity,
                "reservation_id": f"RES-{sku}-{asyncio.get_event_loop().time()}"
            })
        else:
            inventory_status[sku] = {
                "available": False,
                "stock": 0
            }
            raise ValueError(f"Item {sku} is out of stock")
    
    return {
        "all_available": True,
        "inventory_status": inventory_status,
        "reserved_items": reserved_items
    }


@worker("restore_inventory", timeout=30)
async def restore_inventory_worker(context: Dict[str, Any]) -> Dict[str, Any]:
    """Compensation worker to restore inventory."""
    reserved_items = context.get("reserved_items", [])
    
    # Simulate inventory restoration
    await asyncio.sleep(0.1)
    
    restored = []
    for item in reserved_items:
        restored.append({
            "sku": item["sku"],
            "quantity": item["quantity"],
            "restored": True
        })
    
    return {
        "restoration_complete": True,
        "restored_items": restored
    }


@worker("payment_processor", timeout=60)
async def process_payment_worker(context: Dict[str, Any]) -> Dict[str, Any]:
    """Processes payment for the order."""
    order_id = context.get("order_id")
    total = context.get("total", 0)
    payment_info = context.get("payment_info", {})
    
    # Simulate payment processing
    await asyncio.sleep(0.5)
    
    # Always succeed for deterministic testing (failures tested separately)
    # Payment always succeeds unless specifically testing failure scenarios
    
    # Generate transaction ID
    transaction_id = f"TXN-{order_id}-{int(asyncio.get_event_loop().time())}"
    
    return {
        "payment_successful": True,
        "transaction_id": transaction_id,
        "amount_charged": total,
        "payment_method": "credit_card",
        "authorization_code": f"AUTH-{abs(hash(order_id)) % 999999}"
    }


@worker("refund_payment", timeout=60)
async def refund_payment_worker(context: Dict[str, Any]) -> Dict[str, Any]:
    """Compensation worker to refund payment."""
    transaction_id = context.get("transaction_id")
    amount = context.get("amount_charged", 0)
    
    # Simulate refund processing
    await asyncio.sleep(0.3)
    
    refund_id = f"REF-{transaction_id}-{int(asyncio.get_event_loop().time())}"
    
    return {
        "refund_successful": True,
        "refund_id": refund_id,
        "amount_refunded": amount,
        "refund_timestamp": asyncio.get_event_loop().time()
    }


@worker("customer_validator", timeout=30)
async def validate_customer_worker(context: Dict[str, Any]) -> Dict[str, Any]:
    """Validates customer data."""
    customer_id = context.get("customer_id")
    
    # Simulate customer validation
    await asyncio.sleep(0.1)
    
    if not customer_id:
        raise ValueError("Customer ID is required")
    
    return {
        "customer_validated": True,
        "customer_id": customer_id,
        "customer_tier": "standard",
        "validation_timestamp": asyncio.get_event_loop().time()
    }


@worker("pricing_calculator", timeout=30)
async def calculate_pricing_worker(context: Dict[str, Any]) -> Dict[str, Any]:
    """Calculates pricing and taxes."""
    items = context.get("items", [])
    customer_tier = context.get("customer_tier", "standard")
    
    # Simulate pricing calculation
    await asyncio.sleep(0.1)
    
    subtotal = sum(item["quantity"] * item["price"] for item in items)
    
    # Apply customer tier discount
    discount = 0.05 if customer_tier == "premium" else 0.0
    discounted_subtotal = subtotal * (1 - discount)
    
    # Calculate tax (8.5%)
    tax = discounted_subtotal * 0.085
    total = discounted_subtotal + tax
    
    return {
        "pricing_calculated": True,
        "subtotal": subtotal,
        "discount": discount,
        "tax": tax,
        "total": total
    }


@worker("notification_sender", timeout=30)
async def send_notification_worker(context: Dict[str, Any]) -> Dict[str, Any]:
    """Sends order confirmation notification."""
    order_id = context.get("order_id")
    customer_id = context.get("customer_id")
    tracking_number = context.get("tracking_number")
    
    # Simulate notification sending
    await asyncio.sleep(0.1)
    
    return {
        "notification_sent": True,
        "order_id": order_id,
        "customer_id": customer_id,
        "tracking_number": tracking_number,
        "notification_id": f"NOTIF-{order_id}-{int(asyncio.get_event_loop().time())}"
    }


@worker("shipping_handler", timeout=120)
async def handle_shipping_worker(context: Dict[str, Any]) -> Dict[str, Any]:
    """Handles order shipping."""
    order_id = context.get("order_id")
    shipping_address = context.get("shipping_address", {})
    items = context.get("items", [])
    
    # Simulate shipping label creation
    await asyncio.sleep(0.3)
    
    # Generate tracking number (deterministic for testing)
    tracking_number = f"TRACK-{order_id}-{abs(hash(order_id)) % 9999999}"
    
    # Calculate estimated delivery (deterministic)
    estimated_days = 3  # Fixed for testing
    
    return {
        "shipping_arranged": True,
        "tracking_number": tracking_number,
        "carrier": "FastShip Express",
        "estimated_delivery_days": estimated_days,
        "shipping_label_url": f"https://shipping.example.com/label/{tracking_number}",
        "package_weight": sum(item["quantity"] * 0.5 for item in items)  # Mock weight calculation
    }


# Error simulation workers for testing failure scenarios
@worker("failing_worker", timeout=10)
async def always_fails_worker(context: Dict[str, Any]) -> Dict[str, Any]:
    """Worker that always fails - for testing error handling."""
    await asyncio.sleep(0.1)
    raise Exception("This worker always fails")

# Alias for import
failing_worker = always_fails_worker


@worker("shipping_handler", timeout=120)
async def failing_shipping_handler(context: Dict[str, Any]) -> Dict[str, Any]:
    """Shipping handler that always fails for testing compensation."""
    await asyncio.sleep(0.1)
    raise Exception("Shipping failed")


@worker("timeout_worker", timeout=2)
async def timeout_worker(context: Dict[str, Any]) -> Dict[str, Any]:
    """Worker that times out - for testing timeout handling."""
    await asyncio.sleep(5)  # Sleep longer than timeout
    return {"never": "reaches here"}


@worker("intermittent_worker", timeout=30, retry_attempts=3)
async def intermittent_failure_worker(context: Dict[str, Any]) -> Dict[str, Any]:
    """Worker that fails intermittently - for testing retry logic."""
    attempt = context.get("_retry_attempt", 0)
    
    # Fail on first two attempts, succeed on third
    if attempt < 2:
        raise Exception(f"Intermittent failure on attempt {attempt + 1}")
    
    return {
        "success": True,
        "attempts_needed": attempt + 1
    }