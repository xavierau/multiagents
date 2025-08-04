"""
Worker performance monitoring system.
"""
import asyncio
from collections import defaultdict, deque
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, Optional, List, Deque
import threading

from .interfaces import ILogger, LogLevel, WorkerMetrics


class WorkerMonitor:
    """
    Monitors worker performance, health, and metrics.
    Tracks success rates, processing times, and error patterns.
    """

    def __init__(self, 
                 logger: Optional[ILogger] = None,
                 health_check_interval_seconds: int = 30,
                 metrics_retention_hours: int = 24,
                 max_metrics_per_worker: int = 1000):
        
        self.logger = logger
        self.health_check_interval_seconds = health_check_interval_seconds
        self.metrics_retention_hours = metrics_retention_hours
        self.max_metrics_per_worker = max_metrics_per_worker
        
        # Thread-safe storage
        self._worker_metrics: Dict[str, WorkerMetrics] = {}
        self._metrics_lock = threading.RLock()
        
        # Time-series metrics for each worker
        self._worker_timeseries: Dict[str, Deque[Dict[str, Any]]] = defaultdict(
            lambda: deque(maxlen=max_metrics_per_worker)
        )
        self._timeseries_lock = threading.RLock()
        
        # Health monitoring
        self._health_check_task: Optional[asyncio.Task] = None
        self._running = False

    async def start(self) -> None:
        """Start worker monitoring and health checks."""
        if not self._running:
            self._running = True
            self._health_check_task = asyncio.create_task(self._health_check_loop())
            
            if self.logger:
                await self.logger.info("Worker monitor started",
                    health_check_interval_seconds=self.health_check_interval_seconds,
                    metrics_retention_hours=self.metrics_retention_hours
                )

    async def stop(self) -> None:
        """Stop worker monitoring."""
        self._running = False
        
        if self._health_check_task and not self._health_check_task.done():
            self._health_check_task.cancel()
            try:
                await self._health_check_task
            except asyncio.CancelledError:
                pass
        
        if self.logger:
            await self.logger.info("Worker monitor stopped")

    def register_worker(self, worker_type: str, worker_instance: str = None) -> None:
        """Register a new worker for monitoring."""
        worker_key = f"{worker_type}:{worker_instance or worker_type}"
        
        with self._metrics_lock:
            if worker_key not in self._worker_metrics:
                self._worker_metrics[worker_key] = WorkerMetrics(worker_type, worker_instance)
                
                if self.logger:
                    asyncio.create_task(self.logger.info("Worker registered for monitoring",
                        worker_type=worker_type,
                        worker_instance=worker_instance or worker_type
                    ))

    def unregister_worker(self, worker_type: str, worker_instance: str = None) -> bool:
        """Unregister a worker from monitoring."""
        worker_key = f"{worker_type}:{worker_instance or worker_type}"
        
        with self._metrics_lock:
            if worker_key in self._worker_metrics:
                del self._worker_metrics[worker_key]
                
                with self._timeseries_lock:
                    if worker_key in self._worker_timeseries:
                        del self._worker_timeseries[worker_key]
                
                if self.logger:
                    asyncio.create_task(self.logger.info("Worker unregistered from monitoring",
                        worker_type=worker_type,
                        worker_instance=worker_instance or worker_type
                    ))
                return True
        return False

    async def track_command_start(self, worker_type: str, command_id: str,
                                worker_instance: str = None) -> None:
        """Track when a worker starts processing a command."""
        worker_key = f"{worker_type}:{worker_instance or worker_type}"
        
        # Ensure worker is registered
        self.register_worker(worker_type, worker_instance)
        
        with self._metrics_lock:
            metrics = self._worker_metrics.get(worker_key)
            if metrics:
                metrics.record_command_start()
        
        await self._record_timeseries_metric(worker_key, "command_started", {
            "command_id": command_id,
            "worker_type": worker_type,
            "worker_instance": worker_instance or worker_type,
        })

    async def track_command_success(self, worker_type: str, command_id: str,
                                  processing_time: float, 
                                  worker_instance: str = None,
                                  result_metadata: Optional[Dict[str, Any]] = None) -> None:
        """Track successful command completion."""
        worker_key = f"{worker_type}:{worker_instance or worker_type}"
        
        # Ensure worker is registered
        self.register_worker(worker_type, worker_instance)
        
        with self._metrics_lock:
            metrics = self._worker_metrics.get(worker_key)
            if metrics:
                # If this success wasn't preceded by a start call, count it as a total command too
                prev_total = metrics.total_commands
                prev_success = metrics.successful_commands
                metrics.record_command_success(processing_time)
                
                # If total_commands wasn't incremented by record_command_start, increment it now
                if metrics.total_commands == prev_total:
                    metrics.total_commands += 1
        
        await self._record_timeseries_metric(worker_key, "command_success", {
            "command_id": command_id,
            "processing_time": processing_time,
            "worker_type": worker_type,
            "worker_instance": worker_instance or worker_type,
            "result_metadata": result_metadata or {},
        })
        
        if self.logger:
            await self.logger.debug("Worker command completed",
                worker_type=worker_type,
                worker_instance=worker_instance or worker_type,
                command_id=command_id,
                processing_time=processing_time
            )

    async def track_command_failure(self, worker_type: str, command_id: str,
                                  processing_time: float, error_message: str,
                                  worker_instance: str = None,
                                  error_details: Optional[Dict[str, Any]] = None) -> None:
        """Track failed command."""
        worker_key = f"{worker_type}:{worker_instance or worker_type}"
        
        # Ensure worker is registered
        self.register_worker(worker_type, worker_instance)
        
        with self._metrics_lock:
            metrics = self._worker_metrics.get(worker_key)
            if metrics:
                # If this failure wasn't preceded by a start call, count it as a total command too
                prev_total = metrics.total_commands
                prev_failed = metrics.failed_commands
                metrics.record_command_failure(processing_time, error_message, error_details)
                
                # If total_commands wasn't incremented by record_command_start, increment it now
                if metrics.total_commands == prev_total:
                    metrics.total_commands += 1
        
        await self._record_timeseries_metric(worker_key, "command_failure", {
            "command_id": command_id,
            "processing_time": processing_time,
            "error_message": error_message,
            "error_details": error_details or {},
            "worker_type": worker_type,
            "worker_instance": worker_instance or worker_type,
        })
        
        if self.logger:
            await self.logger.warning("Worker command failed",
                worker_type=worker_type,
                worker_instance=worker_instance or worker_type,
                command_id=command_id,
                processing_time=processing_time,
                error_message=error_message
            )

    async def track_command_timeout(self, worker_type: str, command_id: str,
                                  processing_time: float,
                                  worker_instance: str = None) -> None:
        """Track command timeout."""
        worker_key = f"{worker_type}:{worker_instance or worker_type}"
        
        # Ensure worker is registered
        self.register_worker(worker_type, worker_instance)
        
        with self._metrics_lock:
            metrics = self._worker_metrics.get(worker_key)
            if metrics:
                # If this timeout wasn't preceded by a start call, count it as a total command too
                prev_total = metrics.total_commands
                prev_timeout = metrics.timeout_commands
                metrics.record_command_timeout(processing_time)
                
                # If total_commands wasn't incremented by record_command_start, increment it now
                if metrics.total_commands == prev_total:
                    metrics.total_commands += 1
        
        await self._record_timeseries_metric(worker_key, "command_timeout", {
            "command_id": command_id,
            "processing_time": processing_time,
            "worker_type": worker_type,
            "worker_instance": worker_instance or worker_type,
        })
        
        if self.logger:
            await self.logger.warning("Worker command timeout",
                worker_type=worker_type,
                worker_instance=worker_instance or worker_type,
                command_id=command_id,
                processing_time=processing_time
            )

    async def get_worker_metrics(self, worker_type: str = None, 
                               worker_instance: str = None) -> Dict[str, Any]:
        """Get metrics for specific worker or all workers."""
        with self._metrics_lock:
            if worker_type:
                worker_key = f"{worker_type}:{worker_instance or worker_type}"
                metrics = self._worker_metrics.get(worker_key)
                if metrics:
                    return metrics.to_dict()
                return {}
            else:
                # Return all worker metrics
                return {
                    worker_key: metrics.to_dict()
                    for worker_key, metrics in self._worker_metrics.items()
                }

    async def get_worker_performance_summary(self, time_window_minutes: int = 60) -> Dict[str, Any]:
        """Get performance summary for all workers."""
        cutoff_time = datetime.now(timezone.utc) - timedelta(minutes=time_window_minutes)
        
        summary = {
            "time_window_minutes": time_window_minutes,
            "workers": {},
            "aggregated_metrics": {
                "total_commands": 0,
                "successful_commands": 0,
                "failed_commands": 0,
                "timeout_commands": 0,
                "average_success_rate": 0.0,
                "average_processing_time": 0.0,
            },
            "top_performers": [],
            "problem_workers": [],
        }
        
        with self._metrics_lock:
            worker_summaries = []
            
            for worker_key, metrics in self._worker_metrics.items():
                # Get recent timeseries data
                recent_commands = await self._get_recent_commands(worker_key, cutoff_time)
                
                worker_summary = {
                    "worker_key": worker_key,
                    "worker_type": metrics.worker_type,
                    "worker_instance": metrics.worker_instance,
                    "recent_commands": len(recent_commands),
                    "success_rate": metrics.success_rate,
                    "failure_rate": metrics.failure_rate,
                    "average_processing_time": metrics.average_processing_time,
                    "health_status": metrics.health_status,
                    "last_activity": metrics.last_activity.isoformat() if metrics.last_activity else None,
                }
                
                summary["workers"][worker_key] = worker_summary
                worker_summaries.append(worker_summary)
                
                # Aggregate metrics
                summary["aggregated_metrics"]["total_commands"] += metrics.total_commands
                summary["aggregated_metrics"]["successful_commands"] += metrics.successful_commands
                summary["aggregated_metrics"]["failed_commands"] += metrics.failed_commands
                summary["aggregated_metrics"]["timeout_commands"] += metrics.timeout_commands
        
        # Calculate aggregated averages
        if summary["aggregated_metrics"]["total_commands"] > 0:
            total_commands = summary["aggregated_metrics"]["total_commands"]
            successful_commands = summary["aggregated_metrics"]["successful_commands"]
            summary["aggregated_metrics"]["average_success_rate"] = (successful_commands / total_commands) * 100
        
        if worker_summaries:
            processing_times = [w["average_processing_time"] for w in worker_summaries if w["average_processing_time"] > 0]
            if processing_times:
                summary["aggregated_metrics"]["average_processing_time"] = sum(processing_times) / len(processing_times)
        
        # Identify top performers and problem workers
        sorted_by_success = sorted(worker_summaries, key=lambda x: x["success_rate"], reverse=True)
        summary["top_performers"] = sorted_by_success[:5]
        
        problem_workers = [
            w for w in worker_summaries 
            if w["failure_rate"] > 10 or w["health_status"] != "healthy"
        ]
        summary["problem_workers"] = sorted(problem_workers, key=lambda x: x["failure_rate"], reverse=True)
        
        return summary

    async def get_worker_health_status(self, worker_type: str = None,
                                     worker_instance: str = None) -> Dict[str, Any]:
        """Get health status for workers."""
        with self._metrics_lock:
            if worker_type:
                worker_key = f"{worker_type}:{worker_instance or worker_type}"
                metrics = self._worker_metrics.get(worker_key)
                if metrics:
                    return {
                        "worker_key": worker_key,
                        "health_status": metrics.health_status,
                        "last_activity": metrics.last_activity.isoformat() if metrics.last_activity else None,
                        "total_commands": metrics.total_commands,
                        "success_rate": metrics.success_rate,
                        "failure_rate": metrics.failure_rate,
                    }
                return {}
            else:
                # Return health for all workers
                health_status = {}
                for worker_key, metrics in self._worker_metrics.items():
                    health_status[worker_key] = {
                        "health_status": metrics.health_status,
                        "last_activity": metrics.last_activity.isoformat() if metrics.last_activity else None,
                        "success_rate": metrics.success_rate,
                        "failure_rate": metrics.failure_rate,
                    }
                return health_status

    async def _record_timeseries_metric(self, worker_key: str, metric_type: str, 
                                      data: Dict[str, Any]) -> None:
        """Record a time-series metric point."""
        metric_point = {
            "timestamp": datetime.now(timezone.utc).isoformat() + "Z",
            "metric_type": metric_type,
            **data
        }
        
        with self._timeseries_lock:
            self._worker_timeseries[worker_key].append(metric_point)

    async def _get_recent_commands(self, worker_key: str, cutoff_time: datetime) -> List[Dict[str, Any]]:
        """Get recent commands for a worker."""
        with self._timeseries_lock:
            if worker_key not in self._worker_timeseries:
                return []
            
            recent_commands = []
            for metric in self._worker_timeseries[worker_key]:
                timestamp_str = metric["timestamp"]
                # Handle different timestamp formats
                if timestamp_str.endswith("Z"):
                    timestamp_str = timestamp_str[:-1] + "+00:00"
                elif not timestamp_str.endswith("+00:00") and not timestamp_str.endswith("-"):
                    # If no timezone info, assume UTC
                    if "+" not in timestamp_str and timestamp_str.count("-") <= 2:
                        timestamp_str += "+00:00"
                
                try:
                    metric_time = datetime.fromisoformat(timestamp_str)
                    if metric_time > cutoff_time:
                        recent_commands.append(metric)
                except ValueError:
                    # Skip metrics with invalid timestamps
                    continue
            
            return recent_commands

    async def _health_check_loop(self) -> None:
        """Background health check loop."""
        while self._running:
            try:
                await asyncio.sleep(self.health_check_interval_seconds)
                await self._perform_health_checks()
            except asyncio.CancelledError:
                break
            except Exception as e:
                if self.logger:
                    await self.logger.error("Error in worker health check", error=e)

    async def _perform_health_checks(self) -> None:
        """Perform health checks on all workers."""
        unhealthy_workers = []
        
        with self._metrics_lock:
            for worker_key, metrics in self._worker_metrics.items():
                # Check if worker has been inactive for too long
                if metrics.last_activity:
                    inactive_time = datetime.now(timezone.utc) - metrics.last_activity
                    if inactive_time.total_seconds() > (self.health_check_interval_seconds * 3):
                        metrics.health_status = "inactive"
                        unhealthy_workers.append((worker_key, "inactive", inactive_time.total_seconds()))
                
                # Check failure rate
                if metrics.failure_rate > 50:  # More than 50% failure rate
                    metrics.health_status = "failing"
                    unhealthy_workers.append((worker_key, "high_failure_rate", metrics.failure_rate))
                elif metrics.failure_rate > 20:  # More than 20% failure rate
                    metrics.health_status = "degraded" 
                elif metrics.health_status in ["failing", "degraded", "inactive"] and metrics.failure_rate < 10:
                    # Recover to healthy if failure rate is low
                    metrics.health_status = "healthy"
        
        # Log unhealthy workers
        if unhealthy_workers and self.logger:
            for worker_key, issue, value in unhealthy_workers:
                await self.logger.warning("Worker health issue detected",
                    worker_key=worker_key,
                    issue=issue,
                    value=value
                )

    def get_monitor_stats(self) -> Dict[str, Any]:
        """Get statistics about the worker monitor."""
        with self._metrics_lock:
            worker_count = len(self._worker_metrics)
            healthy_workers = sum(1 for m in self._worker_metrics.values() if m.health_status == "healthy")
        
        with self._timeseries_lock:
            total_metrics = sum(len(deque) for deque in self._worker_timeseries.values())
        
        return {
            "worker_count": worker_count,
            "healthy_workers": healthy_workers,
            "unhealthy_workers": worker_count - healthy_workers,
            "total_timeseries_metrics": total_metrics,
            "health_check_interval_seconds": self.health_check_interval_seconds,
            "metrics_retention_hours": self.metrics_retention_hours,
            "running": self._running,
        }