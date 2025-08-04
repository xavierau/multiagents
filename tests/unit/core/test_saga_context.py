import pytest
from datetime import datetime
from uuid import UUID

from multiagents.core.saga_context import SagaContext, SagaState, StepExecution


class TestStepExecution:
    def test_step_execution_creation(self):
        step = StepExecution(
            step_name="payment",
            status="started",
            started_at=datetime.utcnow()
        )
        
        assert step.step_name == "payment"
        assert step.status == "started"
        assert isinstance(step.started_at, datetime)
        assert step.completed_at is None
        assert step.result is None
        assert step.error is None
        assert step.command_id is None

    def test_step_execution_with_all_fields(self):
        now = datetime.utcnow()
        step = StepExecution(
            step_name="payment",
            status="completed",
            started_at=now,
            completed_at=now,
            result={"transaction_id": "pay-123"},
            error=None,
            command_id="cmd-456"
        )
        
        assert step.result == {"transaction_id": "pay-123"}
        assert step.command_id == "cmd-456"
        assert step.completed_at == now


class TestSagaContext:
    def test_saga_context_initialization(self):
        context = SagaContext()
        
        assert UUID(context.transaction_id)  # Should be valid UUID
        assert context.workflow_id == ""
        assert context.state == SagaState.PENDING
        assert context.current_step is None
        assert context.data == {}
        assert context.step_results == {}
        assert context.execution_history == []
        assert isinstance(context.created_at, datetime)
        assert isinstance(context.updated_at, datetime)
        assert context.error is None
        assert context.metadata == {}

    def test_saga_context_with_custom_values(self):
        context = SagaContext(
            transaction_id="trans-123",
            workflow_id="order-processing",
            state=SagaState.RUNNING,
            current_step="payment",
            data={"order_id": "order-456"},
            metadata={"user_id": "user-789"}
        )
        
        assert context.transaction_id == "trans-123"
        assert context.workflow_id == "order-processing"
        assert context.state == SagaState.RUNNING
        assert context.current_step == "payment"
        assert context.data == {"order_id": "order-456"}
        assert context.metadata == {"user_id": "user-789"}

    def test_update_step_result(self):
        context = SagaContext()
        before_update = context.updated_at
        
        context.update_step_result("payment", {"transaction_id": "pay-123", "amount": 100})
        
        assert context.step_results["payment"] == {"transaction_id": "pay-123", "amount": 100}
        assert context.data == {"transaction_id": "pay-123", "amount": 100}
        assert context.updated_at > before_update

    def test_update_step_result_merges_data(self):
        context = SagaContext(data={"order_id": "order-456"})
        
        context.update_step_result("payment", {"transaction_id": "pay-123"})
        
        assert context.data == {"order_id": "order-456", "transaction_id": "pay-123"}

    def test_record_step_start(self):
        context = SagaContext()
        
        context.record_step_start("payment", "cmd-789")
        
        assert context.current_step == "payment"
        assert len(context.execution_history) == 1
        
        execution = context.execution_history[0]
        assert execution.step_name == "payment"
        assert execution.status == "started"
        assert execution.command_id == "cmd-789"
        assert isinstance(execution.started_at, datetime)

    def test_record_step_completion(self):
        context = SagaContext()
        context.record_step_start("payment", "cmd-789")
        
        result = {"transaction_id": "pay-123", "amount": 100}
        context.record_step_completion("payment", result)
        
        execution = context.execution_history[0]
        assert execution.status == "completed"
        assert execution.result == result
        assert execution.completed_at is not None
        assert context.step_results["payment"] == result

    def test_record_step_failure(self):
        context = SagaContext()
        context.record_step_start("payment", "cmd-789")
        
        context.record_step_failure("payment", "Payment gateway error")
        
        execution = context.execution_history[0]
        assert execution.status == "failed"
        assert execution.error == "Payment gateway error"
        assert execution.completed_at is not None
        assert context.error == "Payment gateway error"
        assert context.state == SagaState.FAILED

    def test_get_step_result(self):
        context = SagaContext()
        context.update_step_result("payment", {"transaction_id": "pay-123"})
        
        result = context.get_step_result("payment")
        assert result == {"transaction_id": "pay-123"}
        
        # Non-existent step
        assert context.get_step_result("shipping") is None

    def test_is_step_completed(self):
        context = SagaContext()
        context.update_step_result("payment", {"transaction_id": "pay-123"})
        
        assert context.is_step_completed("payment") is True
        assert context.is_step_completed("shipping") is False

    def test_multiple_step_executions(self):
        context = SagaContext()
        
        # Execute multiple steps
        context.record_step_start("validation", "cmd-1")
        context.record_step_completion("validation", {"valid": True})
        
        context.record_step_start("payment", "cmd-2")
        context.record_step_completion("payment", {"transaction_id": "pay-123"})
        
        context.record_step_start("shipping", "cmd-3")
        context.record_step_failure("shipping", "Out of stock")
        
        assert len(context.execution_history) == 3
        assert context.execution_history[0].status == "completed"
        assert context.execution_history[1].status == "completed"
        assert context.execution_history[2].status == "failed"
        assert context.state == SagaState.FAILED
        assert context.current_step == "shipping"

    def test_to_dict_serialization(self):
        context = SagaContext(
            transaction_id="trans-123",
            workflow_id="order-processing",
            state=SagaState.RUNNING
        )
        
        context.record_step_start("payment", "cmd-789")
        context.record_step_completion("payment", {"transaction_id": "pay-123"})
        
        dict_repr = context.to_dict()
        
        assert dict_repr["transaction_id"] == "trans-123"
        assert dict_repr["workflow_id"] == "order-processing"
        assert dict_repr["state"] == "running"
        assert dict_repr["step_results"]["payment"] == {"transaction_id": "pay-123"}
        assert len(dict_repr["execution_history"]) == 1
        
        # Check execution history serialization
        exec_dict = dict_repr["execution_history"][0]
        assert exec_dict["step_name"] == "payment"
        assert exec_dict["status"] == "completed"
        assert exec_dict["command_id"] == "cmd-789"
        assert exec_dict["result"] == {"transaction_id": "pay-123"}

    def test_saga_state_transitions(self):
        context = SagaContext()
        
        # Initial state
        assert context.state == SagaState.PENDING
        
        # Can be set to running
        context.state = SagaState.RUNNING
        assert context.state == SagaState.RUNNING
        
        # Failure sets state to failed
        context.record_step_failure("payment", "Error")
        assert context.state == SagaState.FAILED
        
        # Can transition to compensating
        context.state = SagaState.COMPENSATING
        assert context.state == SagaState.COMPENSATING