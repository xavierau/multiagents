"""
System metrics collection and aggregation.
"""
import asyncio
from collections import defaultdict, deque
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, Optional, List, Deque
import threading
import json

from .interfaces import IMetricsCollector, ILogger


def _parse_timestamp(timestamp):
    """Helper function to parse timestamp consistently."""
    # Check if it's already a datetime object (handles mocked datetime too)
    if hasattr(timestamp, 'year') and hasattr(timestamp, 'month') and hasattr(timestamp, 'day'):
        # Already a datetime object, return it directly
        return timestamp
    elif not isinstance(timestamp, str):
        # Convert to string first
        timestamp = str(timestamp)
    
    if timestamp.endswith("Z"):
        timestamp = timestamp[:-1] + "+00:00"
    return datetime.fromisoformat(timestamp)


class MetricsCollector(IMetricsCollector):
    """
    Collects and aggregates system metrics for monitoring and analysis.
    Provides time-series data and statistical summaries.
    """

    def __init__(self, 
                 logger: Optional[ILogger] = None,
                 collection_interval_seconds: int = 60,
                 retention_days: int = 7,
                 max_metrics_per_type: int = 10000):
        
        self.logger = logger
        self.collection_interval_seconds = collection_interval_seconds
        self.retention_days = retention_days
        self.max_metrics_per_type = max_metrics_per_type
        
        # Thread-safe storage for metrics
        self._event_metrics: Dict[str, Deque[Dict[str, Any]]] = defaultdict(
            lambda: deque(maxlen=max_metrics_per_type)
        )
        self._worker_metrics: Dict[str, Deque[Dict[str, Any]]] = defaultdict(
            lambda: deque(maxlen=max_metrics_per_type)
        )
        self._system_metrics: Deque[Dict[str, Any]] = deque(maxlen=max_metrics_per_type)
        
        self._metrics_lock = threading.RLock()
        
        # Background collection task
        self._collection_task: Optional[asyncio.Task] = None
        self._running = False

    async def start(self) -> None:
        """Start metrics collection."""
        if not self._running:
            self._running = True
            self._collection_task = asyncio.create_task(self._collection_loop())
            
            if self.logger:
                await self.logger.info("Metrics collector started",
                    collection_interval_seconds=self.collection_interval_seconds,
                    retention_days=self.retention_days
                )

    async def stop(self) -> None:
        """Stop metrics collection."""
        self._running = False
        
        if self._collection_task and not self._collection_task.done():
            self._collection_task.cancel()
            try:
                await self._collection_task
            except asyncio.CancelledError:
                pass
        
        if self.logger:
            await self.logger.info("Metrics collector stopped")

    async def record_event_metric(self, event_type: str, duration: float, 
                                 success: bool, metadata: Optional[Dict[str, Any]] = None) -> None:
        """Record metrics for an event."""
        metric = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event_type": event_type,
            "duration": duration,
            "success": success,
            "metadata": metadata or {}
        }
        
        with self._metrics_lock:
            self._event_metrics[event_type].append(metric)

    async def record_worker_metric(self, worker_type: str, metric_name: str, 
                                 value: float, metadata: Optional[Dict[str, Any]] = None) -> None:
        """Record metrics for a worker."""
        metric = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "worker_type": worker_type,
            "metric_name": metric_name,
            "value": value,
            "metadata": metadata or {}
        }
        
        with self._metrics_lock:
            self._worker_metrics[worker_type].append(metric)

    async def record_system_metric(self, metric_name: str, value: float,
                                 metadata: Optional[Dict[str, Any]] = None) -> None:
        """Record system-level metrics."""
        metric = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "metric_name": metric_name,
            "value": value,
            "metadata": metadata or {}
        }
        
        with self._metrics_lock:
            self._system_metrics.append(metric)

    async def get_system_metrics(self, time_window_minutes: int = 60) -> Dict[str, Any]:
        """Get aggregated system metrics."""
        cutoff_time = datetime.now(timezone.utc) - timedelta(minutes=time_window_minutes)
        
        with self._metrics_lock:
            # Filter recent metrics
            recent_system_metrics = []
            for metric in self._system_metrics:
                if _parse_timestamp(metric["timestamp"]) > cutoff_time:
                    recent_system_metrics.append(metric)
            
            # Aggregate event metrics
            all_event_metrics = []
            for event_type, metrics in self._event_metrics.items():
                for metric in metrics:
                    if _parse_timestamp(metric["timestamp"]) > cutoff_time:
                        all_event_metrics.append(metric)
            
            # Aggregate worker metrics
            all_worker_metrics = []
            for worker_type, metrics in self._worker_metrics.items():
                for metric in metrics:
                    if _parse_timestamp(metric["timestamp"]) > cutoff_time:
                        all_worker_metrics.append(metric)

        # Calculate aggregated statistics
        event_stats = self._calculate_event_statistics(all_event_metrics)
        worker_stats = self._calculate_worker_statistics(all_worker_metrics)
        system_stats = self._calculate_system_statistics(recent_system_metrics)

        return {
            "time_window_minutes": time_window_minutes,
            "collected_at": datetime.utcnow().isoformat() + "Z",
            "event_metrics": event_stats,
            "worker_metrics": worker_stats,
            "system_metrics": system_stats,
        }

    async def get_worker_metrics(self, worker_type: str = None, 
                               time_window_minutes: int = 60) -> Dict[str, Any]:
        """Get worker-specific metrics."""
        cutoff_time = datetime.now(timezone.utc) - timedelta(minutes=time_window_minutes)
        
        with self._metrics_lock:
            if worker_type:
                # Get metrics for specific worker
                if worker_type not in self._worker_metrics:
                    return {
                        "worker_type": worker_type,
                        "time_window_minutes": time_window_minutes,
                        "metrics": []
                    }
                
                recent_metrics = []
                for metric in self._worker_metrics[worker_type]:
                    if _parse_timestamp(metric["timestamp"]) > cutoff_time:
                        recent_metrics.append(metric)
                
                return {
                    "worker_type": worker_type,
                    "time_window_minutes": time_window_minutes,
                    "metrics": recent_metrics,
                    "statistics": self._calculate_worker_type_statistics(recent_metrics)
                }
            else:
                # Get metrics for all workers
                all_worker_metrics = {}
                for wtype, metrics in self._worker_metrics.items():
                    recent_metrics = []
                    for metric in metrics:
                        if _parse_timestamp(metric["timestamp"]) > cutoff_time:
                            recent_metrics.append(metric)
                    
                    all_worker_metrics[wtype] = {
                        "metrics": recent_metrics,
                        "statistics": self._calculate_worker_type_statistics(recent_metrics)
                    }
                
                return {
                    "time_window_minutes": time_window_minutes,
                    "workers": all_worker_metrics
                }

    async def get_event_metrics(self, event_type: str = None,
                              time_window_minutes: int = 60) -> Dict[str, Any]:
        """Get event-specific metrics."""
        cutoff_time = datetime.now(timezone.utc) - timedelta(minutes=time_window_minutes)
        
        with self._metrics_lock:
            if event_type:
                # Get metrics for specific event type
                if event_type not in self._event_metrics:
                    return {
                        "event_type": event_type,
                        "time_window_minutes": time_window_minutes,
                        "metrics": []
                    }
                
                recent_metrics = []
                for metric in self._event_metrics[event_type]:
                    if _parse_timestamp(metric["timestamp"]) > cutoff_time:
                        recent_metrics.append(metric)
                
                return {
                    "event_type": event_type,
                    "time_window_minutes": time_window_minutes,
                    "metrics": recent_metrics,
                    "statistics": self._calculate_event_type_statistics(recent_metrics)
                }
            else:
                # Get metrics for all event types
                all_event_metrics = {}
                for etype, metrics in self._event_metrics.items():
                    recent_metrics = []
                    for metric in metrics:
                        if _parse_timestamp(metric["timestamp"]) > cutoff_time:
                            recent_metrics.append(metric)
                    
                    all_event_metrics[etype] = {
                        "metrics": recent_metrics,
                        "statistics": self._calculate_event_type_statistics(recent_metrics)
                    }
                
                return {
                    "time_window_minutes": time_window_minutes,
                    "events": all_event_metrics
                }

    def _calculate_event_statistics(self, metrics: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate statistics for event metrics."""
        if not metrics:
            return {
                "total_events": 0,
                "success_rate": 0.0,
                "average_duration": 0.0,
                "events_by_type": {}
            }
        
        total_events = len(metrics)
        successful_events = sum(1 for m in metrics if m["success"])
        success_rate = (successful_events / total_events) * 100
        
        durations = [m["duration"] for m in metrics]
        average_duration = sum(durations) / len(durations) if durations else 0.0
        
        events_by_type = defaultdict(int)
        for metric in metrics:
            events_by_type[metric["event_type"]] += 1
        
        return {
            "total_events": total_events,
            "successful_events": successful_events,
            "success_rate": success_rate,
            "average_duration": average_duration,
            "min_duration": min(durations) if durations else 0.0,
            "max_duration": max(durations) if durations else 0.0,
            "events_by_type": dict(events_by_type)
        }

    def _calculate_worker_statistics(self, metrics: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate statistics for worker metrics."""
        if not metrics:
            return {
                "total_metrics": 0,
                "workers_by_type": {}
            }
        
        workers_by_type = defaultdict(int)
        metrics_by_name = defaultdict(list)
        
        for metric in metrics:
            workers_by_type[metric["worker_type"]] += 1
            metrics_by_name[metric["metric_name"]].append(metric["value"])
        
        metric_stats = {}
        for metric_name, values in metrics_by_name.items():
            metric_stats[metric_name] = {
                "count": len(values),
                "average": sum(values) / len(values),
                "min": min(values),
                "max": max(values)
            }
        
        return {
            "total_metrics": len(metrics),
            "workers_by_type": dict(workers_by_type),
            "metric_statistics": metric_stats
        }

    def _calculate_system_statistics(self, metrics: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate statistics for system metrics."""
        if not metrics:
            return {
                "total_metrics": 0,
                "metrics_by_name": {}
            }
        
        metrics_by_name = defaultdict(list)
        for metric in metrics:
            metrics_by_name[metric["metric_name"]].append(metric["value"])
        
        stats = {}
        for metric_name, values in metrics_by_name.items():
            stats[metric_name] = {
                "count": len(values),
                "average": sum(values) / len(values),
                "min": min(values),
                "max": max(values),
                "latest": values[-1] if values else 0.0
            }
        
        return stats

    def _calculate_event_type_statistics(self, metrics: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate statistics for a specific event type."""
        if not metrics:
            return {
                "count": 0,
                "success_rate": 0.0,
                "average_duration": 0.0
            }
        
        count = len(metrics)
        successful = sum(1 for m in metrics if m["success"])
        success_rate = (successful / count) * 100
        
        durations = [m["duration"] for m in metrics]
        average_duration = sum(durations) / len(durations) if durations else 0.0
        
        return {
            "count": count,
            "successful": successful,
            "success_rate": success_rate,
            "average_duration": average_duration,
            "min_duration": min(durations) if durations else 0.0,
            "max_duration": max(durations) if durations else 0.0
        }

    def _calculate_worker_type_statistics(self, metrics: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate statistics for a specific worker type."""
        if not metrics:
            return {
                "count": 0,
                "metrics_by_name": {}
            }
        
        metrics_by_name = defaultdict(list)
        for metric in metrics:
            metrics_by_name[metric["metric_name"]].append(metric["value"])
        
        stats = {}
        for metric_name, values in metrics_by_name.items():
            stats[metric_name] = {
                "count": len(values),
                "average": sum(values) / len(values),
                "min": min(values),
                "max": max(values)
            }
        
        return {
            "count": len(metrics),
            "metrics_by_name": stats
        }

    async def _collection_loop(self) -> None:
        """Background metrics collection loop."""
        while self._running:
            try:
                await asyncio.sleep(self.collection_interval_seconds)
                await self._collect_system_metrics()
                await self._cleanup_old_metrics()
            except asyncio.CancelledError:
                break
            except Exception as e:
                if self.logger:
                    await self.logger.error("Error in metrics collection", error=e)

    async def _collect_system_metrics(self) -> None:
        """Collect system-level metrics."""
        try:
            # Memory usage
            import psutil
            process = psutil.Process()
            memory_info = process.memory_info()
            
            await self.record_system_metric("memory_rss_mb", memory_info.rss / 1024 / 1024)
            await self.record_system_metric("memory_vms_mb", memory_info.vms / 1024 / 1024)
            await self.record_system_metric("cpu_percent", process.cpu_percent())
            
            # System metrics
            await self.record_system_metric("system_cpu_percent", psutil.cpu_percent())
            memory = psutil.virtual_memory()
            await self.record_system_metric("system_memory_percent", memory.percent)
            
        except ImportError:
            # psutil not available, record basic metrics
            import sys
            await self.record_system_metric("python_objects", len(sys.modules))
        except Exception as e:
            if self.logger:
                await self.logger.warning("Failed to collect system metrics", error=e)

    async def _cleanup_old_metrics(self) -> None:
        """Clean up metrics older than retention period."""
        cutoff_time = datetime.now(timezone.utc) - timedelta(days=self.retention_days)
        
        with self._metrics_lock:
            # Clean event metrics
            for event_type, metrics in self._event_metrics.items():
                # Convert deque to list, filter, and convert back
                filtered_metrics = [
                    m for m in metrics
                    if _parse_timestamp(m["timestamp"]) > cutoff_time
                ]
                metrics.clear()
                metrics.extend(filtered_metrics)
            
            # Clean worker metrics
            for worker_type, metrics in self._worker_metrics.items():
                filtered_metrics = [
                    m for m in metrics
                    if _parse_timestamp(m["timestamp"]) > cutoff_time
                ]
                metrics.clear()
                metrics.extend(filtered_metrics)
            
            # Clean system metrics
            filtered_system_metrics = []
            for m in self._system_metrics:
                timestamp_str = m["timestamp"]
                if timestamp_str.endswith("Z"):
                    timestamp_str = timestamp_str[:-1] + "+00:00"
                if datetime.fromisoformat(timestamp_str) > cutoff_time:
                    filtered_system_metrics.append(m)
            self._system_metrics.clear()
            self._system_metrics.extend(filtered_system_metrics)

    def get_collector_stats(self) -> Dict[str, Any]:
        """Get statistics about the metrics collector."""
        with self._metrics_lock:
            event_types_count = len(self._event_metrics)
            worker_types_count = len(self._worker_metrics)
            system_metrics_count = len(self._system_metrics)
            
            total_event_metrics = sum(len(metrics) for metrics in self._event_metrics.values())
            total_worker_metrics = sum(len(metrics) for metrics in self._worker_metrics.values())
        
        return {
            "event_types_tracked": event_types_count,
            "worker_types_tracked": worker_types_count,
            "total_event_metrics": total_event_metrics,
            "total_worker_metrics": total_worker_metrics,
            "total_system_metrics": system_metrics_count,
            "collection_interval_seconds": self.collection_interval_seconds,
            "retention_days": self.retention_days,
            "running": self._running,
        }