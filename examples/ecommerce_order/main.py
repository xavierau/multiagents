"""
Main entry point for the e-commerce order processing example.

This demonstrates how to:
1. Set up the event bus and orchestrator
2. Register workers
3. Define and execute workflows
4. Handle results and monitor progress
"""
import asyncio
import sys
from typing import Dict, Any
from datetime import datetime

from multiagents.orchestrator import Orchestrator
from multiagents.event_bus.redis_bus import RedisEventBus
from multiagents.worker_sdk import WorkerManager
from multiagents.core.factory import create_simple_framework
from multiagents.monitoring import (
    MonitoringConfig, EventMonitor, WorkerMonitor, MetricsCollector
)

# Import workflow and workers
from .workflow import create_ecommerce_workflow, create_advanced_ecommerce_workflow
from .workers import (
    validate_order_worker,
    check_inventory_worker,
    process_payment_worker,
    refund_payment_worker,
    release_inventory_worker,
    generate_confirmation_worker,
    fulfill_order_worker,
    notify_customer_worker,
)


async def create_sample_order() -> Dict[str, Any]:
    """Create a sample order for testing."""
    return {
        "order": {
            "id": f"ORDER-{datetime.now().timestamp():.0f}",
            "customer_id": "CUST-12345",
            "items": [
                {
                    "product_id": "PROD-001",
                    "name": "Laptop",
                    "quantity": 1,
                    "price": 999.99
                },
                {
                    "product_id": "PROD-002",
                    "name": "Mouse",
                    "quantity": 2,
                    "price": 29.99
                }
            ],
            "total_amount": 1059.97,
            "payment_info": {
                "method": "credit_card",
                "card_last4": "1234"
            },
            "shipping_info": {
                "name": "John Doe",
                "address": "123 Main St",
                "city": "Anytown",
                "state": "CA",
                "zip": "12345",
                "country": "USA"
            }
        },
        "customer_name": "John Doe",
        "order_details": "1x Laptop, 2x Mouse - Total: $1059.97"
    }


async def monitor_workflow_status(orchestrator: Orchestrator, transaction_id: str) -> None:
    """Monitor workflow status until completion."""
    print(f"\n📊 Monitoring workflow {transaction_id}...\n")
    
    completed_states = {"completed", "failed", "compensated", "cancelled"}
    
    while True:
        try:
            status = await orchestrator.get_status(transaction_id)
            
            print(f"State: {status['state']}")
            print(f"Current Step: {status['current_step']}")
            print(f"Steps Completed: {len(status['step_results'])}")
            
            if status['error']:
                print(f"Error: {status['error']}")
            
            print("-" * 50)
            
            if status['state'] in completed_states:
                print(f"\n✅ Workflow completed with state: {status['state']}")
                
                if status['step_results']:
                    print("\n📋 Results:")
                    for step, result in status['step_results'].items():
                        print(f"  {step}: {result}")
                
                break
            
            await asyncio.sleep(2)
            
        except Exception as e:
            print(f"Error monitoring workflow: {e}")
            break


async def main():
    """Run the e-commerce example."""
    print("🚀 Starting E-commerce Order Processing Example\n")
    
    # Create framework components (monitoring is auto-initialized)
    print("📊 Setting up framework with monitoring...")
    workflow = create_ecommerce_workflow()
    event_bus, worker_manager, orchestrator = await create_simple_framework(workflow)
    
    # Get access to monitoring components if needed (optional)
    event_monitor = event_bus.event_monitor
    worker_monitor = worker_manager.worker_monitor
    metrics_collector = event_bus.metrics_collector
    logger = event_bus.monitoring_logger
    
    try:
        # Start event bus
        print("📡 Starting event bus...")
        await event_bus.start()
        
        # Register all workers
        print("\n👷 Registering workers...")
        worker_manager.register(validate_order_worker)
        worker_manager.register(check_inventory_worker)
        worker_manager.register(process_payment_worker)
        worker_manager.register(refund_payment_worker)
        worker_manager.register(release_inventory_worker)
        worker_manager.register(generate_confirmation_worker)
        worker_manager.register(fulfill_order_worker)
        worker_manager.register(notify_customer_worker)
        
        print(f"✓ Registered {len(worker_manager.list_workers())} workers")
        
        # Start workers
        await worker_manager.start()
        
        # Start orchestrator
        print("\n🎯 Starting orchestrator...")
        await orchestrator.start()
        
        # Create and process an order
        print("\n📦 Creating sample order...")
        order_data = await create_sample_order()
        
        # Execute workflow
        print("\n🔄 Executing workflow...")
        transaction_id = await orchestrator.execute_workflow(
            workflow.get_id(),
            order_data
        )
        
        print(f"✓ Workflow started with transaction ID: {transaction_id}")
        
        # Monitor progress
        await monitor_workflow_status(orchestrator, transaction_id)
        
        # Show monitoring summary
        print("\n📈 MONITORING SUMMARY")
        print("=" * 50)
        
        # Event metrics
        event_metrics = await event_monitor.get_event_metrics(time_window_minutes=10)
        print(f"📨 Total Events: {event_metrics['total_events']}")
        print(f"✅ Success Rate: {event_metrics['success_rate']:.1f}%")
        
        # Worker performance
        worker_summary = await worker_monitor.get_worker_performance_summary(time_window_minutes=10)
        print(f"👷 Worker Commands: {worker_summary['aggregated_metrics']['total_commands']}")
        print(f"🎯 Worker Success Rate: {worker_summary['aggregated_metrics']['average_success_rate']:.1f}%")
        
        # System metrics
        system_metrics = await metrics_collector.get_system_metrics(time_window_minutes=10)
        print(f"💻 System Metrics Collected: {len(system_metrics.get('system_metrics', {}))}")
        
        if logger:
            await logger.info("E-commerce workflow completed successfully",
                transaction_id=transaction_id,
                event_metrics=event_metrics,
                worker_summary=worker_summary
            )
        
    except KeyboardInterrupt:
        print("\n⚠️  Interrupted by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Cleanup - monitoring components are stopped automatically
        print("\n🧹 Cleaning up...")
        await worker_manager.stop()
        await orchestrator.stop()
        await event_bus.stop()
        await logger.close()
        print("✓ Shutdown complete")


if __name__ == "__main__":
    # Ensure Redis is running
    print("⚠️  Make sure Redis is running on localhost:6379")
    print("   You can start it with: redis-server\n")
    
    asyncio.run(main())