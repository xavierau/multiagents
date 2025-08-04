"""
Event monitoring system for tracking event lifecycle and performance.
"""
import asyncio
from collections import defaultdict, deque
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, Optional, List, Deque
import threading

from .interfaces import IEventMonitor, ILogger, EventTrace, EventStatus, LogLevel


class EventMonitor(IEventMonitor):
    """
    Monitors events throughout their lifecycle in the system.
    Tracks dispatch, pickup, processing, and completion with detailed metrics.
    """

    def __init__(self, 
                 logger: Optional[ILogger] = None,
                 max_trace_history: int = 10000,
                 cleanup_interval_minutes: int = 60,
                 trace_retention_hours: int = 24):
        
        self.logger = logger
        self.max_trace_history = max_trace_history
        self.cleanup_interval_minutes = cleanup_interval_minutes
        self.trace_retention_hours = trace_retention_hours
        
        # Thread-safe storage for event traces
        self._traces: Dict[str, EventTrace] = {}
        self._transaction_events: Dict[str, List[str]] = defaultdict(list)
        self._trace_lock = threading.RLock()
        
        # Time-based metrics storage
        self._event_metrics: Deque[Dict[str, Any]] = deque(maxlen=max_trace_history)
        self._metrics_lock = threading.RLock()
        
        # Background cleanup task
        self._cleanup_task: Optional[asyncio.Task] = None
        self._running = False

    async def start(self) -> None:
        """Start the event monitor and background cleanup."""
        if not self._running:
            self._running = True
            self._cleanup_task = asyncio.create_task(self._cleanup_loop())
            
            if self.logger:
                await self.logger.info("Event monitor started",
                    max_trace_history=self.max_trace_history,
                    cleanup_interval_minutes=self.cleanup_interval_minutes,
                    trace_retention_hours=self.trace_retention_hours
                )

    async def stop(self) -> None:
        """Stop the event monitor and cleanup."""
        self._running = False
        
        if self._cleanup_task and not self._cleanup_task.done():
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
        
        if self.logger:
            await self.logger.info("Event monitor stopped")

    async def track_event_dispatch(self, event_id: str, event_type: str,
                                 transaction_id: str, correlation_id: str,
                                 source: str, metadata: Optional[Dict[str, Any]] = None) -> EventTrace:
        """Track when an event is dispatched."""
        trace = EventTrace(event_id, event_type, transaction_id, correlation_id)
        trace.source = source
        if metadata:
            trace.metadata.update(metadata)
        
        with self._trace_lock:
            self._traces[event_id] = trace
            self._transaction_events[transaction_id].append(event_id)
        
        # Log event dispatch
        if self.logger:
            await self.logger.debug("Event dispatched",
                event_id=event_id,
                event_type=event_type,
                transaction_id=transaction_id,
                correlation_id=correlation_id,
                source=source
            )
        
        # Record metrics
        await self._record_event_metric("dispatched", trace)
        
        return trace

    async def track_event_pickup(self, event_id: str, worker_type: str, 
                               worker_instance: str = None) -> None:
        """Track when an event is picked up by a worker."""
        with self._trace_lock:
            trace = self._traces.get(event_id)
            if trace:
                trace.mark_picked_up(worker_type, worker_instance)
        
        if self.logger:
            await self.logger.debug("Event picked up",
                event_id=event_id,
                worker_type=worker_type,
                worker_instance=worker_instance,
                pickup_duration=trace.pickup_duration if trace else None
            )
        
        if trace:
            await self._record_event_metric("picked_up", trace)

    async def track_event_processing(self, event_id: str) -> None:
        """Track when event processing starts."""
        with self._trace_lock:
            trace = self._traces.get(event_id)
            if trace:
                trace.mark_processing()
        
        if self.logger:
            await self.logger.debug("Event processing started",
                event_id=event_id,
                worker_type=trace.worker_type if trace else None
            )
        
        if trace:
            await self._record_event_metric("processing_started", trace)

    async def track_event_completion(self, event_id: str, 
                                   result_metadata: Optional[Dict[str, Any]] = None) -> None:
        """Track when event processing completes successfully.""" 
        with self._trace_lock:
            trace = self._traces.get(event_id)
            if trace:
                trace.mark_completed(result_metadata)
        
        if self.logger:
            await self.logger.info("Event completed successfully",
                event_id=event_id,
                worker_type=trace.worker_type if trace else None,
                worker_instance=trace.worker_instance if trace else None,
                total_duration=trace.total_duration if trace else None,
                processing_duration=trace.processing_duration if trace else None
            )
        
        if trace:
            await self._record_event_metric("completed", trace)

    async def track_event_failure(self, event_id: str, error_message: str,
                                error_details: Optional[Dict[str, Any]] = None) -> None:
        """Track when event processing fails."""
        with self._trace_lock:
            trace = self._traces.get(event_id)
            if trace:
                trace.mark_failed(error_message, error_details)
        
        if self.logger:
            await self.logger.error("Event processing failed",
                event_id=event_id,
                worker_type=trace.worker_type if trace else None,
                worker_instance=trace.worker_instance if trace else None,
                error_message=error_message,
                total_duration=trace.total_duration if trace else None,
                error_details=error_details
            )
        
        if trace:
            await self._record_event_metric("failed", trace)

    async def track_event_timeout(self, event_id: str) -> None:
        """Track when event processing times out."""
        with self._trace_lock:
            trace = self._traces.get(event_id)
            if trace:
                trace.mark_timeout()
        
        if self.logger:
            await self.logger.warning("Event processing timeout",
                event_id=event_id,
                worker_type=trace.worker_type if trace else None,
                worker_instance=trace.worker_instance if trace else None,
                total_duration=trace.total_duration if trace else None
            )
        
        if trace:
            await self._record_event_metric("timeout", trace)

    async def get_event_trace(self, event_id: str) -> Optional[EventTrace]:
        """Get the trace for a specific event."""
        with self._trace_lock:
            return self._traces.get(event_id)

    async def get_transaction_events(self, transaction_id: str) -> List[EventTrace]:
        """Get all events for a transaction."""
        with self._trace_lock:
            event_ids = self._transaction_events.get(transaction_id, [])
            traces = []
            for event_id in event_ids:
                trace = self._traces.get(event_id)
                if trace:
                    traces.append(trace)
            return traces

    async def get_event_metrics(self, time_window_minutes: int = 60) -> Dict[str, Any]:
        """Get aggregated event metrics for a time window."""
        cutoff_time = datetime.now(timezone.utc) - timedelta(minutes=time_window_minutes)
        
        with self._metrics_lock:
            # Filter metrics within time window
            recent_metrics = [
                metric for metric in self._event_metrics
                if datetime.fromisoformat(metric["timestamp"].replace("Z", "+00:00")) > cutoff_time
            ]
        
        if not recent_metrics:
            return {
                "time_window_minutes": time_window_minutes,
                "total_events": 0,
                "events_by_type": {},
                "events_by_status": {},
                "average_processing_time": 0.0,
                "success_rate": 0.0,
            }

        # Aggregate metrics
        events_by_type = defaultdict(int)
        events_by_status = defaultdict(int)
        processing_times = []
        successful_events = 0
        total_events = len(recent_metrics)

        for metric in recent_metrics:
            events_by_type[metric["event_type"]] += 1
            events_by_status[metric["status"]] += 1
            
            if metric["status"] == "completed":
                successful_events += 1
                
            if metric.get("processing_duration"):
                processing_times.append(metric["processing_duration"])

        return {
            "time_window_minutes": time_window_minutes,
            "total_events": total_events,
            "events_by_type": dict(events_by_type),
            "events_by_status": dict(events_by_status),
            "average_processing_time": sum(processing_times) / len(processing_times) if processing_times else 0.0,
            "success_rate": (successful_events / total_events * 100) if total_events > 0 else 0.0,
            "metrics_collected_at": datetime.utcnow().isoformat() + "Z",
        }

    async def _record_event_metric(self, status: str, trace: EventTrace) -> None:
        """Record a metric point for an event."""
        metric = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "event_id": trace.event_id,
            "event_type": trace.event_type,
            "transaction_id": trace.transaction_id,
            "status": status,
            "worker_type": trace.worker_type,
            "worker_instance": trace.worker_instance,
            "total_duration": trace.total_duration,
            "pickup_duration": trace.pickup_duration,
            "processing_duration": trace.processing_duration,
        }
        
        with self._metrics_lock:
            self._event_metrics.append(metric)

    async def _cleanup_loop(self) -> None:
        """Background cleanup loop to remove old traces."""
        while self._running:
            try:
                await asyncio.sleep(self.cleanup_interval_minutes * 60)
                await self._cleanup_old_traces()
            except asyncio.CancelledError:
                break
            except Exception as e:
                if self.logger:
                    await self.logger.error("Error in event monitor cleanup", error=e)

    async def _cleanup_old_traces(self) -> None:
        """Remove traces older than retention period."""
        cutoff_time = datetime.utcnow() - timedelta(hours=self.trace_retention_hours)
        removed_traces = 0
        
        with self._trace_lock:
            # Find traces to remove
            traces_to_remove = []
            transactions_to_clean = set()
            
            for event_id, trace in self._traces.items():
                if trace.dispatched_at < cutoff_time:
                    traces_to_remove.append(event_id)
                    transactions_to_clean.add(trace.transaction_id)
            
            # Remove old traces
            for event_id in traces_to_remove:
                del self._traces[event_id]
                removed_traces += 1
            
            # Clean up transaction mappings
            for transaction_id in transactions_to_clean:
                self._transaction_events[transaction_id] = [
                    eid for eid in self._transaction_events[transaction_id]
                    if eid in self._traces
                ]
                
                # Remove empty transaction entries
                if not self._transaction_events[transaction_id]:
                    del self._transaction_events[transaction_id]
        
        if self.logger and removed_traces > 0:
            await self.logger.debug("Cleaned up old event traces",
                removed_traces=removed_traces,
                cutoff_time=cutoff_time.isoformat(),
                remaining_traces=len(self._traces)
            )

    def get_monitor_stats(self) -> Dict[str, Any]:
        """Get statistics about the event monitor."""
        with self._trace_lock:
            active_traces = len(self._traces)
            active_transactions = len(self._transaction_events)
        
        with self._metrics_lock:
            metrics_count = len(self._event_metrics)
        
        return {
            "active_traces": active_traces,
            "active_transactions": active_transactions,
            "metrics_count": metrics_count,
            "max_trace_history": self.max_trace_history,
            "cleanup_interval_minutes": self.cleanup_interval_minutes,
            "trace_retention_hours": self.trace_retention_hours,
            "running": self._running,
        }