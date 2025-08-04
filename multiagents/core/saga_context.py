from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, Any, List, Optional
from uuid import uuid4


class SagaState(str, Enum):
    """States of a saga/workflow instance."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    COMPENSATING = "compensating"
    COMPENSATED = "compensated"
    CANCELLED = "cancelled"


@dataclass
class StepExecution:
    """Record of a single step execution."""
    step_name: str
    status: str
    started_at: datetime
    completed_at: Optional[datetime] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    command_id: Optional[str] = None


@dataclass
class SagaContext:
    """
    Context maintaining the state of a workflow instance.
    This is persisted and used to track progress and handle failures.
    """
    transaction_id: str = field(default_factory=lambda: str(uuid4()))
    workflow_id: str = field(default="")
    state: SagaState = field(default=SagaState.PENDING)
    current_step: Optional[str] = field(default=None)
    data: Dict[str, Any] = field(default_factory=dict)
    step_results: Dict[str, Any] = field(default_factory=dict)
    execution_history: List[StepExecution] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    error: Optional[str] = field(default=None)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def update_step_result(self, step_name: str, result: Dict[str, Any]) -> None:
        """Update the result of a step execution."""
        self.step_results[step_name] = result
        self.data.update(result)
        self.updated_at = datetime.utcnow()

    def record_step_start(self, step_name: str, command_id: str) -> None:
        """Record the start of a step execution."""
        execution = StepExecution(
            step_name=step_name,
            status="started",
            started_at=datetime.utcnow(),
            command_id=command_id
        )
        self.execution_history.append(execution)
        self.current_step = step_name
        self.updated_at = datetime.utcnow()

    def record_step_completion(self, step_name: str, result: Dict[str, Any]) -> None:
        """Record the completion of a step."""
        for execution in reversed(self.execution_history):
            if execution.step_name == step_name and execution.status == "started":
                execution.status = "completed"
                execution.completed_at = datetime.utcnow()
                execution.result = result
                break
        self.update_step_result(step_name, result)

    def record_step_failure(self, step_name: str, error: str) -> None:
        """Record a step failure."""
        for execution in reversed(self.execution_history):
            if execution.step_name == step_name and execution.status == "started":
                execution.status = "failed"
                execution.completed_at = datetime.utcnow()
                execution.error = error
                break
        self.error = error
        self.state = SagaState.FAILED
        self.updated_at = datetime.utcnow()

    def get_step_result(self, step_name: str) -> Optional[Dict[str, Any]]:
        """Get the result of a previously executed step."""
        return self.step_results.get(step_name)

    def is_step_completed(self, step_name: str) -> bool:
        """Check if a step has been completed successfully."""
        return step_name in self.step_results

    def to_dict(self) -> Dict[str, Any]:
        """Convert context to dictionary for serialization."""
        return {
            "transaction_id": self.transaction_id,
            "workflow_id": self.workflow_id,
            "state": self.state.value,
            "current_step": self.current_step,
            "data": self.data,
            "step_results": self.step_results,
            "execution_history": [
                {
                    "step_name": e.step_name,
                    "status": e.status,
                    "started_at": e.started_at.isoformat(),
                    "completed_at": e.completed_at.isoformat() if e.completed_at else None,
                    "result": e.result,
                    "error": e.error,
                    "command_id": e.command_id,
                }
                for e in self.execution_history
            ],
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "error": self.error,
            "metadata": self.metadata,
        }