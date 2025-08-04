import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import MagicMock, AsyncMock

from multiagents.monitoring.event_monitor import EventMonitor
from multiagents.monitoring.interfaces import EventStatus, EventTrace


class TestEventMonitor:
    @pytest.fixture
    async def event_monitor(self, mock_logger):
        monitor = EventMonitor(
            logger=mock_logger,
            max_trace_history=1000,
            cleanup_interval_minutes=60,
            trace_retention_hours=24
        )
        yield monitor
        if monitor._running:
            await monitor.stop()

    @pytest.mark.asyncio
    async def test_initialization(self, event_monitor):
        assert event_monitor.max_trace_history == 1000
        assert event_monitor.cleanup_interval_minutes == 60
        assert event_monitor.trace_retention_hours == 24
        assert not event_monitor._running
        assert len(event_monitor._traces) == 0

    @pytest.mark.asyncio
    async def test_start_stop(self, event_monitor, mock_logger):
        # Start monitor
        await event_monitor.start()
        assert event_monitor._running
        assert event_monitor._cleanup_task is not None
        mock_logger.info.assert_called()

        # Stop monitor
        await event_monitor.stop()
        assert not event_monitor._running
        assert mock_logger.info.call_count >= 2  # Start and stop logs

    @pytest.mark.asyncio
    async def test_track_event_dispatch(self, event_monitor):
        await event_monitor.start()
        
        trace = await event_monitor.track_event_dispatch(
            event_id="evt-123",
            event_type="command",
            transaction_id="trans-456",
            correlation_id="corr-789",
            source="orchestrator",
            metadata={"worker_type": "payment"}
        )
        
        assert trace.event_id == "evt-123"
        assert trace.event_type == "command"
        assert trace.transaction_id == "trans-456"
        assert trace.correlation_id == "corr-789"
        assert trace.source == "orchestrator"
        assert trace.status == EventStatus.DISPATCHED
        assert trace.metadata["worker_type"] == "payment"
        
        # Check internal storage
        assert "evt-123" in event_monitor._traces
        assert "evt-123" in event_monitor._transaction_events["trans-456"]

    @pytest.mark.asyncio
    async def test_track_event_pickup(self, event_monitor):
        await event_monitor.start()
        
        # First dispatch an event
        await event_monitor.track_event_dispatch(
            event_id="evt-123",
            event_type="command",
            transaction_id="trans-456",
            correlation_id="corr-789",
            source="orchestrator"
        )
        
        # Then track pickup
        await event_monitor.track_event_pickup(
            event_id="evt-123",
            worker_type="payment_worker",
            worker_instance="worker-001"
        )
        
        trace = event_monitor._traces["evt-123"]
        assert trace.status == EventStatus.PICKED_UP
        assert trace.worker_type == "payment_worker"
        assert trace.worker_instance == "worker-001"
        assert trace.picked_up_at is not None

    @pytest.mark.asyncio
    async def test_track_event_processing(self, event_monitor):
        await event_monitor.start()
        
        # Dispatch and pickup
        await event_monitor.track_event_dispatch(
            event_id="evt-123",
            event_type="command",
            transaction_id="trans-456",
            correlation_id="corr-789",
            source="orchestrator"
        )
        await event_monitor.track_event_pickup(
            event_id="evt-123",
            worker_type="payment_worker"
        )
        
        # Track processing start
        await event_monitor.track_event_processing(
            event_id="evt-123"
        )
        
        trace = event_monitor._traces["evt-123"]
        assert trace.status == EventStatus.PROCESSING
        assert trace.processing_started_at is not None
        # payload tracking removed from this version

    @pytest.mark.asyncio
    async def test_track_event_completion(self, event_monitor):
        await event_monitor.start()
        
        # Full event lifecycle
        await event_monitor.track_event_dispatch(
            event_id="evt-123",
            event_type="command",
            transaction_id="trans-456",
            correlation_id="corr-789",
            source="orchestrator"
        )
        await event_monitor.track_event_pickup("evt-123", "payment_worker")
        await event_monitor.track_event_processing("evt-123")
        
        # Complete event
        await event_monitor.track_event_completion(
            event_id="evt-123",
            result_metadata={"status": "success", "transaction_id": "pay-123"}
        )
        
        trace = event_monitor._traces["evt-123"]
        assert trace.status == EventStatus.COMPLETED
        assert trace.completed_at is not None
        assert trace.metadata.get("status") == "success"
        assert trace.metadata.get("transaction_id") == "pay-123"
        assert trace.error_message is None

    @pytest.mark.asyncio
    async def test_track_event_failure(self, event_monitor):
        await event_monitor.start()
        
        # Setup event
        await event_monitor.track_event_dispatch(
            event_id="evt-123",
            event_type="command",
            transaction_id="trans-456",
            correlation_id="corr-789",
            source="orchestrator"
        )
        await event_monitor.track_event_pickup("evt-123", "payment_worker")
        await event_monitor.track_event_processing("evt-123")
        
        # Track failure
        await event_monitor.track_event_failure(
            event_id="evt-123",
            error_message="Payment gateway timeout",
            error_details={"code": "TIMEOUT", "retry_count": 3}
        )
        
        trace = event_monitor._traces["evt-123"]
        assert trace.status == EventStatus.FAILED
        assert trace.completed_at is not None
        assert trace.error_message == "Payment gateway timeout"
        assert trace.error_details == {"code": "TIMEOUT", "retry_count": 3}

    @pytest.mark.asyncio
    async def test_get_event_trace(self, event_monitor):
        await event_monitor.start()
        
        # Non-existent event
        assert await event_monitor.get_event_trace("non-existent") is None
        
        # Existing event
        await event_monitor.track_event_dispatch(
            event_id="evt-123",
            event_type="command",
            transaction_id="trans-456",
            correlation_id="corr-789",
            source="orchestrator"
        )
        
        trace = await event_monitor.get_event_trace("evt-123")
        assert trace is not None
        assert trace.event_id == "evt-123"

    @pytest.mark.asyncio
    async def test_get_transaction_trace(self, event_monitor):
        await event_monitor.start()
        
        # Dispatch multiple events for same transaction
        await event_monitor.track_event_dispatch(
            event_id="evt-1",
            event_type="command",
            transaction_id="trans-456",
            correlation_id="corr-789",
            source="orchestrator"
        )
        await event_monitor.track_event_dispatch(
            event_id="evt-2",
            event_type="command",
            transaction_id="trans-456",
            correlation_id="corr-790",
            source="orchestrator"
        )
        
        traces = await event_monitor.get_transaction_events("trans-456")
        assert len(traces) == 2
        assert all(t.transaction_id == "trans-456" for t in traces)

    @pytest.mark.asyncio
    async def test_cleanup_old_traces(self, event_monitor):
        await event_monitor.start()
        
        # Create old event
        old_trace = await event_monitor.track_event_dispatch(
            event_id="old-evt",
            event_type="command",
            transaction_id="old-trans",
            correlation_id="old-corr",
            source="orchestrator"
        )
        
        # Manually set dispatch time to be old (use UTC to match cleanup logic)
        old_trace.dispatched_at = datetime.utcnow() - timedelta(hours=25)
        
        # Create recent event
        await event_monitor.track_event_dispatch(
            event_id="new-evt",
            event_type="command",
            transaction_id="new-trans",
            correlation_id="new-corr",
            source="orchestrator"
        )
        
        # Run cleanup
        await event_monitor._cleanup_old_traces()
        
        # Old event should be gone
        assert await event_monitor.get_event_trace("old-evt") is None
        # New event should remain
        assert await event_monitor.get_event_trace("new-evt") is not None

    @pytest.mark.asyncio
    async def test_concurrent_access(self, event_monitor):
        await event_monitor.start()
        
        # Test thread safety with concurrent operations
        async def dispatch_events(start_id):
            for i in range(100):
                await event_monitor.track_event_dispatch(
                    event_id=f"evt-{start_id}-{i}",
                    event_type="command",
                    transaction_id=f"trans-{start_id}",
                    correlation_id=f"corr-{start_id}-{i}",
                    source="test"
                )
        
        # Run multiple concurrent tasks
        await asyncio.gather(
            dispatch_events(1),
            dispatch_events(2),
            dispatch_events(3)
        )
        
        # Verify all events were tracked
        assert len(event_monitor._traces) == 300

    @pytest.mark.asyncio
    async def test_event_lifecycle_duration_tracking(self, event_monitor):
        await event_monitor.start()
        
        # Track full lifecycle
        await event_monitor.track_event_dispatch(
            event_id="evt-123",
            event_type="command",
            transaction_id="trans-456",
            correlation_id="corr-789",
            source="orchestrator"
        )
        
        await asyncio.sleep(0.01)  # Small delay
        await event_monitor.track_event_pickup("evt-123", "payment_worker")
        
        await asyncio.sleep(0.01)
        await event_monitor.track_event_processing("evt-123")
        
        await asyncio.sleep(0.01)
        await event_monitor.track_event_completion("evt-123", {"status": "success"})
        
        trace = await event_monitor.get_event_trace("evt-123")
        
        # Verify timestamps are in order
        assert trace.dispatched_at < trace.picked_up_at
        assert trace.picked_up_at < trace.processing_started_at
        assert trace.processing_started_at < trace.completed_at
        
        # Verify durations
        assert trace.pickup_duration > 0
        assert trace.processing_duration > 0
        assert trace.total_duration > 0