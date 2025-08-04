import pytest
import asyncio
import os
from typing import AsyncGenerator, Dict, Any
import redis.asyncio as redis
from pathlib import Path
import tempfile
import shutil

from multiagents.event_bus import RedisEventBus
from multiagents.orchestrator import Orchestrator, WorkflowBuilder
from multiagents.worker_sdk import WorkerManager
from multiagents.monitoring import EventMonitor, WorkerMonitor, MonitoringConfig
from multiagents.core.factory import MultiAgentSystemFactory


@pytest.fixture(scope="session")
def event_loop_policy():
    """Set event loop policy for the test session."""
    return asyncio.get_event_loop_policy()


@pytest.fixture
async def redis_client():
    """Create a real Redis client for integration tests."""
    # Use a test-specific Redis DB (default is 0, we use 15 for tests)
    client = await redis.from_url("redis://localhost:6379/15")
    
    # Clean the test database
    await client.flushdb()
    
    yield client
    
    # Cleanup
    await client.flushdb()
    await client.close()


@pytest.fixture
async def test_monitoring_config(tmp_path):
    """Create monitoring configuration for tests."""
    log_dir = tmp_path / "logs"
    log_dir.mkdir(exist_ok=True)
    
    # Create nested config structure
    from multiagents.monitoring.config import LoggingConfig, EventMonitoringConfig, WorkerMonitoringConfig
    from multiagents.monitoring.interfaces import LogLevel
    
    logging_config = LoggingConfig(
        level=LogLevel.DEBUG,
        file_path=str(log_dir / "test.log")
    )
    
    event_config = EventMonitoringConfig(
        trace_retention_hours=1
    )
    
    worker_config = WorkerMonitoringConfig(
        metrics_retention_hours=1,
        health_check_interval_seconds=5
    )
    
    config = MonitoringConfig(
        logging=logging_config,
        event_monitoring=event_config,
        worker_monitoring=worker_config
    )
    
    return config


@pytest.fixture
async def integration_event_bus(redis_client, test_monitoring_config):
    """Create a real event bus connected to Redis."""
    logger = test_monitoring_config.create_logger()
    event_monitor = EventMonitor(logger=logger)
    
    event_bus = RedisEventBus(
        redis_url="redis://localhost:6379/15",
        channel_prefix="test_multiagent:",
        event_monitor=event_monitor,
        logger=logger
    )
    
    await event_bus.start()
    
    yield event_bus
    
    await event_bus.stop()


@pytest.fixture
async def integration_orchestrator(integration_event_bus, redis_client, test_monitoring_config):
    """Create an orchestrator for integration tests."""
    from tests.integration.fixtures.workflows import get_workflow
    
    logger = test_monitoring_config.create_logger()
    
    # Use the ecommerce workflow for most integration tests
    # This matches what the tests expect to execute
    ecommerce_workflow = get_workflow("ecommerce")
    
    orchestrator = Orchestrator(
        workflow=ecommerce_workflow,
        event_bus=integration_event_bus,
        logger=logger
        # Let orchestrator use default RedisStateStore
    )
    
    await orchestrator.start()
    
    yield orchestrator
    
    await orchestrator.stop()


@pytest.fixture
async def integration_worker_manager(integration_event_bus, test_monitoring_config):
    """Create a worker manager for integration tests."""
    logger = test_monitoring_config.create_logger()
    worker_monitor = WorkerMonitor(logger=logger)
    
    manager = WorkerManager(
        event_bus=integration_event_bus,
        worker_monitor=worker_monitor,
        logger=logger
    )
    
    await manager.start()
    
    yield manager
    
    await manager.stop()


@pytest.fixture
def workflow_builder():
    """Create a workflow builder for tests."""
    return WorkflowBuilder("test-workflow")


@pytest.fixture
async def multi_agent_system(test_monitoring_config):
    """Create a complete multi-agent system for integration tests."""
    # Create temporary directory for logs
    with tempfile.TemporaryDirectory() as temp_dir:
        log_path = Path(temp_dir) / "logs"
        log_path.mkdir()
        
        # Update config with temp log path
        test_monitoring_config.log_file_path = str(log_path / "integration.log")
        
        # Create system using factory
        system = await MultiAgentSystemFactory.create_system(
            redis_url="redis://localhost:6379/15",
            monitoring_config=test_monitoring_config
        )
        
        yield system
        
        # Cleanup
        await system.shutdown()


@pytest.fixture
def sample_workflow_definition():
    """Create a sample workflow definition for testing."""
    def create_workflow():
        builder = WorkflowBuilder("order-processing")
        
        # Define workflow steps
        builder.add_step(
            name="validate_order",
            worker_type="order_validator",
            timeout_seconds=30
        )
        
        builder.add_step(
            name="check_inventory", 
            worker_type="inventory_checker",
            compensation="restore_inventory",
            timeout_seconds=30
        )
        
        builder.add_step(
            name="process_payment",
            worker_type="payment_processor", 
            compensation="refund_payment",
            timeout_seconds=60
        )
        
        builder.add_step(
            name="ship_order",
            worker_type="shipping_handler",
            timeout_seconds=120
        )
        
        return builder.build()
    
    return create_workflow


@pytest.fixture
async def cleanup_redis(redis_client):
    """Cleanup Redis after each test."""
    yield
    await redis_client.flushdb()


@pytest.mark.integration
class IntegrationTest:
    """Base class for integration tests with common setup."""
    pass


# Test data fixtures
@pytest.fixture
def order_data():
    """Sample order data for testing."""
    return {
        "order_id": "TEST-ORDER-123",
        "customer_id": "CUST-456",
        "items": [
            {"sku": "ITEM-001", "quantity": 2, "price": 29.99},
            {"sku": "ITEM-002", "quantity": 1, "price": 49.99}
        ],
        "total": 109.97,
        "shipping_address": {
            "street": "123 Test St",
            "city": "Test City",
            "state": "TC",
            "zip": "12345"
        }
    }


@pytest.fixture
def payment_data():
    """Sample payment data for testing."""
    return {
        "card_number": "4111111111111111",
        "expiry": "12/25",
        "cvv": "123",
        "amount": 109.97
    }


# Utility to wait for conditions
async def wait_for_condition(condition_func, timeout=10, interval=0.1):
    """Wait for a condition to become true."""
    start_time = asyncio.get_event_loop().time()
    
    while asyncio.get_event_loop().time() - start_time < timeout:
        if await condition_func():
            return True
        await asyncio.sleep(interval)
    
    return False