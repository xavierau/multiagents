import pytest
from datetime import datetime
from uuid import UUID

from multiagents.event_bus.events import (
    EventType,
    EventMetadata,
    Event,
    CommandEvent,
    ResultEvent,
    ErrorEvent,
    CompensationEvent,
    StatusEvent
)


class TestEventMetadata:
    def test_event_metadata_creation(self):
        metadata = EventMetadata(
            transaction_id="trans-123",
            correlation_id="corr-456",
            source="test-source"
        )
        
        assert metadata.transaction_id == "trans-123"
        assert metadata.correlation_id == "corr-456"
        assert metadata.source == "test-source"
        assert metadata.version == "1.0"
        assert isinstance(metadata.timestamp, datetime)

    def test_event_metadata_custom_version(self):
        metadata = EventMetadata(
            transaction_id="trans-123",
            correlation_id="corr-456",
            source="test-source",
            version="2.0"
        )
        
        assert metadata.version == "2.0"

    def test_event_metadata_timestamp_auto_generation(self):
        metadata1 = EventMetadata(
            transaction_id="trans-123",
            correlation_id="corr-456",
            source="test-source"
        )
        metadata2 = EventMetadata(
            transaction_id="trans-123",
            correlation_id="corr-456",
            source="test-source"
        )
        
        # Timestamps should be different (generated at different times)
        assert metadata1.timestamp <= metadata2.timestamp


class TestBaseEvent:
    def test_event_creation(self):
        metadata = EventMetadata(
            transaction_id="trans-123",
            correlation_id="corr-456",
            source="test-source"
        )
        event = Event(
            type=EventType.COMMAND,
            metadata=metadata,
            payload={"key": "value"}
        )
        
        assert event.type == EventType.COMMAND.value
        assert event.metadata == metadata
        assert event.payload == {"key": "value"}
        assert UUID(event.id)  # Should be a valid UUID

    def test_event_id_auto_generation(self):
        metadata = EventMetadata(
            transaction_id="trans-123",
            correlation_id="corr-456",
            source="test-source"
        )
        event1 = Event(type=EventType.COMMAND, metadata=metadata)
        event2 = Event(type=EventType.COMMAND, metadata=metadata)
        
        assert event1.id != event2.id
        assert UUID(event1.id)
        assert UUID(event2.id)

    def test_event_default_payload(self):
        metadata = EventMetadata(
            transaction_id="trans-123",
            correlation_id="corr-456",
            source="test-source"
        )
        event = Event(type=EventType.COMMAND, metadata=metadata)
        
        assert event.payload == {}


class TestCommandEvent:
    def test_command_event_creation(self):
        metadata = EventMetadata(
            transaction_id="trans-123",
            correlation_id="corr-456",
            source="orchestrator"
        )
        command = CommandEvent(
            metadata=metadata,
            worker_type="payment_worker",
            payload={"amount": 100}
        )
        
        assert command.type == EventType.COMMAND.value
        assert command.worker_type == "payment_worker"
        assert command.timeout_seconds == 300
        assert command.retry_policy is None
        assert command.payload == {"amount": 100}

    def test_command_event_custom_timeout(self):
        metadata = EventMetadata(
            transaction_id="trans-123",
            correlation_id="corr-456",
            source="orchestrator"
        )
        command = CommandEvent(
            metadata=metadata,
            worker_type="payment_worker",
            timeout_seconds=600
        )
        
        assert command.timeout_seconds == 600

    def test_command_event_with_retry_policy(self):
        metadata = EventMetadata(
            transaction_id="trans-123",
            correlation_id="corr-456",
            source="orchestrator"
        )
        retry_policy = {
            "max_retries": 3,
            "backoff_seconds": 5
        }
        command = CommandEvent(
            metadata=metadata,
            worker_type="payment_worker",
            retry_policy=retry_policy
        )
        
        assert command.retry_policy == retry_policy


