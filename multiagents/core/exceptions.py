class MultiAgentException(Exception):
    """Base exception for all framework exceptions."""
    pass


class WorkflowException(MultiAgentException):
    """Exception related to workflow execution."""
    pass


class WorkerException(MultiAgentException):
    """Exception related to worker execution."""
    pass


class EventBusException(MultiAgentException):
    """Exception related to event bus operations."""
    pass


class StateException(MultiAgentException):
    """Exception related to state management."""
    pass


class ValidationException(MultiAgentException):
    """Exception related to validation errors."""
    pass