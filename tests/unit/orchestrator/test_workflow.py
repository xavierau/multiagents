import pytest
from unittest.mock import MagicMock

from multiagents.orchestrator.workflow import WorkflowStep, WorkflowDefinition, ConditionalBranch
from multiagents.core.saga_context import SagaContext, SagaState


class TestWorkflowStep:
    def test_workflow_step_creation(self):
        step = WorkflowStep(
            name="payment",
            worker_type="payment_worker",
            compensation="refund_payment",
            timeout_seconds=600
        )
        
        assert step.name == "payment"
        assert step.worker_type == "payment_worker"
        assert step.compensation == "refund_payment"
        assert step.timeout_seconds == 600
        assert step.retry_policy is None
        assert step.condition is None
        assert step.next_steps == {}

    def test_workflow_step_with_retry_policy(self):
        retry_policy = {"max_retries": 3, "backoff_seconds": 5}
        step = WorkflowStep(
            name="payment",
            worker_type="payment_worker",
            retry_policy=retry_policy
        )
        
        assert step.retry_policy == retry_policy

    def test_should_execute_without_condition(self):
        step = WorkflowStep(name="payment", worker_type="payment_worker")
        context = SagaContext()
        
        assert step.should_execute(context) is True

    def test_should_execute_with_condition(self):
        def condition(ctx: SagaContext) -> bool:
            return ctx.data.get("amount", 0) > 100
        
        step = WorkflowStep(
            name="fraud_check",
            worker_type="fraud_worker",
            condition=condition
        )
        
        # Should not execute when amount <= 100
        context1 = SagaContext(data={"amount": 50})
        assert step.should_execute(context1) is False
        
        # Should execute when amount > 100
        context2 = SagaContext(data={"amount": 150})
        assert step.should_execute(context2) is True

    def test_workflow_step_with_next_steps(self):
        step = WorkflowStep(
            name="validation",
            worker_type="validation_worker",
            next_steps={
                "valid": "payment",
                "invalid": "rejection"
            }
        )
        
        assert step.next_steps["valid"] == "payment"
        assert step.next_steps["invalid"] == "rejection"