class TestResultEvent:
    def test_result_event_success(self):
        metadata = EventMetadata(
            transaction_id="trans-123",
            correlation_id="corr-456",
            source="payment_worker"
        )
        result = ResultEvent(
            metadata=metadata,
            command_id="cmd-789",
            success=True,
            payload={"transaction_id": "pay-123"}
        )
        
        assert result.type == EventType.RESULT.value
        assert result.command_id == "cmd-789"
        assert result.success is True
        assert result.error_message is None
        assert result.error_details is None

    def test_result_event_failure(self):
        metadata = EventMetadata(
            transaction_id="trans-123",
            correlation_id="corr-456",
            source="payment_worker"
        )
        result = ResultEvent(
            metadata=metadata,
            command_id="cmd-789",
            success=False,
            error_message="Payment failed",
            error_details={"code": "INSUFFICIENT_FUNDS"}
        )
        
        assert result.success is False
        assert result.error_message == "Payment failed"
        assert result.error_details == {"code": "INSUFFICIENT_FUNDS"}


class TestErrorEvent:
    def test_error_event_creation(self):
        metadata = EventMetadata(
            transaction_id="trans-123",
            correlation_id="corr-456",
            source="payment_worker"
        )
        error = ErrorEvent(
            metadata=metadata,
            error_code="PAYMENT_FAILED",
            error_message="Unable to process payment",
            error_details={"reason": "Network timeout"},
            recoverable=True
        )
        
        assert error.type == EventType.ERROR.value
        assert error.error_code == "PAYMENT_FAILED"
        assert error.error_message == "Unable to process payment"
        assert error.error_details == {"reason": "Network timeout"}
        assert error.recoverable is True

    def test_error_event_non_recoverable(self):
        metadata = EventMetadata(
            transaction_id="trans-123",
            correlation_id="corr-456",
            source="payment_worker"
        )
        error = ErrorEvent(
            metadata=metadata,
            error_code="INVALID_ACCOUNT",
            error_message="Account does not exist",
            recoverable=False
        )
        
        assert error.recoverable is False


class TestCompensationEvent:
    def test_compensation_event_creation(self):
        metadata = EventMetadata(
            transaction_id="trans-123",
            correlation_id="corr-456",
            source="orchestrator"
        )
        compensation = CompensationEvent(
            metadata=metadata,
            original_command_id="cmd-789",
            compensation_type="refund_payment"
        )
        
        assert compensation.type == EventType.COMPENSATION.value
        assert compensation.original_command_id == "cmd-789"
        assert compensation.compensation_type == "refund_payment"


class TestStatusEvent:
    def test_status_event_creation(self):
        metadata = EventMetadata(
            transaction_id="trans-123",
            correlation_id="corr-456",
            source="orchestrator"
        )
        status = StatusEvent(
            metadata=metadata,
            status="processing",
            progress=0.5,
            message="Processing payment"
        )
        
        assert status.type == EventType.STATUS.value
        assert status.status == "processing"
        assert status.progress == 0.5
        assert status.message == "Processing payment"

    def test_status_event_minimal(self):
        metadata = EventMetadata(
            transaction_id="trans-123",
            correlation_id="corr-456",
            source="orchestrator"
        )
        status = StatusEvent(
            metadata=metadata,
            status="started"
        )
        
        assert status.status == "started"
        assert status.progress is None
        assert status.message is None


class TestEventSerialization:
    def test_event_to_dict(self):
        metadata = EventMetadata(
            transaction_id="trans-123",
            correlation_id="corr-456",
            source="test-source"
        )
        event = CommandEvent(
            metadata=metadata,
            worker_type="test_worker",
            payload={"key": "value"}
        )
        
        event_dict = event.model_dump()
        
        assert isinstance(event_dict, dict)
        assert event_dict["type"] == "command"
        assert event_dict["worker_type"] == "test_worker"
        assert event_dict["metadata"]["transaction_id"] == "trans-123"
        assert event_dict["payload"] == {"key": "value"}

    def test_event_from_dict(self):
        event_dict = {
            "id": "event-123",
            "type": "command",
            "metadata": {
                "transaction_id": "trans-123",
                "correlation_id": "corr-456",
                "source": "test-source",
                "timestamp": "2024-01-01T00:00:00",
                "version": "1.0"
            },
            "worker_type": "test_worker",
            "timeout_seconds": 300,
            "payload": {"key": "value"}
        }
        
        event = CommandEvent.model_validate(event_dict)
        
        assert event.id == "event-123"
        assert event.worker_type == "test_worker"
        assert event.metadata.transaction_id == "trans-123"
        assert event.payload == {"key": "value"}