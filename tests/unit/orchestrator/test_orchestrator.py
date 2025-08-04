"""
Comprehensive unit tests for the Orchestrator class.
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock, ANY
from datetime import datetime
from multiagents.orchestrator.orchestrator import Orchestrator
from multiagents.orchestrator.interface import IWorkflowDefinition, IStateStore
from multiagents.event_bus.interface import IEventBus
from multiagents.event_bus.events import (
    CommandEvent, ResultEvent, StatusEvent, CompensationEvent,
    EventMetadata
)
from multiagents.event_bus.redis_bus import RedisStateStore
from multiagents.core.saga_context import SagaContext, SagaState, StepExecution
from multiagents.core.exceptions import WorkflowException


class TestOrchestratorInitialization:
    """Test cases for Orchestrator initialization."""
    
    def test_init_with_required_params(self):
        """Test initialization with required parameters."""
        # Arrange
        workflow = Mock(spec=IWorkflowDefinition)
        event_bus = Mock(spec=IEventBus)
        
        # Act
        orchestrator = Orchestrator(workflow=workflow, event_bus=event_bus)
        
        # Assert
        assert orchestrator.workflow == workflow
        assert orchestrator.event_bus == event_bus
        assert isinstance(orchestrator.state_store, RedisStateStore)
        assert orchestrator.active_workflows == {}
        assert orchestrator._running is False
        assert orchestrator.monitoring_logger is not None
    
    def test_init_with_custom_state_store(self):
        """Test initialization with custom state store."""
        # Arrange
        workflow = Mock(spec=IWorkflowDefinition)
        event_bus = Mock(spec=IEventBus)
        state_store = Mock(spec=IStateStore)
        
        # Act
        orchestrator = Orchestrator(
            workflow=workflow,
            event_bus=event_bus,
            state_store=state_store
        )
        
        # Assert
        assert orchestrator.state_store == state_store
    
    def test_init_with_custom_logger(self):
        """Test initialization with custom logger."""
        # Arrange
        workflow = Mock(spec=IWorkflowDefinition)
        event_bus = Mock(spec=IEventBus)
        logger = Mock()
        
        # Act
        orchestrator = Orchestrator(
            workflow=workflow,
            event_bus=event_bus,
            logger=logger
        )
        
        # Assert
        assert orchestrator.monitoring_logger == logger
    
    @patch('multiagents.monitoring.config.MonitoringConfig')
    def test_init_with_monitoring_config(self, mock_monitoring_config):
        """Test initialization with monitoring config."""
        # Arrange
        workflow = Mock(spec=IWorkflowDefinition)
        event_bus = Mock(spec=IEventBus)
        monitoring_config = Mock()
        custom_logger = Mock()
        # The actual implementation uses the passed monitoring_config, not the patched one
        monitoring_config.create_logger = Mock(return_value=custom_logger)
        
        # Act
        orchestrator = Orchestrator(
            workflow=workflow,
            event_bus=event_bus,
            monitoring_config=monitoring_config
        )
        
        # Assert
        assert orchestrator.monitoring_logger == custom_logger


class TestOrchestratorLifecycle:
    """Test cases for orchestrator start/stop lifecycle."""
    
    @pytest.mark.asyncio
    async def test_start_with_redis_state_store(self):
        """Test starting orchestrator with Redis state store."""
        # Arrange
        workflow = Mock(spec=IWorkflowDefinition)
        step1 = Mock(name="step1", worker_type="worker1")
        step2 = Mock(name="step2", worker_type="worker2")
        workflow.get_steps.return_value = [step1, step2]
        workflow.get_id.return_value = "test-workflow"
        
        event_bus = AsyncMock(spec=IEventBus)
        state_store = AsyncMock(spec=RedisStateStore)
        
        orchestrator = Orchestrator(
            workflow=workflow,
            event_bus=event_bus,
            state_store=state_store
        )
        
        # Act
        await orchestrator.start()
        
        # Assert
        state_store.connect.assert_called_once()
        assert event_bus.subscribe.call_count == 2
        event_bus.subscribe.assert_any_call("result.worker1", orchestrator._handle_result_event)
        event_bus.subscribe.assert_any_call("result.worker2", orchestrator._handle_result_event)
        assert orchestrator._running is True
    
    @pytest.mark.asyncio
    async def test_start_with_non_redis_state_store(self):
        """Test starting orchestrator with non-Redis state store."""
        # Arrange
        workflow = Mock(spec=IWorkflowDefinition)
        workflow.get_steps.return_value = []
        workflow.get_id.return_value = "test-workflow"
        
        event_bus = AsyncMock(spec=IEventBus)
        state_store = Mock(spec=IStateStore)  # Not RedisStateStore
        
        orchestrator = Orchestrator(
            workflow=workflow,
            event_bus=event_bus,
            state_store=state_store
        )
        
        # Act
        await orchestrator.start()
        
        # Assert
        # Should not call connect on non-Redis store
        assert not hasattr(state_store, 'connect') or state_store.connect.call_count == 0
        assert orchestrator._running is True
    
    @pytest.mark.asyncio
    async def test_stop_with_redis_state_store(self):
        """Test stopping orchestrator with Redis state store."""
        # Arrange
        workflow = Mock(spec=IWorkflowDefinition)
        workflow.get_id.return_value = "test-workflow"
        event_bus = AsyncMock(spec=IEventBus)
        state_store = AsyncMock(spec=RedisStateStore)
        
        orchestrator = Orchestrator(
            workflow=workflow,
            event_bus=event_bus,
            state_store=state_store
        )
        orchestrator._running = True
        
        # Act
        await orchestrator.stop()
        
        # Assert
        assert orchestrator._running is False
        state_store.disconnect.assert_called_once()


class TestExecuteWorkflow:
    """Test cases for execute_workflow method."""
    
    @pytest.mark.asyncio
    async def test_execute_workflow_success(self):
        """Test successful workflow execution."""
        # Arrange
        initial_step = Mock(name="step1", worker_type="worker1")
        workflow = Mock(spec=IWorkflowDefinition)
        workflow.get_initial_step.return_value = initial_step
        workflow.get_id.return_value = "test-workflow"
        
        event_bus = AsyncMock(spec=IEventBus)
        state_store = AsyncMock(spec=IStateStore)
        
        orchestrator = Orchestrator(
            workflow=workflow,
            event_bus=event_bus,
            state_store=state_store
        )
        
        initial_context = {"input": "data"}
        workflow_id = "workflow-123"
        
        # Act
        with patch.object(orchestrator, '_execute_step', new_callable=AsyncMock) as mock_execute:
            with patch.object(orchestrator, '_publish_status_event', new_callable=AsyncMock) as mock_status:
                transaction_id = await orchestrator.execute_workflow(workflow_id, initial_context)
        
        # Assert
        assert transaction_id in orchestrator.active_workflows
        context = orchestrator.active_workflows[transaction_id]
        assert context.workflow_id == workflow_id
        assert context.data == initial_context
        assert context.state == SagaState.RUNNING
        
        state_store.save_context.assert_called_once_with(context)
        mock_status.assert_called_once()
        mock_execute.assert_called_once_with(context, initial_step)
    
    @pytest.mark.asyncio
    async def test_execute_workflow_no_initial_step(self):
        """Test workflow execution with no initial step."""
        # Arrange
        workflow = Mock(spec=IWorkflowDefinition)
        workflow.get_initial_step.return_value = None
        workflow.get_id.return_value = "test-workflow"
        
        event_bus = AsyncMock(spec=IEventBus)
        state_store = AsyncMock(spec=IStateStore)
        orchestrator = Orchestrator(workflow=workflow, event_bus=event_bus, state_store=state_store)
        
        # Act & Assert
        with pytest.raises(WorkflowException, match="No initial step defined"):
            await orchestrator.execute_workflow("workflow-123", {})


class TestGetStatus:
    """Test cases for get_status method."""
    
    @pytest.mark.asyncio
    async def test_get_status_from_memory(self):
        """Test getting status for active workflow in memory."""
        # Arrange
        workflow = Mock(spec=IWorkflowDefinition)
        event_bus = AsyncMock(spec=IEventBus)
        orchestrator = Orchestrator(workflow=workflow, event_bus=event_bus)
        
        transaction_id = "txn-123"
        context = SagaContext(
            workflow_id="workflow-123",
            data={"test": "data"},
            state=SagaState.RUNNING
        )
        context.transaction_id = transaction_id
        context.current_step = "step1"
        orchestrator.active_workflows[transaction_id] = context
        
        # Act
        status = await orchestrator.get_status(transaction_id)
        
        # Assert
        assert status["transaction_id"] == transaction_id
        assert status["workflow_id"] == "workflow-123"
        assert status["state"] == "running"
        assert status["current_step"] == "step1"
        assert "created_at" in status
        assert "updated_at" in status
    
    @pytest.mark.asyncio
    async def test_get_status_from_store(self):
        """Test getting status for persisted workflow."""
        # Arrange
        workflow = Mock(spec=IWorkflowDefinition)
        event_bus = AsyncMock(spec=IEventBus)
        state_store = AsyncMock(spec=IStateStore)
        
        orchestrator = Orchestrator(
            workflow=workflow,
            event_bus=event_bus,
            state_store=state_store
        )
        
        transaction_id = "txn-123"
        context_data = {
            "transaction_id": transaction_id,
            "workflow_id": "workflow-123",
            "state": "running",
            "current_step": "step1",
            "data": {"test": "data"},
            "step_results": {},
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
            "execution_history": []
        }
        state_store.load_context.return_value = context_data
        
        # Act
        with patch.object(orchestrator, '_reconstruct_context') as mock_reconstruct:
            mock_context = Mock()
            mock_context.transaction_id = transaction_id
            mock_context.workflow_id = "workflow-123"
            mock_context.state = SagaState.RUNNING
            mock_context.current_step = "step1"
            mock_context.created_at = datetime.utcnow()
            mock_context.updated_at = datetime.utcnow()
            mock_context.step_results = {}
            mock_context.error = None
            mock_context.execution_history = []
            mock_reconstruct.return_value = mock_context
            
            status = await orchestrator.get_status(transaction_id)
        
        # Assert
        state_store.load_context.assert_called_once_with(transaction_id)
        assert status["transaction_id"] == transaction_id
        assert status["workflow_id"] == "workflow-123"
    
    @pytest.mark.asyncio
    async def test_get_status_not_found(self):
        """Test getting status for non-existent workflow."""
        # Arrange
        workflow = Mock(spec=IWorkflowDefinition)
        event_bus = AsyncMock(spec=IEventBus)
        state_store = AsyncMock(spec=IStateStore)
        state_store.load_context.return_value = None
        
        orchestrator = Orchestrator(
            workflow=workflow,
            event_bus=event_bus,
            state_store=state_store
        )
        
        # Act & Assert
        with pytest.raises(WorkflowException, match="Workflow.*not found"):
            await orchestrator.get_status("nonexistent-txn")


class TestCancelWorkflow:
    """Test cases for cancel_workflow method."""
    
    @pytest.mark.asyncio
    async def test_cancel_workflow_success(self):
        """Test successful workflow cancellation."""
        # Arrange
        workflow = Mock(spec=IWorkflowDefinition)
        event_bus = AsyncMock(spec=IEventBus)
        state_store = AsyncMock(spec=IStateStore)
        
        orchestrator = Orchestrator(
            workflow=workflow,
            event_bus=event_bus,
            state_store=state_store
        )
        
        transaction_id = "txn-123"
        context = SagaContext(
            workflow_id="workflow-123",
            data={"test": "data"},
            state=SagaState.RUNNING
        )
        context.transaction_id = transaction_id
        context.current_step = "step1"
        
        with patch.object(orchestrator, '_load_context', new_callable=AsyncMock) as mock_load:
            mock_load.return_value = context
            with patch.object(orchestrator, '_trigger_compensations', new_callable=AsyncMock) as mock_comp:
                with patch.object(orchestrator, '_publish_status_event', new_callable=AsyncMock) as mock_status:
                    # Act
                    result = await orchestrator.cancel_workflow(transaction_id)
        
        # Assert
        assert result is True
        assert context.state == SagaState.CANCELLED
        state_store.save_context.assert_called_once_with(context)
        mock_comp.assert_called_once_with(context)
        mock_status.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_cancel_workflow_not_found(self):
        """Test cancelling non-existent workflow."""
        # Arrange
        workflow = Mock(spec=IWorkflowDefinition)
        event_bus = AsyncMock(spec=IEventBus)
        orchestrator = Orchestrator(workflow=workflow, event_bus=event_bus)
        
        with patch.object(orchestrator, '_load_context', new_callable=AsyncMock) as mock_load:
            mock_load.return_value = None
            
            # Act
            result = await orchestrator.cancel_workflow("nonexistent-txn")
        
        # Assert
        assert result is False


class TestExecuteStep:
    """Test cases for _execute_step method."""
    
    @pytest.mark.asyncio
    async def test_execute_step_success(self):
        """Test successful step execution."""
        # Arrange
        workflow = Mock(spec=IWorkflowDefinition)
        workflow.get_id.return_value = "test-workflow"
        event_bus = AsyncMock(spec=IEventBus)
        state_store = AsyncMock(spec=IStateStore)
        
        orchestrator = Orchestrator(
            workflow=workflow,
            event_bus=event_bus,
            state_store=state_store
        )
        
        context = SagaContext(
            workflow_id="workflow-123",
            data={"input": "data"},
            state=SagaState.RUNNING
        )
        
        step = Mock()
        step.name = "step1"
        step.worker_type = "worker1"
        step.timeout_seconds = 30
        step.retry_policy = None
        
        # Act
        await orchestrator._execute_step(context, step)
        
        # Assert
        # Verify command event was published
        event_bus.publish.assert_called_once()
        call_args = event_bus.publish.call_args
        assert call_args[0][0] == "command.worker1"
        
        # Verify context was updated
        assert len(context.execution_history) == 1
        assert context.execution_history[0].step_name == "step1"
        assert context.execution_history[0].status == "started"
        
        # Verify state was saved
        state_store.save_context.assert_called_with(context)
    
    @pytest.mark.asyncio
    async def test_execute_step_failure(self):
        """Test step execution failure."""
        # Arrange
        workflow = Mock(spec=IWorkflowDefinition)
        workflow.get_id = Mock(return_value="test-workflow")
        event_bus = AsyncMock(spec=IEventBus)
        event_bus.publish.side_effect = Exception("Publish failed")
        state_store = AsyncMock(spec=IStateStore)
        
        orchestrator = Orchestrator(
            workflow=workflow,
            event_bus=event_bus,
            state_store=state_store
        )
        
        context = SagaContext(
            workflow_id="workflow-123",
            data={"input": "data"},
            state=SagaState.RUNNING
        )
        
        step = Mock()
        step.name = "step1"
        step.worker_type = "worker1"
        step.timeout_seconds = 30
        step.retry_policy = None
        
        with patch.object(orchestrator, '_trigger_compensations', new_callable=AsyncMock) as mock_comp:
            # Act
            await orchestrator._execute_step(context, step)
        
        # Assert
        # When publish fails early, the step might not be recorded in history
        # But the context state should be failed and compensations triggered
        assert context.state == SagaState.FAILED
        assert context.error is not None
        assert "Publish failed" in str(context.error)
        
        # Verify compensations were triggered
        mock_comp.assert_called_once_with(context)


class TestHandleResultEvent:
    """Test cases for _handle_result_event method."""
    
    @pytest.mark.asyncio
    async def test_handle_result_success_with_next_step(self):
        """Test handling successful result with next step."""
        # Arrange
        step1 = Mock()
        step1.name = "step1"
        step1.worker_type = "worker1"
        step2 = Mock()
        step2.name = "step2"
        step2.worker_type = "worker2"
        
        workflow = Mock(spec=IWorkflowDefinition)
        workflow.get_steps.return_value = [step1, step2]
        workflow.get_next_step.return_value = step2
        
        event_bus = AsyncMock(spec=IEventBus)
        orchestrator = Orchestrator(workflow=workflow, event_bus=event_bus)
        
        context = SagaContext(
            workflow_id="workflow-123",
            data={"input": "data"},
            state=SagaState.RUNNING
        )
        context.current_step = "step1"
        context.record_step_start("step1", "cmd-123")
        
        result_event = {
            "metadata": {
                "transaction_id": context.transaction_id,
                "correlation_id": "corr-123",
                "source": "test-worker"
            },
            "command_id": "cmd-123",
            "success": True,
            "payload": {"result": "data"}
        }
        
        with patch.object(orchestrator, '_load_context', new_callable=AsyncMock) as mock_load:
            mock_load.return_value = context
            with patch.object(orchestrator, '_execute_step', new_callable=AsyncMock) as mock_execute:
                # Act
                await orchestrator._handle_result_event(result_event)
        
        # Assert
        # Verify step completion was recorded
        # The record_step_completion should have been called
        assert "step1" in context.step_results
        assert context.step_results["step1"] == {"result": "data"}
        
        # Verify next step was executed
        mock_execute.assert_called_once_with(context, step2)
    
    @pytest.mark.asyncio
    async def test_handle_result_success_workflow_complete(self):
        """Test handling successful result that completes workflow."""
        # Arrange
        step1 = Mock()
        step1.name = "step1"
        step1.worker_type = "worker1"
        
        workflow = Mock(spec=IWorkflowDefinition)
        workflow.get_steps.return_value = [step1]
        workflow.get_next_step.return_value = None  # No next step
        
        event_bus = AsyncMock(spec=IEventBus)
        state_store = AsyncMock(spec=IStateStore)
        
        orchestrator = Orchestrator(
            workflow=workflow,
            event_bus=event_bus,
            state_store=state_store
        )
        
        context = SagaContext(
            workflow_id="workflow-123",
            data={"input": "data"},
            state=SagaState.RUNNING
        )
        context.current_step = "step1"
        context.record_step_start("step1", "cmd-123")
        orchestrator.active_workflows[context.transaction_id] = context
        
        result_event = {
            "metadata": {
                "transaction_id": context.transaction_id,
                "correlation_id": "corr-123",
                "source": "test-worker"
            },
            "command_id": "cmd-123",
            "success": True,
            "payload": {"result": "data"}
        }
        
        with patch.object(orchestrator, '_load_context', new_callable=AsyncMock) as mock_load:
            mock_load.return_value = context
            with patch.object(orchestrator, '_publish_status_event', new_callable=AsyncMock) as mock_status:
                # Act
                await orchestrator._handle_result_event(result_event)
        
        # Assert
        # Check the workflow was completed
        mock_load.assert_called_once_with(context.transaction_id)
        state_store.save_context.assert_called()
        mock_status.assert_called_once()
        assert context.transaction_id not in orchestrator.active_workflows
        state_store.save_context.assert_called_with(context)
        mock_status.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_handle_result_failure(self):
        """Test handling failed result."""
        # Arrange
        step1 = Mock()
        step1.name = "step1"
        step1.worker_type = "worker1"
        
        workflow = Mock(spec=IWorkflowDefinition)
        workflow.get_steps.return_value = [step1]
        
        event_bus = AsyncMock(spec=IEventBus)
        state_store = AsyncMock(spec=IStateStore)
        
        orchestrator = Orchestrator(
            workflow=workflow,
            event_bus=event_bus,
            state_store=state_store
        )
        
        context = SagaContext(
            workflow_id="workflow-123",
            data={"input": "data"},
            state=SagaState.RUNNING
        )
        context.current_step = "step1"
        context.record_step_start("step1", "cmd-123")
        
        result_event = {
            "metadata": {
                "transaction_id": context.transaction_id,
                "correlation_id": "corr-123",
                "source": "test-worker"
            },
            "command_id": "cmd-123",
            "success": False,
            "error_message": "Worker failed"
        }
        
        with patch.object(orchestrator, '_load_context', new_callable=AsyncMock) as mock_load:
            mock_load.return_value = context
            with patch.object(orchestrator, '_trigger_compensations', new_callable=AsyncMock) as mock_comp:
                # Act
                await orchestrator._handle_result_event(result_event)
        
        # Assert
        # The record_step_failure should have been called
        state_store.save_context.assert_called_with(context)
        mock_comp.assert_called_once_with(context)
        state_store.save_context.assert_called_with(context)
        mock_comp.assert_called_once_with(context)


class TestTriggerCompensations:
    """Test cases for _trigger_compensations method."""
    
    @pytest.mark.asyncio
    async def test_trigger_compensations_with_completed_steps(self):
        """Test triggering compensations for completed steps."""
        # Arrange
        step1 = Mock()
        step1.name = "step1"
        step1.worker_type = "worker1"
        step1.compensation = "comp1"
        step2 = Mock()
        step2.name = "step2"
        step2.worker_type = "worker2"
        step2.compensation = "comp2"
        step3 = Mock()
        step3.name = "step3"
        step3.worker_type = "worker3"
        step3.compensation = None
        
        workflow = Mock(spec=IWorkflowDefinition)
        workflow.get_steps.return_value = [step1, step2, step3]
        workflow.get_id.return_value = "test-workflow"
        
        event_bus = AsyncMock(spec=IEventBus)
        state_store = AsyncMock(spec=IStateStore)
        
        orchestrator = Orchestrator(
            workflow=workflow,
            event_bus=event_bus,
            state_store=state_store
        )
        
        context = SagaContext(
            workflow_id="workflow-123",
            data={"input": "data"},
            state=SagaState.RUNNING
        )
        
        # Add execution history
        exec1 = StepExecution(
            step_name="step1",
            status="completed",
            started_at=datetime.utcnow(),
            completed_at=datetime.utcnow(),
            command_id="cmd1"
        )
        exec2 = StepExecution(
            step_name="step2",
            status="completed",
            started_at=datetime.utcnow(),
            completed_at=datetime.utcnow(),
            command_id="cmd2"
        )
        exec3 = StepExecution(
            step_name="step3",
            status="failed",
            started_at=datetime.utcnow(),
            error="Failed"
        )
        context.execution_history = [exec1, exec2, exec3]
        
        with patch.object(orchestrator, '_publish_status_event', new_callable=AsyncMock):
            # Act
            await orchestrator._trigger_compensations(context)
        
        # Assert
        # Check that compensations were triggered
        assert event_bus.publish.call_count == 2
        
        # Verify state transitions
        assert state_store.save_context.call_count >= 2
        calls = event_bus.publish.call_args_list
        
        # First compensation should be for step2
        assert calls[0][0][0] == "compensation.comp2"
        comp_event = calls[0][0][1]
        assert comp_event["original_command_id"] == "cmd2"
        
        # Second compensation should be for step1
        assert calls[1][0][0] == "compensation.comp1"
        comp_event = calls[1][0][1]
        assert comp_event["original_command_id"] == "cmd1"


class TestReconstructContext:
    """Test cases for _reconstruct_context method."""
    
    def test_reconstruct_context_complete(self):
        """Test reconstructing context from complete data."""
        # Arrange
        workflow = Mock(spec=IWorkflowDefinition)
        event_bus = AsyncMock(spec=IEventBus)
        orchestrator = Orchestrator(workflow=workflow, event_bus=event_bus)
        
        data = {
            "transaction_id": "txn-123",
            "workflow_id": "workflow-123",
            "state": "running",
            "current_step": "step1",
            "data": {"input": "data"},
            "step_results": {"step0": {"result": "data"}},
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
            "error": None,
            "metadata": {"key": "value"},
            "execution_history": [
                {
                    "step_name": "step0",
                    "status": "completed",
                    "started_at": datetime.utcnow().isoformat(),
                    "completed_at": datetime.utcnow().isoformat(),
                    "result": {"result": "data"},
                    "command_id": "cmd-123"
                }
            ]
        }
        
        # Act
        context = orchestrator._reconstruct_context(data)
        
        # Assert
        assert context.transaction_id == "txn-123"
        assert context.workflow_id == "workflow-123"
        assert context.state == SagaState.RUNNING
        assert context.current_step == "step1"
        assert context.data == {"input": "data"}
        assert context.step_results == {"step0": {"result": "data"}}
        assert context.metadata == {"key": "value"}
        assert len(context.execution_history) == 1
        assert context.execution_history[0].step_name == "step0"
        assert context.execution_history[0].status == "completed"