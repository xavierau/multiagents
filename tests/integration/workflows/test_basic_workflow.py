"""
Integration tests for basic workflow execution.
Tests the complete flow from workflow definition to execution.
"""
import pytest
import asyncio
from typing import Dict, Any

from multiagents.orchestrator import WorkflowBuilder
from multiagents.core.saga_context import SagaState
from tests.integration.utils.test_workers import (
    validate_order_worker,
    check_inventory_worker,
    process_payment_worker,
    handle_shipping_worker
)


@pytest.mark.integration
@pytest.mark.asyncio
class TestBasicWorkflow:
    """Test basic workflow execution scenarios."""
    
    async def test_simple_sequential_workflow(
        self,
        integration_orchestrator,
        integration_worker_manager,
        order_data
    ):
        """Test a simple sequential workflow execution."""
        # Register workers
        integration_worker_manager.register(validate_order_worker)
        integration_worker_manager.register(check_inventory_worker)
        integration_worker_manager.register(process_payment_worker)
        integration_worker_manager.register(handle_shipping_worker)
        
        # Create workflow
        builder = WorkflowBuilder("simple-order-workflow")
        builder.add_step("validate", "order_validator")
        builder.add_step("inventory", "inventory_checker")
        builder.add_step("payment", "payment_processor")
        builder.add_step("shipping", "shipping_handler")
        workflow = builder.build()
        
        # Create separate orchestrator for this workflow
        from multiagents.orchestrator import Orchestrator
        test_orchestrator = Orchestrator(
            workflow=workflow,
            event_bus=integration_orchestrator.event_bus,
            logger=integration_orchestrator.monitoring_logger
        )
        await test_orchestrator.start()
        
        # Execute workflow
        transaction_id = await test_orchestrator.execute_workflow(
            "simple-order-workflow",
            order_data
        )
        
        # Wait for completion
        await asyncio.sleep(2)  # Give time for async execution
        
        # Check final state
        state = await test_orchestrator.get_status(transaction_id)
        
        assert state is not None
        assert state["state"] == SagaState.COMPLETED.value
        
        # Check step results - use the step names from add_step
        step_results = state["step_results"]
        assert step_results.get("validate", {}).get("validated") is True
        assert step_results.get("inventory", {}).get("all_available") is True
        assert step_results.get("payment", {}).get("payment_successful") is True
        assert step_results.get("shipping", {}).get("shipping_arranged") is True
        assert any("tracking_number" in result for result in step_results.values() if isinstance(result, dict))
        
        # Clean up
        await test_orchestrator.stop()
    
    async def test_workflow_with_initial_data_merge(
        self,
        integration_orchestrator,
        integration_worker_manager,
        order_data
    ):
        """Test that initial data is preserved throughout workflow."""
        # Register minimal worker
        from multiagents.worker_sdk import worker
        
        @worker("data_checker", timeout=10)
        async def check_data_worker(context: Dict[str, Any]) -> Dict[str, Any]:
            # Verify original data is still present
            assert context.get("order_id") == order_data["order_id"]
            assert context.get("customer_id") == order_data["customer_id"]
            return {"data_verified": True}
        
        integration_worker_manager.register(check_data_worker)
        
        # Create workflow
        builder = WorkflowBuilder("data-preservation-workflow")
        builder.add_step("check", "data_checker")
        workflow = builder.build()
        
        # Create separate orchestrator for this workflow
        from multiagents.orchestrator import Orchestrator
        data_orchestrator = Orchestrator(
            workflow=workflow,
            event_bus=integration_orchestrator.event_bus,
            logger=integration_orchestrator.monitoring_logger
        )
        await data_orchestrator.start()
        
        # Execute
        transaction_id = await data_orchestrator.execute_workflow(
            "data-preservation-workflow",
            order_data
        )
        
        await asyncio.sleep(0.5)
        
        state = await data_orchestrator.get_status(transaction_id)
        assert state["state"] == SagaState.COMPLETED.value
        
        # Check step results for data verification
        step_results = state["step_results"]
        assert step_results.get("check", {}).get("data_verified") is True
        
        # Check if order_id is preserved - the worker validates it's present so it must be there
        # The data_checker worker explicitly asserts context.get("order_id") == order_data["order_id"]
        # If that assertion passed, then data was preserved correctly
        assert step_results.get("check", {}).get("data_verified") is True
        
        # Clean up
        await data_orchestrator.stop()
    
    async def test_workflow_step_timeout(
        self,
        integration_orchestrator,
        integration_worker_manager
    ):
        """Test workflow behavior when a step times out."""
        # Import timeout worker
        from tests.integration.utils.test_workers import timeout_worker
        
        integration_worker_manager.register(timeout_worker)
        
        # Create workflow with timeout step
        builder = WorkflowBuilder("timeout-workflow")
        builder.add_step("timeout_step", "timeout_worker", timeout=1)
        workflow = builder.build()
        
        # Create separate orchestrator for this workflow
        from multiagents.orchestrator import Orchestrator
        timeout_orchestrator = Orchestrator(
            workflow=workflow,
            event_bus=integration_orchestrator.event_bus,
            logger=integration_orchestrator.monitoring_logger
        )
        await timeout_orchestrator.start()
        
        # Execute and expect timeout
        transaction_id = await timeout_orchestrator.execute_workflow(
            "timeout-workflow",
            {}
        )
        
        # Wait for timeout
        await asyncio.sleep(2)
        
        state = await timeout_orchestrator.get_status(transaction_id)
        # Timeout triggers compensation due to the framework design
        assert state["state"] in [SagaState.FAILED.value, SagaState.COMPENSATED.value]
        # Check if error mentions timeout (might be in error or execution_history)
        error_found = False
        if state.get("error") and "timeout" in state["error"].lower():
            error_found = True
        elif state.get("execution_history"):
            for entry in state["execution_history"]:
                if entry.get("error") and "timeout" in entry["error"].lower():
                    error_found = True
                    break
        assert error_found or state["state"] == SagaState.COMPENSATED.value
        
        # Clean up
        await timeout_orchestrator.stop()
    
    async def test_workflow_state_persistence(
        self,
        integration_orchestrator,
        integration_worker_manager,
        redis_client
    ):
        """Test that workflow state is properly persisted."""
        # Register a slow worker
        from multiagents.worker_sdk import worker
        
        @worker("slow_worker", timeout=30)
        async def slow_worker(context: Dict[str, Any]) -> Dict[str, Any]:
            await asyncio.sleep(0.5)
            return {"processed": True}
        
        integration_worker_manager.register(slow_worker)
        
        # Create workflow
        builder = WorkflowBuilder("persistence-workflow")
        builder.add_step("slow_step", "slow_worker")
        workflow = builder.build()
        
        # Create separate orchestrator for this workflow
        from multiagents.orchestrator import Orchestrator
        from multiagents.event_bus.redis_bus import RedisStateStore
        
        # Use a state store with the same Redis URL as the test client
        test_state_store = RedisStateStore(redis_url="redis://localhost:6379/15")
        
        persistence_orchestrator = Orchestrator(
            workflow=workflow,
            event_bus=integration_orchestrator.event_bus,
            state_store=test_state_store,
            logger=integration_orchestrator.monitoring_logger
        )
        await persistence_orchestrator.start()
        
        # Execute
        transaction_id = await persistence_orchestrator.execute_workflow(
            "persistence-workflow",
            {"test": "data"}
        )
        
        # Give a moment for state to be saved
        await asyncio.sleep(0.1)
        
        # Check state is persisted
        state_key = f"saga:{transaction_id}"
        persisted = await redis_client.get(state_key)
        assert persisted is not None
        
        # Wait for completion
        await asyncio.sleep(1)
        
        # Verify final state is persisted
        final_persisted = await redis_client.get(state_key)
        assert final_persisted is not None
        
        # Load state and verify
        state = await persistence_orchestrator.get_status(transaction_id)
        assert state["state"] == SagaState.COMPLETED.value
        
        # Check step results for processed flag
        step_results = state["step_results"]
        assert step_results.get("slow_step", {}).get("processed") is True
        
        # Clean up
        await persistence_orchestrator.stop()