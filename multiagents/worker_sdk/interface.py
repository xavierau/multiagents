from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List


class IWorker(ABC):
    """
    Worker interface following Single Responsibility Principle.
    Each worker handles a specific type of task.
    """

    @abstractmethod
    async def process(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a single command with the given context.
        
        Args:
            context: Input data for the task
            
        Returns:
            Result data from the task execution
            
        Raises:
            WorkerException: If processing fails
        """
        pass

    @abstractmethod
    def get_worker_type(self) -> str:
        """Return the worker type identifier that this worker handles."""
        pass

    @abstractmethod
    def validate_input(self, context: Dict[str, Any]) -> bool:
        """
        Validate input context before processing.
        
        Args:
            context: Input data to validate
            
        Returns:
            True if input is valid
        """
        pass


class IWorkerRegistry(ABC):
    """Registry for managing available workers."""

    @abstractmethod
    def register(self, worker: IWorker) -> None:
        """Register a worker."""
        pass

    @abstractmethod
    def unregister(self, worker_type: str) -> bool:
        """Unregister a worker by type."""
        pass

    @abstractmethod
    def get_worker(self, worker_type: str) -> Optional[IWorker]:
        """Get a worker by type."""
        pass

    @abstractmethod
    def list_workers(self) -> List[str]:
        """List all registered worker types."""
        pass


class IWorkerLifecycle(ABC):
    """Interface for worker lifecycle management."""

    @abstractmethod
    async def on_start(self) -> None:
        """Called when worker starts."""
        pass

    @abstractmethod
    async def on_stop(self) -> None:
        """Called when worker stops."""
        pass

    @abstractmethod
    async def health_check(self) -> Dict[str, Any]:
        """Return health status of the worker."""
        pass