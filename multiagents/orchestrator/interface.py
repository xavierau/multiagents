from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from ..core.saga_context import SagaContext


class IOrchestrator(ABC):
    """
    Main orchestrator interface following Interface Segregation Principle.
    Manages workflow execution and state.
    """

    @abstractmethod
    async def execute_workflow(self, workflow_id: str, initial_context: Dict[str, Any]) -> str:
        """
        Start a new workflow instance.
        
        Args:
            workflow_id: ID of the workflow definition to execute
            initial_context: Initial data for the workflow
            
        Returns:
            transaction_id: Unique ID for this workflow instance
        """
        pass

    @abstractmethod
    async def get_status(self, transaction_id: str) -> Dict[str, Any]:
        """
        Get current status of a workflow instance.
        
        Args:
            transaction_id: ID of the workflow instance
            
        Returns:
            Status information including state, current step, and results
        """
        pass

    @abstractmethod
    async def cancel_workflow(self, transaction_id: str) -> bool:
        """
        Cancel a running workflow.
        
        Args:
            transaction_id: ID of the workflow instance to cancel
            
        Returns:
            True if cancelled successfully
        """
        pass


class IWorkflowDefinition(ABC):
    """Interface for defining workflows."""

    @abstractmethod
    def get_id(self) -> str:
        """Get the workflow ID."""
        pass

    @abstractmethod
    def get_steps(self) -> List['WorkflowStep']:
        """Get all steps in the workflow."""
        pass

    @abstractmethod
    def get_initial_step(self) -> Optional['WorkflowStep']:
        """Get the first step to execute."""
        pass

    @abstractmethod
    def get_next_step(self, current_step: str, context: SagaContext) -> Optional['WorkflowStep']:
        """
        Determine the next step based on current step and context.
        
        Args:
            current_step: Name of the current step
            context: Current saga context with results
            
        Returns:
            Next step to execute or None if workflow is complete
        """
        pass


class IStateStore(ABC):
    """Interface for persisting workflow state."""

    @abstractmethod
    async def save_context(self, context: SagaContext) -> None:
        """Save or update a saga context."""
        pass

    @abstractmethod
    async def load_context(self, transaction_id: str) -> Optional[SagaContext]:
        """Load a saga context by transaction ID."""
        pass

    @abstractmethod
    async def delete_context(self, transaction_id: str) -> bool:
        """Delete a saga context."""
        pass

    @abstractmethod
    async def list_contexts(self, workflow_id: Optional[str] = None, 
                          state: Optional[str] = None) -> List[str]:
        """List transaction IDs matching criteria."""
        pass