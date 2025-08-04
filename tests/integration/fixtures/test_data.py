"""
Test data fixtures for integration tests.
"""
from typing import Dict, Any, List
import random
from datetime import datetime, timedelta


def generate_order_data(
    order_id: str = None,
    customer_id: str = None,
    item_count: int = 2,
    total: float = None
) -> Dict[str, Any]:
    """Generate realistic order data for testing."""
    if not order_id:
        order_id = f"ORDER-{random.randint(100000, 999999)}"
    
    if not customer_id:
        customer_id = f"CUST-{random.randint(10000, 99999)}"
    
    # Generate items
    items = []
    calculated_total = 0.0
    
    for i in range(item_count):
        price = round(random.uniform(10.00, 100.00), 2)
        quantity = random.randint(1, 5)
        item = {
            "sku": f"SKU-{random.randint(1000, 9999)}-{i}",
            "name": f"Product {i+1}",
            "price": price,
            "quantity": quantity,
            "subtotal": price * quantity
        }
        items.append(item)
        calculated_total += item["subtotal"]
    
    # Calculate tax and shipping
    tax = round(calculated_total * 0.08, 2)  # 8% tax
    shipping = 9.99
    
    # Use provided total or calculated total including tax and shipping
    final_total = total if total is not None else (calculated_total + tax + shipping)
    
    return {
        "order_id": order_id,
        "customer_id": customer_id,
        "items": items,
        "subtotal": calculated_total,
        "tax": tax,
        "shipping": shipping,
        "total": final_total,
        "currency": "USD",
        "order_date": datetime.utcnow().isoformat(),
        "shipping_address": {
            "name": "John Doe",
            "street": "123 Main St",
            "city": "Anytown",
            "state": "CA",
            "zip": "12345",
            "country": "US"
        },
        "billing_address": {
            "name": "John Doe", 
            "street": "123 Main St",
            "city": "Anytown",
            "state": "CA",
            "zip": "12345",
            "country": "US"
        }
    }


def generate_customer_data(customer_id: str = None) -> Dict[str, Any]:
    """Generate customer data for testing."""
    if not customer_id:
        customer_id = f"CUST-{random.randint(10000, 99999)}"
    
    return {
        "customer_id": customer_id,
        "email": f"customer{random.randint(1000, 9999)}@example.com",
        "first_name": "John",
        "last_name": "Doe", 
        "phone": f"+1-555-{random.randint(100, 999)}-{random.randint(1000, 9999)}",
        "registration_date": (datetime.utcnow() - timedelta(days=random.randint(1, 365))).isoformat(),
        "loyalty_tier": random.choice(["bronze", "silver", "gold", "platinum"]),
        "credit_limit": random.uniform(1000, 10000),
        "payment_methods": [
            {
                "type": "credit_card",
                "last_four": str(random.randint(1000, 9999)),
                "brand": random.choice(["visa", "mastercard", "amex"])
            }
        ]
    }


def generate_payment_data(amount: float = None) -> Dict[str, Any]:
    """Generate payment data for testing."""
    if amount is None:
        amount = round(random.uniform(10.00, 500.00), 2)
    
    return {
        "amount": amount,
        "currency": "USD",
        "payment_method": {
            "type": "credit_card",
            "card_number": "4111111111111111",  # Test card number
            "expiry_month": "12",
            "expiry_year": "2025",
            "cvv": "123",
            "cardholder_name": "John Doe"
        },
        "billing_address": {
            "street": "123 Main St",
            "city": "Anytown", 
            "state": "CA",
            "zip": "12345",
            "country": "US"
        }
    }


def generate_inventory_data(items: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Generate inventory data based on order items."""
    inventory = {}
    
    for item in items:
        sku = item["sku"]
        requested_qty = item["quantity"]
        
        # Simulate inventory levels
        available_qty = random.randint(0, requested_qty + 10)
        
        inventory[sku] = {
            "sku": sku,
            "available_quantity": available_qty,
            "reserved_quantity": 0,
            "warehouse_location": f"WH-{random.choice(['A', 'B', 'C'])}-{random.randint(1, 100)}",
            "last_updated": datetime.utcnow().isoformat()
        }
    
    return inventory


def generate_large_dataset(count: int = 100) -> List[Dict[str, Any]]:
    """Generate a large dataset for load testing."""
    return [generate_order_data() for _ in range(count)]


def generate_error_scenarios() -> List[Dict[str, Any]]:
    """Generate data that will trigger various error scenarios."""
    return [
        # Invalid order - missing required fields
        {
            "order_id": "INVALID-001",
            "items": [],  # Empty items
            "total": 0
        },
        
        # Invalid payment data
        {
            "order_id": "INVALID-002", 
            "items": [{"sku": "TEST-001", "quantity": 1, "price": 10.00}],
            "total": 10.00,
            "payment_info": {
                "card_number": "0000000000000000",  # Invalid card
                "amount": -10.00  # Negative amount
            }
        },
        
        # Inventory shortage
        {
            "order_id": "SHORTAGE-001",
            "items": [
                {"sku": "OUT-OF-STOCK-001", "quantity": 999, "price": 10.00}
            ],
            "total": 9990.00
        }
    ]


# Pre-defined test scenarios
TEST_SCENARIOS = {
    "simple_order": lambda: generate_order_data("SIMPLE-001", "CUST-001", 1),  # Let it calculate total correctly
    "complex_order": lambda: generate_order_data("COMPLEX-001", "CUST-002", 5),  # Let it calculate total correctly  
    "high_value_order": lambda: generate_order_data("HIGH-001", "CUST-003", 3),  # Let it calculate total correctly
    "international_order": lambda: {
        **generate_order_data("INTL-001", "CUST-004", 2, 149.99),
        "shipping_address": {
            "name": "Jane Smith",
            "street": "456 Queen St",
            "city": "Toronto", 
            "state": "ON",
            "zip": "M5V 3A1",
            "country": "CA"
        }
    },
    "bulk_order": lambda: generate_order_data("BULK-001", "CUST-005", 10, 899.99),
}


def get_test_scenario(name: str) -> Dict[str, Any]:
    """Get a predefined test scenario by name."""
    if name not in TEST_SCENARIOS:
        raise ValueError(f"Unknown test scenario: {name}. Available: {list(TEST_SCENARIOS.keys())}")
    
    return TEST_SCENARIOS[name]()