#!/usr/bin/env python3
"""
{PROJECT_NAME} - E-commerce Order Processing

A comprehensive example demonstrating complex workflow orchestration
with saga pattern, compensation, and monitoring.
"""

import asyncio
import logging
from pathlib import Path
from typing import Dict, Any

from multiagents import (
    Orchestrator, WorkflowBuilder, WorkerManager,
    RedisEventBus, MonitoringConfig
)
from workers.ecommerce_workers import setup_workers
from models.order_models import OrderData


async def create_test_orders() -> list[OrderData]:
    """Create test orders for different scenarios."""
    
    return [
        # Successful order
        OrderData(
            order_id="ORD-001",
            customer_id="CUST-123",
            items=[
                {"product_id": "PROD-001", "quantity": 2, "price": 29.99},
                {"product_id": "PROD-002", "quantity": 1, "price": 49.99}
            ],
            payment_method="credit_card",
            payment_token="tok_valid_card",
            shipping_address={
                "street": "123 Main St",
                "city": "San Francisco", 
                "state": "CA",
                "zip": "94105"
            }
        ),
        
        # Order that will fail at payment
        OrderData(
            order_id="ORD-002",
            customer_id="CUST-456", 
            items=[
                {"product_id": "PROD-003", "quantity": 1, "price": 99.99}
            ],
            payment_method="credit_card",
            payment_token="tok_invalid_card",  # This will cause payment failure
            shipping_address={
                "street": "456 Oak Ave",
                "city": "Portland",
                "state": "OR", 
                "zip": "97201"
            }
        ),
        
        # Order that will fail due to insufficient inventory
        OrderData(
            order_id="ORD-003",
            customer_id="CUST-789",
            items=[
                {"product_id": "PROD-004", "quantity": 100, "price": 19.99}  # Requesting too many
            ],
            payment_method="paypal",
            payment_token="tok_valid_paypal",
            shipping_address={
                "street": "789 Pine St",
                "city": "Seattle",
                "state": "WA",
                "zip": "98101"
            }
        )
    ]


async def setup_framework() -> tuple[Orchestrator, WorkerManager, RedisEventBus]:
    """Setup and initialize the MultiAgents framework components."""
    
    # Load monitoring configuration
    config_path = Path(__file__).parent / "config" / "monitoring.yaml"
    monitoring_config = MonitoringConfig.from_file(config_path)
    
    # Initialize event bus
    event_bus = RedisEventBus(
        redis_url="redis://localhost:6379",
        event_monitor=monitoring_config.create_event_monitor(),
        logger=monitoring_config.create_logger()
    )
    
    # Initialize worker manager
    worker_manager = WorkerManager(
        event_bus=event_bus,
        worker_monitor=monitoring_config.create_worker_monitor(),
        logger=monitoring_config.create_logger()
    )
    
    # Setup workers
    setup_workers(worker_manager)
    
    # Initialize orchestrator
    orchestrator = Orchestrator(
        event_bus=event_bus,
        logger=monitoring_config.create_logger()
    )
    
    return orchestrator, worker_manager, event_bus


def create_order_workflow():
    """Create the e-commerce order processing workflow."""
    
    return (WorkflowBuilder("ecommerce-order-processing")
        .add_step("validate", "order-validator")
        .add_step("inventory", "inventory-manager")
        .add_step("payment", "payment-processor")
        .add_step("fulfillment", "order-fulfiller")
        .add_step("notification", "notification-sender")
        
        # Compensation chain (executed in reverse order)
        .add_compensation("notification", "notification-cleanup")
        .add_compensation("fulfillment", "fulfillment-rollback")  
        .add_compensation("payment", "payment-refund")
        .add_compensation("inventory", "inventory-release")
        
        .build())


async def process_order(orchestrator: Orchestrator, workflow, order: OrderData, scenario_name: str):
    """Process a single order and handle the result."""
    
    logger = logging.getLogger(__name__)
    
    logger.info("=" * 60)
    logger.info("Processing %s: %s", scenario_name, order.order_id)
    logger.info("Customer: %s", order.customer_id)
    logger.info("Items: %d products, Total: $%.2f", len(order.items), order.total_amount)
    logger.info("=" * 60)
    
    try:
        result = await orchestrator.execute_workflow(
            workflow_definition=workflow,
            initial_data=order.dict(),
            transaction_id=f"txn-{order.order_id}"
        )
        
        if result.get("status") == "completed":
            logger.info("✅ Order %s processed successfully!", order.order_id)
            logger.info("   Payment ID: %s", result.get("payment", {}).get("payment_id"))
            logger.info("   Tracking Number: %s", result.get("fulfillment", {}).get("tracking_number"))
        else:
            logger.warning("⚠️ Order %s completed with warnings", order.order_id)
            
    except Exception as e:
        logger.error("❌ Order %s failed: %s", order.order_id, str(e))
        logger.info("   Automatic compensation should have been triggered")
    
    # Add delay between orders for better log readability
    await asyncio.sleep(2)


async def main():
    """Main application entry point."""
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger("{PROJECT_NAME}")
    
    logger.info("🚀 Starting {PROJECT_NAME} E-commerce Order Processing Demo")
    
    try:
        # Setup framework
        orchestrator, worker_manager, event_bus = await setup_framework()
        
        # Create workflow
        workflow = create_order_workflow()
        
        # Start services
        await worker_manager.start()
        await event_bus.connect()
        
        logger.info("✅ All services started successfully")
        logger.info("📊 Monitoring enabled - check ./logs/{PROJECT_NAME}.log for detailed traces")
        
        # Create test orders
        test_orders = await create_test_orders()
        
        # Process each order scenario
        scenarios = [
            "Successful Order Processing",
            "Payment Failure Scenario (will trigger compensation)",
            "Inventory Shortage Scenario (will trigger compensation)"
        ]
        
        for order, scenario in zip(test_orders, scenarios):
            await process_order(orchestrator, workflow, order, scenario)
        
        logger.info("🎉 All order processing scenarios completed!")
        logger.info("📈 Check the monitoring logs to see event traces and performance metrics")
        
    except Exception as e:
        logger.error("💥 Application failed: %s", str(e))
        raise
    
    finally:
        # Cleanup
        try:
            await worker_manager.stop()
            await event_bus.disconnect()
            logger.info("🛑 Services stopped successfully")
        except Exception as e:
            logger.error("Error during cleanup: %s", str(e))


if __name__ == "__main__":
    asyncio.run(main())