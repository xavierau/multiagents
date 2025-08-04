from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, Any, Optional
from uuid import uuid4
from pydantic import BaseModel, Field


class EventType(str, Enum):
    """Standard event types in the framework."""
    COMMAND = "command"
    RESULT = "result"
    ERROR = "error"
    COMPENSATION = "compensation"
    STATUS = "status"


class EventMetadata(BaseModel):
    """Metadata carried by all events for tracing and correlation."""
    transaction_id: str = Field(description="Unique ID for the entire workflow instance")
    correlation_id: str = Field(description="ID linking related events")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    source: str = Field(description="Component that generated the event")
    version: str = Field(default="1.0", description="Event schema version")


class Event(BaseModel):
    """Base event class following Open/Closed Principle."""
    id: str = Field(default_factory=lambda: str(uuid4()))
    type: EventType
    metadata: EventMetadata
    payload: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        use_enum_values = True


class CommandEvent(Event):
    """Event requesting a worker to perform an action."""
    type: EventType = EventType.COMMAND
    worker_type: str = Field(description="Type of worker that should handle this command")
    timeout_seconds: Optional[int] = Field(default=300, description="Command timeout")
    retry_policy: Optional[Dict[str, Any]] = Field(
        default=None, 
        description="Retry configuration for this command"
    )


class ResultEvent(Event):
    """Event containing the result of a command execution."""
    type: EventType = EventType.RESULT
    command_id: str = Field(description="ID of the command this result is for")
    success: bool = Field(description="Whether the command succeeded")
    error_message: Optional[str] = Field(default=None)
    error_details: Optional[Dict[str, Any]] = Field(default=None)


class ErrorEvent(Event):
    """Event indicating an error occurred."""
    type: EventType = EventType.ERROR
    error_code: str
    error_message: str
    error_details: Optional[Dict[str, Any]] = Field(default=None)
    recoverable: bool = Field(default=True)


class CompensationEvent(Event):
    """Event triggering a compensation action."""
    type: EventType = EventType.COMPENSATION
    original_command_id: str = Field(description="ID of the command to compensate")
    compensation_type: str = Field(description="Type of compensation to perform")


class StatusEvent(Event):
    """Event providing status updates about workflow progress."""
    type: EventType = EventType.STATUS
    status: str = Field(description="Current status")
    progress: Optional[float] = Field(default=None, description="Progress percentage")
    message: Optional[str] = Field(default=None)