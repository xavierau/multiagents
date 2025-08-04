"""
E-commerce order processing workers demonstrating the framework capabilities.
"""
from typing import Dict, Any
import random
import asyncio
from datetime import datetime

from multiagents.worker_sdk import worker, dspy_worker


@worker("validate_order")
async def validate_order_worker(context: Dict[str, Any]) -> Dict[str, Any]:
    """Validate order details."""
    order = context.get("order", {})
    
    # Simulate validation
    await asyncio.sleep(0.5)  # Simulate processing time
    
    # Check required fields
    required_fields = ["customer_id", "items", "total_amount"]
    missing_fields = [f for f in required_fields if f not in order]
    
    if missing_fields:
        return {
            "valid": False,
            "error": f"Missing required fields: {missing_fields}",
            "order_id": order.get("id", "unknown")
        }
    
    # Validate items
    if not order["items"] or len(order["items"]) == 0:
        return {
            "valid": False,
            "error": "Order must contain at least one item",
            "order_id": order.get("id", "unknown")
        }
    
    # Validate total amount
    if order["total_amount"] <= 0:
        return {
            "valid": False,
            "error": "Total amount must be greater than 0",
            "order_id": order.get("id", "unknown")
        }
    
    return {
        "valid": True,
        "order_id": order.get("id", f"ORD-{datetime.now().timestamp():.0f}"),
        "validated_at": datetime.utcnow().isoformat()
    }


@worker("check_inventory")
async def check_inventory_worker(context: Dict[str, Any]) -> Dict[str, Any]:
    """Check inventory availability for order items."""
    order = context.get("order", {})
    items = order.get("items", [])
    
    # Simulate inventory check
    await asyncio.sleep(0.3)
    
    # Mock inventory levels
    inventory = {
        "PROD-001": 100,
        "PROD-002": 50,
        "PROD-003": 0,  # Out of stock
        "PROD-004": 25,
    }
    
    unavailable_items = []
    reserved_items = []
    
    for item in items:
        product_id = item.get("product_id")
        quantity = item.get("quantity", 1)
        
        if product_id in inventory:
            if inventory[product_id] >= quantity:
                reserved_items.append({
                    "product_id": product_id,
                    "quantity": quantity,
                    "reserved": True
                })
                # Simulate reservation
                inventory[product_id] -= quantity
            else:
                unavailable_items.append({
                    "product_id": product_id,
                    "requested": quantity,
                    "available": inventory[product_id]
                })
        else:
            unavailable_items.append({
                "product_id": product_id,
                "requested": quantity,
                "available": 0,
                "error": "Product not found"
            })
    
    if unavailable_items:
        return {
            "inventory_available": False,
            "unavailable_items": unavailable_items,
            "error": "Some items are not available"
        }
    
    return {
        "inventory_available": True,
        "reserved_items": reserved_items,
        "reservation_id": f"RES-{datetime.now().timestamp():.0f}"
    }


@worker("process_payment")
async def process_payment_worker(context: Dict[str, Any]) -> Dict[str, Any]:
    """Process payment for the order."""
    order = context.get("order", {})
    payment_info = order.get("payment_info", {})
    
    # Simulate payment processing
    await asyncio.sleep(1.0)
    
    # Mock payment gateway response
    # 90% success rate for demonstration
    success = random.random() < 0.9
    
    if not payment_info:
        return {
            "payment_success": False,
            "error": "No payment information provided"
        }
    
    if success:
        return {
            "payment_success": True,
            "transaction_id": f"TXN-{datetime.now().timestamp():.0f}",
            "payment_method": payment_info.get("method", "credit_card"),
            "amount_charged": order.get("total_amount", 0),
            "processed_at": datetime.utcnow().isoformat()
        }
    else:
        return {
            "payment_success": False,
            "error": "Payment declined by processor",
            "decline_code": "INSUFFICIENT_FUNDS"
        }


@worker("refund_payment")
async def refund_payment_worker(context: Dict[str, Any]) -> Dict[str, Any]:
    """Compensation worker to refund payment."""
    transaction_id = context.get("transaction_id")
    
    if not transaction_id:
        return {
            "refund_success": False,
            "error": "No transaction ID provided for refund"
        }
    
    # Simulate refund processing
    await asyncio.sleep(0.5)
    
    return {
        "refund_success": True,
        "refund_transaction_id": f"REF-{datetime.now().timestamp():.0f}",
        "original_transaction_id": transaction_id,
        "refunded_at": datetime.utcnow().isoformat()
    }


@worker("release_inventory")
async def release_inventory_worker(context: Dict[str, Any]) -> Dict[str, Any]:
    """Compensation worker to release reserved inventory."""
    reservation_id = context.get("reservation_id")
    reserved_items = context.get("reserved_items", [])
    
    # Simulate inventory release
    await asyncio.sleep(0.3)
    
    released_items = []
    for item in reserved_items:
        released_items.append({
            "product_id": item["product_id"],
            "quantity": item["quantity"],
            "released": True
        })
    
    return {
        "release_success": True,
        "reservation_id": reservation_id,
        "released_items": released_items,
        "released_at": datetime.utcnow().isoformat()
    }


@dspy_worker("generate_order_confirmation", 
             signature="order_details, customer_name -> confirmation_message")
async def generate_confirmation_worker(context: Dict[str, Any]) -> Dict[str, Any]:
    """Use DSPy to generate a personalized order confirmation message."""
    # DSPy will automatically generate the confirmation_message
    # based on the signature and input data
    
    # We can add additional processing here if needed
    order_id = context.get("order_id", "unknown")
    
    return {
        "order_id": order_id,
        "confirmation_sent": True,
        "sent_at": datetime.utcnow().isoformat()
    }


@worker("fulfill_order")
async def fulfill_order_worker(context: Dict[str, Any]) -> Dict[str, Any]:
    """Create fulfillment request for the order."""
    order = context.get("order", {})
    order_id = context.get("order_id")
    
    # Simulate fulfillment creation
    await asyncio.sleep(0.5)
    
    # Create shipping label
    shipping_info = order.get("shipping_info", {})
    
    fulfillment = {
        "fulfillment_success": True,
        "order_id": order_id,
        "fulfillment_id": f"FUL-{datetime.now().timestamp():.0f}",
        "tracking_number": f"TRACK-{random.randint(100000, 999999)}",
        "carrier": "FedEx",
        "estimated_delivery": "3-5 business days",
        "shipping_address": shipping_info,
        "created_at": datetime.utcnow().isoformat()
    }
    
    return fulfillment


@worker("notify_customer")
async def notify_customer_worker(context: Dict[str, Any]) -> Dict[str, Any]:
    """Send notification to customer."""
    order_id = context.get("order_id")
    customer_id = context.get("order", {}).get("customer_id")
    notification_type = context.get("notification_type", "order_update")
    
    # Simulate notification sending
    await asyncio.sleep(0.2)
    
    return {
        "notification_sent": True,
        "notification_id": f"NOTIF-{datetime.now().timestamp():.0f}",
        "customer_id": customer_id,
        "order_id": order_id,
        "notification_type": notification_type,
        "sent_at": datetime.utcnow().isoformat()
    }