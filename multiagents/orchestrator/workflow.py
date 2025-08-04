from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List, Callable
from ..core.saga_context import SagaContext
from .interface import IWorkflowDefinition


@dataclass
class WorkflowStep:
    """Represents a single step in a workflow."""
    name: str
    worker_type: str
    compensation: Optional[str] = None
    timeout_seconds: int = 300
    retry_policy: Optional[Dict[str, Any]] = None
    condition: Optional[Callable[[SagaContext], bool]] = None
    next_steps: Dict[str, str] = field(default_factory=dict)  # condition_result -> step_name

    def should_execute(self, context: SagaContext) -> bool:
        """Check if this step should execute based on condition."""
        if self.condition is None:
            return True
        return self.condition(context)


@dataclass
class ConditionalBranch:
    """Represents a conditional branch in the workflow."""
    condition: str  # Expression to evaluate
    true_step: str
    false_step: str


class WorkflowDefinition(IWorkflowDefinition):
    """
    Concrete implementation of workflow definition.
    Follows Single Responsibility Principle - only manages workflow structure.
    """

    def __init__(self, workflow_id: str):
        self.workflow_id = workflow_id
        self.steps: Dict[str, WorkflowStep] = {}
        self.initial_step: Optional[str] = None
        self.compensation_map: Dict[str, str] = {}
        self.step_order: List[str] = []

    def get_id(self) -> str:
        return self.workflow_id

    def get_steps(self) -> List[WorkflowStep]:
        return list(self.steps.values())

    def get_initial_step(self) -> Optional[WorkflowStep]:
        if self.initial_step:
            return self.steps.get(self.initial_step)
        return None

    def add_step(self, step: WorkflowStep) -> None:
        """Add a step to the workflow."""
        self.steps[step.name] = step
        self.step_order.append(step.name)
        if self.initial_step is None:
            self.initial_step = step.name
        if step.compensation:
            self.compensation_map[step.name] = step.compensation

    def get_next_step(self, current_step: str, context: SagaContext) -> Optional[WorkflowStep]:
        """Determine next step based on workflow logic."""
        current = self.steps.get(current_step)
        if not current:
            return None

        # Check for conditional branching
        if current.next_steps:
            # Evaluate conditions and determine next step
            for condition, next_step_name in current.next_steps.items():
                if self._evaluate_condition(condition, context):
                    return self.steps.get(next_step_name)
            return None

        # Simple sequential flow
        current_index = self.step_order.index(current_step)
        if current_index + 1 < len(self.step_order):
            next_step_name = self.step_order[current_index + 1]
            next_step = self.steps.get(next_step_name)
            if next_step and next_step.should_execute(context):
                return next_step

        return None

    def get_compensation_steps(self, failed_step: str) -> List[WorkflowStep]:
        """Get compensation steps to execute after a failure."""
        compensation_steps = []
        
        # Find all steps executed before the failed step
        failed_index = self.step_order.index(failed_step)
        for i in range(failed_index, -1, -1):
            step_name = self.step_order[i]
            if context.is_step_completed(step_name) and step_name in self.compensation_map:
                comp_step_name = self.compensation_map[step_name]
                if comp_step_name in self.steps:
                    compensation_steps.append(self.steps[comp_step_name])
        
        return compensation_steps

    def _evaluate_condition(self, condition: str, context: SagaContext) -> bool:
        """Evaluate a condition expression against the context."""
        # Simple implementation - can be enhanced with a proper expression evaluator
        if condition == "true":
            return True
        elif condition == "false":
            return False
        
        # Check for simple path expressions like "payment.success"
        if "." in condition:
            parts = condition.split(".")
            value = context.data
            for part in parts:
                if isinstance(value, dict) and part in value:
                    value = value[part]
                else:
                    return False
            return bool(value)
        
        return False


class WorkflowBuilder:
    """
    Fluent builder for creating workflow definitions.
    Follows Builder pattern for easy workflow construction.
    """

    def __init__(self, workflow_id: str):
        self.workflow = WorkflowDefinition(workflow_id)
        self._current_step: Optional[str] = None

    def add_step(self, name: str, worker_type: str, 
                 compensation: Optional[str] = None,
                 timeout: int = 300,
                 retry_policy: Optional[Dict[str, Any]] = None) -> 'WorkflowBuilder':
        """Add a step to the workflow."""
        step = WorkflowStep(
            name=name,
            worker_type=worker_type,
            compensation=compensation,
            timeout_seconds=timeout,
            retry_policy=retry_policy
        )
        self.workflow.add_step(step)
        self._current_step = name
        return self

    def add_conditional(self, condition: str, true_path: str, false_path: str) -> 'WorkflowBuilder':
        """Add conditional branching after the current step."""
        if self._current_step:
            current = self.workflow.steps[self._current_step]
            current.next_steps = {
                condition: true_path,
                f"not_{condition}": false_path
            }
        return self

    def add_parallel_steps(self, steps: List[Dict[str, Any]]) -> 'WorkflowBuilder':
        """Add steps that can execute in parallel."""
        # This is a placeholder for parallel execution support
        # Implementation would require enhancing the orchestrator
        for step_config in steps:
            self.add_step(**step_config)
        return self

    def build(self) -> WorkflowDefinition:
        """Build and return the workflow definition."""
        return self.workflow