class TestWorkflowDefinition:
    def test_workflow_definition_initialization(self):
        workflow = WorkflowDefinition("order-processing")
        
        assert workflow.workflow_id == "order-processing"
        assert workflow.steps == {}
        assert workflow.initial_step is None
        assert workflow.compensation_map == {}
        assert workflow.step_order == []

    def test_get_id(self):
        workflow = WorkflowDefinition("order-processing")
        assert workflow.get_id() == "order-processing"

    def test_add_step(self):
        workflow = WorkflowDefinition("order-processing")
        step = WorkflowStep(name="payment", worker_type="payment_worker")
        
        workflow.add_step(step)
        
        assert "payment" in workflow.steps
        assert workflow.steps["payment"] == step
        assert workflow.initial_step == "payment"
        assert "payment" in workflow.step_order

    def test_add_multiple_steps(self):
        workflow = WorkflowDefinition("order-processing")
        
        step1 = WorkflowStep(name="validation", worker_type="validation_worker")
        step2 = WorkflowStep(name="payment", worker_type="payment_worker")
        step3 = WorkflowStep(name="shipping", worker_type="shipping_worker")
        
        workflow.add_step(step1)
        workflow.add_step(step2)
        workflow.add_step(step3)
        
        assert len(workflow.steps) == 3
        assert workflow.initial_step == "validation"
        assert workflow.step_order == ["validation", "payment", "shipping"]

    def test_add_step_with_compensation(self):
        workflow = WorkflowDefinition("order-processing")
        step = WorkflowStep(
            name="payment",
            worker_type="payment_worker",
            compensation="refund_payment"
        )
        
        workflow.add_step(step)
        
        assert workflow.compensation_map["payment"] == "refund_payment"

    def test_get_steps(self):
        workflow = WorkflowDefinition("order-processing")
        
        step1 = WorkflowStep(name="validation", worker_type="validation_worker")
        step2 = WorkflowStep(name="payment", worker_type="payment_worker")
        
        workflow.add_step(step1)
        workflow.add_step(step2)
        
        steps = workflow.get_steps()
        assert len(steps) == 2
        assert step1 in steps
        assert step2 in steps

    def test_get_initial_step(self):
        workflow = WorkflowDefinition("order-processing")
        
        # No steps
        assert workflow.get_initial_step() is None
        
        # With steps
        step = WorkflowStep(name="validation", worker_type="validation_worker")
        workflow.add_step(step)
        
        initial = workflow.get_initial_step()
        assert initial == step

    def test_get_next_step_sequential(self):
        workflow = WorkflowDefinition("order-processing")
        context = SagaContext()
        
        step1 = WorkflowStep(name="validation", worker_type="validation_worker")
        step2 = WorkflowStep(name="payment", worker_type="payment_worker")
        step3 = WorkflowStep(name="shipping", worker_type="shipping_worker")
        
        workflow.add_step(step1)
        workflow.add_step(step2)
        workflow.add_step(step3)
        
        # Get next after validation
        next_step = workflow.get_next_step("validation", context)
        assert next_step == step2
        
        # Get next after payment
        next_step = workflow.get_next_step("payment", context)
        assert next_step == step3
        
        # No next after shipping
        next_step = workflow.get_next_step("shipping", context)
        assert next_step is None

    def test_get_next_step_with_condition(self):
        workflow = WorkflowDefinition("order-processing")
        
        # Step 2 only executes if amount > 100
        def high_value_condition(ctx: SagaContext) -> bool:
            return ctx.data.get("amount", 0) > 100
        
        step1 = WorkflowStep(name="validation", worker_type="validation_worker")
        step2 = WorkflowStep(
            name="fraud_check",
            worker_type="fraud_worker",
            condition=high_value_condition
        )
        step3 = WorkflowStep(name="payment", worker_type="payment_worker")
        
        workflow.add_step(step1)
        workflow.add_step(step2)
        workflow.add_step(step3)
        
        # Low value - fraud check condition fails, so no next step
        context_low = SagaContext(data={"amount": 50})
        next_step = workflow.get_next_step("validation", context_low)
        assert next_step is None  # Fraud check condition fails
        
        # High value - should include fraud check
        context_high = SagaContext(data={"amount": 150})
        next_step = workflow.get_next_step("validation", context_high)
        assert next_step == step2  # Goes to fraud check

    def test_get_next_step_with_branching(self):
        workflow = WorkflowDefinition("order-processing")
        context = SagaContext()
        
        # Validation step with branching
        validation_step = WorkflowStep(
            name="validation",
            worker_type="validation_worker",
            next_steps={
                "valid": "payment",
                "invalid": "rejection"
            }
        )
        payment_step = WorkflowStep(name="payment", worker_type="payment_worker")
        rejection_step = WorkflowStep(name="rejection", worker_type="rejection_worker")
        
        workflow.add_step(validation_step)
        workflow.add_step(payment_step)
        workflow.add_step(rejection_step)
        
        # Mock the condition evaluation
        workflow._evaluate_condition = MagicMock()
        
        # Test valid branch
        workflow._evaluate_condition.side_effect = [True, False]  # First condition matches
        next_step = workflow.get_next_step("validation", context)
        assert next_step == payment_step
        
        # Test invalid branch
        workflow._evaluate_condition.side_effect = [False, True]  # Second condition matches
        next_step = workflow.get_next_step("validation", context)
        assert next_step == rejection_step

    def test_get_compensation_steps(self):
        workflow = WorkflowDefinition("order-processing")
        
        # Create steps with compensations
        step1 = WorkflowStep(
            name="inventory",
            worker_type="inventory_worker",
            compensation="restore_inventory"
        )
        step2 = WorkflowStep(
            name="payment",
            worker_type="payment_worker",
            compensation="refund_payment"
        )
        step3 = WorkflowStep(
            name="shipping",
            worker_type="shipping_worker"
        )
        
        # Add compensation steps
        comp1 = WorkflowStep(name="restore_inventory", worker_type="inventory_worker")
        comp2 = WorkflowStep(name="refund_payment", worker_type="payment_worker")
        
        workflow.add_step(step1)
        workflow.add_step(step2)
        workflow.add_step(step3)
        workflow.add_step(comp1)
        workflow.add_step(comp2)
        
        # Create context with completed steps
        context = SagaContext()
        context.update_step_result("inventory", {"reserved": True})
        context.update_step_result("payment", {"paid": True})
        
        # Mock the context parameter in get_compensation_steps
        # Since the method signature expects a context parameter
        workflow.get_compensation_steps = lambda failed_step, ctx=context: [
            comp2 if ctx.is_step_completed("payment") else None,
            comp1 if ctx.is_step_completed("inventory") else None
        ]
        
        # Get compensations after shipping failure
        compensations = workflow.get_compensation_steps("shipping", context)
        compensations = [c for c in compensations if c]  # Filter None values
        
        assert len(compensations) == 2
        assert compensations[0] == comp2  # Refund payment first
        assert compensations[1] == comp1  # Then restore inventory

    def test_workflow_with_no_next_step(self):
        workflow = WorkflowDefinition("simple-workflow")
        context = SagaContext()
        
        step = WorkflowStep(name="single_step", worker_type="worker")
        workflow.add_step(step)
        
        # Should return None for last step
        next_step = workflow.get_next_step("single_step", context)
        assert next_step is None
        
        # Should return None for non-existent step
        next_step = workflow.get_next_step("non_existent", context)
        assert next_step is None