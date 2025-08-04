"""
Monitoring interfaces for the MultiAgents framework.
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone
from enum import Enum


class LogLevel(str, Enum):
    """Log levels for the monitoring system."""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class ILogger(ABC):
    """
    Abstract logger interface for the monitoring system.
    Supports structured logging with metadata and different output formats.
    """

    @abstractmethod
    async def log(self, level: LogLevel, message: str, 
                  metadata: Optional[Dict[str, Any]] = None,
                  error: Optional[Exception] = None) -> None:
        """
        Log a message with optional metadata and error information.
        
        Args:
            level: Log level
            message: Log message
            metadata: Additional structured data
            error: Exception information if applicable
        """
        pass

    @abstractmethod
    async def debug(self, message: str, **kwargs) -> None:
        """Log debug message."""
        pass

    @abstractmethod
    async def info(self, message: str, **kwargs) -> None:
        """Log info message."""
        pass

    @abstractmethod
    async def warning(self, message: str, **kwargs) -> None:
        """Log warning message."""
        pass

    @abstractmethod
    async def error(self, message: str, error: Optional[Exception] = None, **kwargs) -> None:
        """Log error message."""
        pass

    @abstractmethod
    async def critical(self, message: str, error: Optional[Exception] = None, **kwargs) -> None:
        """Log critical message."""
        pass

    @abstractmethod
    async def close(self) -> None:
        """Close logger and cleanup resources."""
        pass


class EventStatus(str, Enum):
    """Status of an event in the monitoring system."""
    DISPATCHED = "dispatched"
    PICKED_UP = "picked_up"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"


class EventTrace:
    """Represents a trace of an event through the system."""
    
    def __init__(self, event_id: str, event_type: str, 
                 transaction_id: str, correlation_id: str):
        self.event_id = event_id
        self.event_type = event_type
        self.transaction_id = transaction_id
        self.correlation_id = correlation_id
        self.status = EventStatus.DISPATCHED
        self.source: Optional[str] = None
        self.worker_type: Optional[str] = None
        self.worker_instance: Optional[str] = None
        self.dispatched_at = datetime.utcnow()
        self.picked_up_at: Optional[datetime] = None
        self.processing_started_at: Optional[datetime] = None
        self.completed_at: Optional[datetime] = None
        self.error_message: Optional[str] = None
        self.error_details: Optional[Dict[str, Any]] = None
        self.metadata: Dict[str, Any] = {}

    def mark_picked_up(self, worker_type: str, worker_instance: str = None) -> None:
        """Mark event as picked up by a worker."""
        self.status = EventStatus.PICKED_UP
        self.worker_type = worker_type
        self.worker_instance = worker_instance or worker_type
        self.picked_up_at = datetime.utcnow()

    def mark_processing(self) -> None:
        """Mark event as being processed."""
        self.status = EventStatus.PROCESSING
        self.processing_started_at = datetime.utcnow()

    def mark_completed(self, result_metadata: Optional[Dict[str, Any]] = None) -> None:
        """Mark event as completed successfully."""
        self.status = EventStatus.COMPLETED
        self.completed_at = datetime.utcnow()
        if result_metadata:
            self.metadata.update(result_metadata)

    def mark_failed(self, error_message: str, error_details: Optional[Dict[str, Any]] = None) -> None:
        """Mark event as failed."""
        self.status = EventStatus.FAILED
        self.completed_at = datetime.utcnow()
        self.error_message = error_message
        self.error_details = error_details or {}

    def mark_timeout(self) -> None:
        """Mark event as timed out."""
        self.status = EventStatus.TIMEOUT
        self.completed_at = datetime.utcnow()
        self.error_message = "Event processing timeout"

    @property
    def total_duration(self) -> Optional[float]:
        """Total duration from dispatch to completion in seconds."""
        if self.completed_at:
            return (self.completed_at - self.dispatched_at).total_seconds()
        return None

    @property
    def pickup_duration(self) -> Optional[float]:
        """Duration from dispatch to pickup in seconds."""
        if self.picked_up_at:
            return (self.picked_up_at - self.dispatched_at).total_seconds()
        return None

    @property
    def processing_duration(self) -> Optional[float]:
        """Duration of processing in seconds."""
        if self.processing_started_at and self.completed_at:
            return (self.completed_at - self.processing_started_at).total_seconds()
        return None

    def to_dict(self) -> Dict[str, Any]:
        """Convert trace to dictionary for serialization."""
        return {
            "event_id": self.event_id,
            "event_type": self.event_type,
            "transaction_id": self.transaction_id,
            "correlation_id": self.correlation_id,
            "status": self.status.value,
            "source": self.source,
            "worker_type": self.worker_type,
            "worker_instance": self.worker_instance,
            "dispatched_at": self.dispatched_at.isoformat(),
            "picked_up_at": self.picked_up_at.isoformat() if self.picked_up_at else None,
            "processing_started_at": self.processing_started_at.isoformat() if self.processing_started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "total_duration": self.total_duration,
            "pickup_duration": self.pickup_duration,
            "processing_duration": self.processing_duration,
            "error_message": self.error_message,
            "error_details": self.error_details,
            "metadata": self.metadata,
        }


class IEventMonitor(ABC):
    """Interface for monitoring events in the system."""

    @abstractmethod
    async def track_event_dispatch(self, event_id: str, event_type: str,
                                 transaction_id: str, correlation_id: str,
                                 source: str, metadata: Optional[Dict[str, Any]] = None) -> EventTrace:
        """Track when an event is dispatched."""
        pass

    @abstractmethod
    async def track_event_pickup(self, event_id: str, worker_type: str, 
                               worker_instance: str = None) -> None:
        """Track when an event is picked up by a worker."""
        pass

    @abstractmethod
    async def track_event_processing(self, event_id: str) -> None:
        """Track when event processing starts."""
        pass

    @abstractmethod
    async def track_event_completion(self, event_id: str, 
                                   result_metadata: Optional[Dict[str, Any]] = None) -> None:
        """Track when event processing completes successfully."""
        pass

    @abstractmethod
    async def track_event_failure(self, event_id: str, error_message: str,
                                error_details: Optional[Dict[str, Any]] = None) -> None:
        """Track when event processing fails."""
        pass

    @abstractmethod
    async def get_event_trace(self, event_id: str) -> Optional[EventTrace]:
        """Get the trace for a specific event."""
        pass

    @abstractmethod
    async def get_transaction_events(self, transaction_id: str) -> List[EventTrace]:
        """Get all events for a transaction."""
        pass

    @abstractmethod
    async def get_event_metrics(self, time_window_minutes: int = 60) -> Dict[str, Any]:
        """Get aggregated event metrics for a time window."""
        pass


class WorkerMetrics:
    """Metrics for a worker instance."""
    
    def __init__(self, worker_type: str, worker_instance: str = None):
        self.worker_type = worker_type
        self.worker_instance = worker_instance or worker_type
        self.total_commands = 0
        self.successful_commands = 0
        self.failed_commands = 0
        self.timeout_commands = 0
        self.total_processing_time = 0.0
        self.min_processing_time: Optional[float] = None
        self.max_processing_time: Optional[float] = None
        self.last_activity: Optional[datetime] = None
        self.health_status = "healthy"
        self.error_details: List[Dict[str, Any]] = []
        self.created_at = datetime.now(timezone.utc)

    def record_command_start(self) -> None:
        """Record that a command started processing."""
        self.total_commands += 1
        self.last_activity = datetime.now(timezone.utc)

    def record_command_success(self, processing_time: float) -> None:
        """Record successful command completion."""
        self.successful_commands += 1
        self._update_processing_time(processing_time)

    def record_command_failure(self, processing_time: float, 
                             error_message: str, error_details: Dict[str, Any] = None) -> None:
        """Record failed command."""
        self.failed_commands += 1
        self._update_processing_time(processing_time)
        
        # Store error details (keep last 10)
        error_record = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "error_message": error_message,
            "details": error_details or {},
        }
        self.error_details.append(error_record)
        if len(self.error_details) > 10:
            self.error_details.pop(0)

    def record_command_timeout(self, processing_time: float) -> None:
        """Record command timeout."""
        self.timeout_commands += 1
        self._update_processing_time(processing_time)

    def _update_processing_time(self, processing_time: float) -> None:
        """Update processing time statistics."""
        self.total_processing_time += processing_time
        
        if self.min_processing_time is None or processing_time < self.min_processing_time:
            self.min_processing_time = processing_time
            
        if self.max_processing_time is None or processing_time > self.max_processing_time:
            self.max_processing_time = processing_time

    @property
    def success_rate(self) -> float:
        """Success rate as percentage."""
        if self.total_commands == 0:
            return 0.0
        return (self.successful_commands / self.total_commands) * 100

    @property
    def failure_rate(self) -> float:
        """Failure rate as percentage."""
        if self.total_commands == 0:
            return 0.0
        return (self.failed_commands / self.total_commands) * 100

    @property
    def average_processing_time(self) -> float:
        """Average processing time in seconds."""
        if self.total_commands == 0:
            return 0.0
        return self.total_processing_time / self.total_commands

    def to_dict(self) -> Dict[str, Any]:
        """Convert metrics to dictionary."""
        return {
            "worker_type": self.worker_type,
            "worker_instance": self.worker_instance,
            "total_commands": self.total_commands,
            "successful_commands": self.successful_commands,
            "failed_commands": self.failed_commands,
            "timeout_commands": self.timeout_commands,
            "success_rate": self.success_rate,
            "failure_rate": self.failure_rate,
            "total_processing_time": self.total_processing_time,
            "average_processing_time": self.average_processing_time,
            "min_processing_time": self.min_processing_time,
            "max_processing_time": self.max_processing_time,
            "last_activity": self.last_activity.isoformat() if self.last_activity else None,
            "health_status": self.health_status,
            "error_details": self.error_details,
            "created_at": self.created_at.isoformat(),
        }


class IMetricsCollector(ABC):
    """Interface for collecting system metrics."""

    @abstractmethod
    async def record_event_metric(self, event_type: str, duration: float, 
                                 success: bool, metadata: Optional[Dict[str, Any]] = None) -> None:
        """Record metrics for an event."""
        pass

    @abstractmethod
    async def record_worker_metric(self, worker_type: str, metric_name: str, 
                                 value: float, metadata: Optional[Dict[str, Any]] = None) -> None:
        """Record metrics for a worker."""
        pass

    @abstractmethod
    async def get_system_metrics(self, time_window_minutes: int = 60) -> Dict[str, Any]:
        """Get aggregated system metrics."""
        pass

    @abstractmethod
    async def get_worker_metrics(self, worker_type: str = None, 
                               time_window_minutes: int = 60) -> Dict[str, Any]:
        """Get worker-specific metrics."""
        pass