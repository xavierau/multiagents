#!/usr/bin/env python3
"""
{PROJECT_NAME} - Basic MultiAgents Framework Project

A simple example demonstrating core MultiAgents concepts.
"""

import asyncio
import logging
from pathlib import Path

from multiagents import (
    Orchestrator, WorkflowBuilder, WorkerManager,
    RedisEventBus, MonitoringConfig
)
from workers.basic_workers import setup_workers


async def main():
    """Main application entry point."""
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger("{PROJECT_NAME}")
    
    logger.info("Starting {PROJECT_NAME} application...")
    
    try:
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
        
        # Define workflow
        workflow = (WorkflowBuilder("basic-example")
            .add_step("validate", "input-validator")
            .add_step("process", "data-processor") 
            .add_step("save", "result-saver")
            .add_compensation("save", "cleanup-saver")
            .add_compensation("process", "rollback-processor")
            .build())
        
        # Initialize orchestrator
        orchestrator = Orchestrator(
            event_bus=event_bus,
            logger=monitoring_config.create_logger()
        )
        
        # Start services
        await worker_manager.start()
        await event_bus.connect()
        
        logger.info("All services started successfully")
        
        # Execute workflow
        initial_data = {
            "input": "Hello MultiAgents!",
            "user_id": "user123",
            "timestamp": "2024-01-01T00:00:00Z"
        }
        
        logger.info("Executing workflow with data: %s", initial_data)
        
        result = await orchestrator.execute_workflow(
            workflow_definition=workflow,
            initial_data=initial_data,
            transaction_id="txn-001"
        )
        
        logger.info("Workflow completed successfully!")
        logger.info("Final result: %s", result)
        
    except Exception as e:
        logger.error("Application failed: %s", str(e))
        raise
    
    finally:
        # Cleanup
        try:
            await worker_manager.stop()
            await event_bus.disconnect()
            logger.info("Services stopped successfully")
        except Exception as e:
            logger.error("Error during cleanup: %s", str(e))


if __name__ == "__main__":
    asyncio.run(main())