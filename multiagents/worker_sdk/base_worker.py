from typing import Dict, Any, Optional
from dataclasses import dataclass
import structlog
from abc import abstractmethod

from .interface import IWorker, IWorkerLifecycle
from ..core.exceptions import WorkerException, ValidationException

logger = structlog.get_logger()


@dataclass
class WorkerConfig:
    """Configuration for a worker."""
    worker_type: str
    timeout_seconds: int = 300
    retry_attempts: int = 3
    retry_delay_seconds: int = 1
    enable_logging: bool = True
    enable_metrics: bool = True
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class BaseWorker(IWorker, IWorkerLifecycle):
    """
    Base implementation of a worker with common functionality.
    Follows Open/Closed Principle - open for extension, closed for modification.
    """

    def __init__(self, config: WorkerConfig):
        self.config = config
        self.logger = logger.bind(worker_type=config.worker_type)
        self._is_running = False

    def get_worker_type(self) -> str:
        return self.config.worker_type

    async def process(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a command with validation and error handling.
        
        This method implements the template pattern - subclasses implement execute().
        """
        try:
            # Validate input
            if not self.validate_input(context):
                raise ValidationException(f"Invalid input for worker {self.get_worker_type()}")

            # Log start
            if self.config.enable_logging:
                self.logger.info("Processing command", context=context)

            # Execute the actual work
            result = await self.execute(context)

            # Validate output
            if not self.validate_output(result):
                raise ValidationException(f"Invalid output from worker {self.get_worker_type()}")

            # Log completion
            if self.config.enable_logging:
                self.logger.info("Command processed successfully", result=result)

            return result

        except Exception as e:
            self.logger.error("Worker processing failed", error=str(e), context=context)
            raise WorkerException(f"Worker {self.get_worker_type()} failed: {str(e)}") from e

    @abstractmethod
    async def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the actual work. Must be implemented by subclasses.
        
        Args:
            context: Input data for the task
            
        Returns:
            Result data from the task execution
        """
        pass

    def validate_input(self, context: Dict[str, Any]) -> bool:
        """
        Validate input context. Override in subclasses for specific validation.
        
        Default implementation checks for non-empty context.
        """
        return context is not None and isinstance(context, dict)

    def validate_output(self, result: Dict[str, Any]) -> bool:
        """
        Validate output result. Override in subclasses for specific validation.
        
        Default implementation checks for non-empty result.
        """
        return result is not None and isinstance(result, dict)

    async def on_start(self) -> None:
        """Called when worker starts."""
        self._is_running = True
        self.logger.info("Worker started")

    async def on_stop(self) -> None:
        """Called when worker stops."""
        self._is_running = False
        self.logger.info("Worker stopped")

    async def health_check(self) -> Dict[str, Any]:
        """Return health status of the worker."""
        return {
            "status": "healthy" if self._is_running else "stopped",
            "worker_type": self.get_worker_type(),
            "config": {
                "timeout_seconds": self.config.timeout_seconds,
                "retry_attempts": self.config.retry_attempts,
            }
        }


class DSPyWorker(BaseWorker):
    """
    Base worker that integrates DSPy for LLM capabilities.
    Extends BaseWorker with DSPy agent functionality.
    """

    def __init__(self, config: WorkerConfig, dspy_agent: Optional['DSPyAgent'] = None):
        super().__init__(config)
        
        # Lazy import to avoid circular dependency
        if dspy_agent is None:
            from .dspy_wrapper import DSPyAgent
            self.dspy_agent = DSPyAgent()
        else:
            self.dspy_agent = dspy_agent

    @abstractmethod
    async def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute using DSPy capabilities."""
        pass