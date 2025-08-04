"""
Comprehensive unit tests for MetricsCollector.
"""
import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, timedelta, timezone
from multiagents.monitoring.metrics_collector import MetricsCollector
from multiagents.monitoring.interfaces import ILogger


class TestMetricsCollectorInitialization:
    """Test cases for MetricsCollector initialization."""
    
    def test_init_with_defaults(self):
        """Test initialization with default parameters."""
        collector = MetricsCollector()
        
        assert collector.logger is None
        assert collector.collection_interval_seconds == 60
        assert collector.retention_days == 7
        assert collector.max_metrics_per_type == 10000
        assert collector._running is False
        assert collector._collection_task is None
        assert len(collector._event_metrics) == 0
        assert len(collector._worker_metrics) == 0
        assert len(collector._system_metrics) == 0
    
    def test_init_with_custom_params(self):
        """Test initialization with custom parameters."""
        logger = Mock(spec=ILogger)
        collector = MetricsCollector(
            logger=logger,
            collection_interval_seconds=30,
            retention_days=3,
            max_metrics_per_type=5000
        )
        
        assert collector.logger == logger
        assert collector.collection_interval_seconds == 30
        assert collector.retention_days == 3
        assert collector.max_metrics_per_type == 5000


class TestMetricsCollectorLifecycle:
    """Test cases for start/stop lifecycle."""
    
    @pytest.mark.asyncio
    async def test_start_without_logger(self):
        """Test starting collector without logger."""
        collector = MetricsCollector()
        
        with patch.object(collector, '_collection_loop', new_callable=AsyncMock) as mock_loop:
            await collector.start()
        
        assert collector._running is True
        assert collector._collection_task is not None
        assert not collector._collection_task.done()
        
        # Cleanup
        await collector.stop()
    
    @pytest.mark.asyncio
    async def test_start_with_logger(self):
        """Test starting collector with logger."""
        logger = AsyncMock(spec=ILogger)
        collector = MetricsCollector(logger=logger)
        
        with patch.object(collector, '_collection_loop', new_callable=AsyncMock):
            await collector.start()
        
        logger.info.assert_called_once_with(
            "Metrics collector started",
            collection_interval_seconds=60,
            retention_days=7
        )
        
        # Cleanup
        await collector.stop()
    
    @pytest.mark.asyncio
    async def test_start_already_running(self):
        """Test starting collector when already running."""
        collector = MetricsCollector()
        collector._running = True
        
        with patch.object(collector, '_collection_loop', new_callable=AsyncMock) as mock_loop:
            await collector.start()
        
        # Should not create new task
        mock_loop.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_stop_with_logger(self):
        """Test stopping collector with logger."""
        logger = AsyncMock(spec=ILogger)
        collector = MetricsCollector(logger=logger)
        
        # Start first
        with patch.object(collector, '_collection_loop', new_callable=AsyncMock):
            await collector.start()
        
        # Then stop
        await collector.stop()
        
        assert collector._running is False
        logger.info.assert_any_call("Metrics collector stopped")
    
    @pytest.mark.asyncio
    async def test_stop_with_cancelled_task(self):
        """Test stopping collector with cancelled task."""
        collector = MetricsCollector()
        
        # Mock task that raises CancelledError
        mock_task = AsyncMock()
        mock_task.done.return_value = False
        mock_task.cancel.return_value = None
        mock_task.side_effect = asyncio.CancelledError()
        
        collector._running = True
        collector._collection_task = mock_task
        
        # Should handle CancelledError gracefully
        await collector.stop()
        
        assert collector._running is False


class TestMetricsRecording:
    """Test cases for metrics recording."""
    
    @pytest.mark.asyncio
    async def test_record_event_metric(self):
        """Test recording event metrics."""
        collector = MetricsCollector()
        
        await collector.record_event_metric(
            event_type="test_event",
            duration=1.5,
            success=True,
            metadata={"key": "value"}
        )
        
        # Check metric was recorded
        assert "test_event" in collector._event_metrics
        metrics = list(collector._event_metrics["test_event"])
        assert len(metrics) == 1
        
        metric = metrics[0]
        assert metric["event_type"] == "test_event"
        assert metric["duration"] == 1.5
        assert metric["success"] is True
        assert metric["metadata"] == {"key": "value"}
        assert "timestamp" in metric
    
    @pytest.mark.asyncio
    async def test_record_event_metric_without_metadata(self):
        """Test recording event metric without metadata."""
        collector = MetricsCollector()
        
        await collector.record_event_metric(
            event_type="test_event",
            duration=2.0,
            success=False
        )
        
        metrics = list(collector._event_metrics["test_event"])
        metric = metrics[0]
        assert metric["metadata"] == {}
    
    @pytest.mark.asyncio
    async def test_record_worker_metric(self):
        """Test recording worker metrics."""
        collector = MetricsCollector()
        
        await collector.record_worker_metric(
            worker_type="test_worker",
            metric_name="processing_time",
            value=0.8,
            metadata={"instance": "worker1"}
        )
        
        # Check metric was recorded
        assert "test_worker" in collector._worker_metrics
        metrics = list(collector._worker_metrics["test_worker"])
        assert len(metrics) == 1
        
        metric = metrics[0]
        assert metric["worker_type"] == "test_worker"
        assert metric["metric_name"] == "processing_time"
        assert metric["value"] == 0.8
        assert metric["metadata"] == {"instance": "worker1"}
        assert "timestamp" in metric
    
    @pytest.mark.asyncio
    async def test_record_system_metric(self):
        """Test recording system metrics."""
        collector = MetricsCollector()
        
        await collector.record_system_metric(
            metric_name="cpu_usage",
            value=45.2,
            metadata={"host": "server1"}
        )
        
        # Check metric was recorded
        metrics = list(collector._system_metrics)
        assert len(metrics) == 1
        
        metric = metrics[0]
        assert metric["metric_name"] == "cpu_usage"
        assert metric["value"] == 45.2
        assert metric["metadata"] == {"host": "server1"}
        assert "timestamp" in metric


class TestMetricsRetrieval:
    """Test cases for metrics retrieval and aggregation."""
    
    @pytest.mark.asyncio
    async def test_get_system_metrics_empty(self):
        """Test getting system metrics when empty."""
        collector = MetricsCollector()
        
        result = await collector.get_system_metrics()
        
        assert result["time_window_minutes"] == 60
        assert "collected_at" in result
        assert result["event_metrics"]["total_events"] == 0
        assert result["worker_metrics"]["total_metrics"] == 0
        assert result["system_metrics"]["total_metrics"] == 0
    
    @pytest.mark.asyncio
    async def test_get_system_metrics_with_data(self):
        """Test getting system metrics with recorded data."""
        collector = MetricsCollector()
        
        # Mock datetime to control timestamps
        fixed_time = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        with patch('multiagents.monitoring.metrics_collector.datetime') as mock_dt:
            mock_dt.now.return_value = fixed_time
            mock_dt.fromisoformat.side_effect = datetime.fromisoformat
            mock_dt.timezone = timezone
            
            # Record test data
            await collector.record_event_metric("test_event", 1.0, True)
            await collector.record_event_metric("test_event", 2.0, False)
            await collector.record_worker_metric("test_worker", "duration", 1.5)
            await collector.record_system_metric("cpu", 50.0)
        
            # Also mock the get_system_metrics call to use the same time
            result = await collector.get_system_metrics()
        
        # Check event metrics
        event_stats = result["event_metrics"]
        assert event_stats["total_events"] == 2
        assert event_stats["successful_events"] == 1
        assert event_stats["success_rate"] == 50.0
        assert event_stats["average_duration"] == 1.5
        
        # Check worker metrics
        worker_stats = result["worker_metrics"]
        assert worker_stats["total_metrics"] == 1
        assert "test_worker" in worker_stats["workers_by_type"]
        
        # Check system metrics
        system_stats = result["system_metrics"]
        assert "cpu" in system_stats
        assert system_stats["cpu"]["latest"] == 50.0
    
    @pytest.mark.asyncio
    async def test_get_worker_metrics_specific_worker(self):
        """Test getting metrics for specific worker."""
        collector = MetricsCollector()
        
        # Record test data for specific worker
        await collector.record_worker_metric("test_worker", "duration", 1.0)
        await collector.record_worker_metric("test_worker", "duration", 2.0)
        await collector.record_worker_metric("other_worker", "duration", 3.0)
        
        result = await collector.get_worker_metrics("test_worker")
        
        assert result["worker_type"] == "test_worker"
        assert len(result["metrics"]) == 2
        assert result["statistics"]["count"] == 2
        assert "duration" in result["statistics"]["metrics_by_name"]
    
    @pytest.mark.asyncio
    async def test_get_worker_metrics_nonexistent_worker(self):
        """Test getting metrics for nonexistent worker."""
        collector = MetricsCollector()
        
        result = await collector.get_worker_metrics("nonexistent_worker")
        
        assert result["worker_type"] == "nonexistent_worker"
        assert result["metrics"] == []
    
    @pytest.mark.asyncio
    async def test_get_worker_metrics_all_workers(self):
        """Test getting metrics for all workers."""
        collector = MetricsCollector()
        
        # Record test data for multiple workers
        await collector.record_worker_metric("worker1", "duration", 1.0)
        await collector.record_worker_metric("worker2", "duration", 2.0)
        
        result = await collector.get_worker_metrics()
        
        assert "workers" in result
        assert "worker1" in result["workers"]
        assert "worker2" in result["workers"]
        assert len(result["workers"]["worker1"]["metrics"]) == 1
        assert len(result["workers"]["worker2"]["metrics"]) == 1
    
    @pytest.mark.asyncio
    async def test_get_event_metrics_specific_event(self):
        """Test getting metrics for specific event type."""
        collector = MetricsCollector()
        
        # Record test data for specific event
        await collector.record_event_metric("test_event", 1.0, True)
        await collector.record_event_metric("test_event", 2.0, False)
        await collector.record_event_metric("other_event", 3.0, True)
        
        result = await collector.get_event_metrics("test_event")
        
        assert result["event_type"] == "test_event"
        assert len(result["metrics"]) == 2
        assert result["statistics"]["count"] == 2
        assert result["statistics"]["success_rate"] == 50.0
    
    @pytest.mark.asyncio
    async def test_get_event_metrics_nonexistent_event(self):
        """Test getting metrics for nonexistent event type."""
        collector = MetricsCollector()
        
        result = await collector.get_event_metrics("nonexistent_event")
        
        assert result["event_type"] == "nonexistent_event"
        assert result["metrics"] == []
    
    @pytest.mark.asyncio
    async def test_get_event_metrics_all_events(self):
        """Test getting metrics for all event types."""
        collector = MetricsCollector()
        
        # Record test data for multiple events
        await collector.record_event_metric("event1", 1.0, True)
        await collector.record_event_metric("event2", 2.0, False)
        
        result = await collector.get_event_metrics()
        
        assert "events" in result
        assert "event1" in result["events"]
        assert "event2" in result["events"]
        assert len(result["events"]["event1"]["metrics"]) == 1
        assert len(result["events"]["event2"]["metrics"]) == 1


class TestStatisticsCalculation:
    """Test cases for statistics calculation methods."""
    
    def test_calculate_event_statistics_empty(self):
        """Test event statistics calculation with empty metrics."""
        collector = MetricsCollector()
        
        stats = collector._calculate_event_statistics([])
        
        assert stats["total_events"] == 0
        assert stats["success_rate"] == 0.0
        assert stats["average_duration"] == 0.0
        assert stats["events_by_type"] == {}
    
    def test_calculate_event_statistics_with_data(self):
        """Test event statistics calculation with data."""
        collector = MetricsCollector()
        
        metrics = [
            {"success": True, "duration": 1.0, "event_type": "type1"},
            {"success": False, "duration": 2.0, "event_type": "type1"},
            {"success": True, "duration": 3.0, "event_type": "type2"}
        ]
        
        stats = collector._calculate_event_statistics(metrics)
        
        assert stats["total_events"] == 3
        assert stats["successful_events"] == 2
        assert stats["success_rate"] == (2/3) * 100
        assert stats["average_duration"] == 2.0
        assert stats["min_duration"] == 1.0
        assert stats["max_duration"] == 3.0
        assert stats["events_by_type"]["type1"] == 2
        assert stats["events_by_type"]["type2"] == 1
    
    def test_calculate_worker_statistics_empty(self):
        """Test worker statistics calculation with empty metrics."""
        collector = MetricsCollector()
        
        stats = collector._calculate_worker_statistics([])
        
        assert stats["total_metrics"] == 0
        assert stats["workers_by_type"] == {}
    
    def test_calculate_worker_statistics_with_data(self):
        """Test worker statistics calculation with data."""
        collector = MetricsCollector()
        
        metrics = [
            {"worker_type": "worker1", "metric_name": "duration", "value": 1.0},
            {"worker_type": "worker1", "metric_name": "duration", "value": 2.0},
            {"worker_type": "worker2", "metric_name": "throughput", "value": 5.0}
        ]
        
        stats = collector._calculate_worker_statistics(metrics)
        
        assert stats["total_metrics"] == 3
        assert stats["workers_by_type"]["worker1"] == 2
        assert stats["workers_by_type"]["worker2"] == 1
        assert "duration" in stats["metric_statistics"]
        assert stats["metric_statistics"]["duration"]["count"] == 2
        assert stats["metric_statistics"]["duration"]["average"] == 1.5
        assert stats["metric_statistics"]["duration"]["min"] == 1.0
        assert stats["metric_statistics"]["duration"]["max"] == 2.0
    
    def test_calculate_system_statistics_empty(self):
        """Test system statistics calculation with empty metrics."""
        collector = MetricsCollector()
        
        stats = collector._calculate_system_statistics([])
        
        assert stats["total_metrics"] == 0
        assert stats["metrics_by_name"] == {}
    
    def test_calculate_system_statistics_with_data(self):
        """Test system statistics calculation with data."""
        collector = MetricsCollector()
        
        metrics = [
            {"metric_name": "cpu", "value": 50.0},
            {"metric_name": "cpu", "value": 60.0},
            {"metric_name": "memory", "value": 80.0}
        ]
        
        stats = collector._calculate_system_statistics(metrics)
        
        assert "cpu" in stats
        assert stats["cpu"]["count"] == 2
        assert stats["cpu"]["average"] == 55.0
        assert stats["cpu"]["min"] == 50.0
        assert stats["cpu"]["max"] == 60.0
        assert stats["cpu"]["latest"] == 60.0
        
        assert "memory" in stats
        assert stats["memory"]["latest"] == 80.0


class TestMetricsCleanup:
    """Test cases for metrics cleanup and retention."""
    
    @pytest.mark.asyncio
    async def test_cleanup_old_metrics(self):
        """Test cleanup of old metrics."""
        collector = MetricsCollector(retention_days=1)
        
        # Create old timestamp (2 days ago)
        old_time = datetime.now(timezone.utc) - timedelta(days=2)
        old_timestamp = old_time.isoformat().replace("+00:00", "Z")
        
        # Create recent timestamp
        recent_time = datetime.now(timezone.utc)
        recent_timestamp = recent_time.isoformat().replace("+00:00", "Z")
        
        # Add metrics with different timestamps
        collector._event_metrics["test_event"].append({
            "timestamp": old_timestamp,
            "event_type": "test_event",
            "duration": 1.0,
            "success": True
        })
        collector._event_metrics["test_event"].append({
            "timestamp": recent_timestamp,
            "event_type": "test_event", 
            "duration": 2.0,
            "success": True
        })
        
        # Before cleanup
        assert len(collector._event_metrics["test_event"]) == 2
        
        # Run cleanup
        await collector._cleanup_old_metrics()
        
        # After cleanup - only recent metric should remain
        assert len(collector._event_metrics["test_event"]) == 1
        remaining_metric = list(collector._event_metrics["test_event"])[0]
        assert remaining_metric["timestamp"] == recent_timestamp


class TestSystemMetricsCollection:
    """Test cases for system metrics collection."""
    
    @pytest.mark.asyncio
    async def test_collect_system_metrics_with_psutil(self):
        """Test system metrics collection with psutil available."""
        collector = MetricsCollector()
        
        # Mock psutil - patch the import in the _collect_system_metrics method
        mock_process = Mock()
        mock_memory_info = Mock()
        mock_memory_info.rss = 1024 * 1024 * 100  # 100MB
        mock_memory_info.vms = 1024 * 1024 * 200  # 200MB
        mock_process.memory_info.return_value = mock_memory_info
        mock_process.cpu_percent.return_value = 25.5
        
        mock_virtual_memory = Mock()
        mock_virtual_memory.percent = 75.0
        
        mock_psutil = Mock()
        mock_psutil.Process.return_value = mock_process
        mock_psutil.cpu_percent.return_value = 50.0
        mock_psutil.virtual_memory.return_value = mock_virtual_memory
        
        # Patch the psutil import inside the method
        with patch('builtins.__import__') as mock_import:
            def import_side_effect(name, *args, **kwargs):
                if name == 'psutil':
                    return mock_psutil
                return __import__(name, *args, **kwargs)
            mock_import.side_effect = import_side_effect
            
            await collector._collect_system_metrics()
        
        # Check that system metrics were recorded
        assert len(collector._system_metrics) == 5
        metrics_by_name = {m["metric_name"]: m["value"] for m in collector._system_metrics}
        
        assert metrics_by_name["memory_rss_mb"] == 100.0
        assert metrics_by_name["memory_vms_mb"] == 200.0
        assert metrics_by_name["cpu_percent"] == 25.5
        assert metrics_by_name["system_cpu_percent"] == 50.0
        assert metrics_by_name["system_memory_percent"] == 75.0
    
    @pytest.mark.asyncio
    async def test_collect_system_metrics_without_psutil(self):
        """Test system metrics collection without psutil."""
        collector = MetricsCollector()
        
        # Patch the psutil import to raise ImportError
        with patch('builtins.__import__') as mock_import:
            def import_side_effect(name, *args, **kwargs):
                if name == 'psutil':
                    raise ImportError("No module named 'psutil'")
                elif name == 'sys':
                    # Return a mock sys module
                    mock_sys = Mock()
                    mock_sys.modules = {"module1": None, "module2": None}
                    return mock_sys
                return __import__(name, *args, **kwargs)
            mock_import.side_effect = import_side_effect
            
            await collector._collect_system_metrics()
        
        # Check that fallback metric was recorded
        assert len(collector._system_metrics) == 1
        metric = list(collector._system_metrics)[0]
        assert metric["metric_name"] == "python_objects"
        assert metric["value"] == 2
    
    @pytest.mark.asyncio
    async def test_collect_system_metrics_with_error(self):
        """Test system metrics collection with error handling."""
        logger = AsyncMock(spec=ILogger)
        collector = MetricsCollector(logger=logger)
        
        # Mock psutil that raises an exception during Process()
        mock_psutil = Mock()
        mock_psutil.Process.side_effect = Exception("Process error")
        
        # Patch the psutil import inside the method
        with patch('builtins.__import__') as mock_import:
            def import_side_effect(name, *args, **kwargs):
                if name == 'psutil':
                    return mock_psutil
                return __import__(name, *args, **kwargs)
            mock_import.side_effect = import_side_effect
            
            await collector._collect_system_metrics()
        
        # Should log warning about failure
        logger.warning.assert_called_once()
        call_args = logger.warning.call_args
        assert "Failed to collect system metrics" in call_args[0][0]


class TestCollectionLoop:
    """Test cases for background collection loop."""
    
    @pytest.mark.asyncio
    async def test_collection_loop_normal_operation(self):
        """Test normal collection loop operation."""
        collector = MetricsCollector(collection_interval_seconds=0.1)
        
        with patch.object(collector, '_collect_system_metrics', new_callable=AsyncMock) as mock_collect:
            with patch.object(collector, '_cleanup_old_metrics', new_callable=AsyncMock) as mock_cleanup:
                # Start the loop
                task = asyncio.create_task(collector._collection_loop())
                collector._running = True
                
                # Let it run for a short time
                await asyncio.sleep(0.15)
                
                # Stop the loop
                collector._running = False
                await task
        
        # Should have called collection methods at least once
        assert mock_collect.call_count >= 1
        assert mock_cleanup.call_count >= 1
    
    @pytest.mark.asyncio
    async def test_collection_loop_with_error(self):
        """Test collection loop with error handling."""
        logger = AsyncMock(spec=ILogger)
        collector = MetricsCollector(logger=logger, collection_interval_seconds=0.1)
        
        with patch.object(collector, '_collect_system_metrics', new_callable=AsyncMock) as mock_collect:
            mock_collect.side_effect = Exception("Collection error")
            
            # Start the loop
            task = asyncio.create_task(collector._collection_loop())
            collector._running = True
            
            # Let it run for a short time
            await asyncio.sleep(0.15)
            
            # Stop the loop
            collector._running = False
            await task
        
        # Should have logged the error
        logger.error.assert_called()
        call_args = logger.error.call_args
        assert "Error in metrics collection" in call_args[0][0]
    
    @pytest.mark.asyncio
    async def test_collection_loop_cancellation(self):
        """Test collection loop cancellation."""
        collector = MetricsCollector()
        
        # Start the loop
        task = asyncio.create_task(collector._collection_loop())
        collector._running = True
        
        # Cancel the task
        task.cancel()
        
        # Should handle cancellation gracefully
        with pytest.raises(asyncio.CancelledError):
            await task


class TestCollectorStats:
    """Test cases for collector statistics."""
    
    @pytest.mark.asyncio
    async def test_get_collector_stats_empty(self):
        """Test getting collector stats when empty."""
        collector = MetricsCollector()
        
        stats = collector.get_collector_stats()
        
        assert stats["event_types_tracked"] == 0
        assert stats["worker_types_tracked"] == 0
        assert stats["total_event_metrics"] == 0
        assert stats["total_worker_metrics"] == 0
        assert stats["total_system_metrics"] == 0
        assert stats["collection_interval_seconds"] == 60
        assert stats["retention_days"] == 7
        assert stats["running"] is False
    
    @pytest.mark.asyncio
    async def test_get_collector_stats_with_data(self):
        """Test getting collector stats with data."""
        collector = MetricsCollector()
        
        # Add some test data
        await collector.record_event_metric("event1", 1.0, True)
        await collector.record_event_metric("event1", 2.0, False)
        await collector.record_event_metric("event2", 3.0, True)
        
        await collector.record_worker_metric("worker1", "duration", 1.0)
        await collector.record_worker_metric("worker2", "throughput", 5.0)
        
        await collector.record_system_metric("cpu", 50.0)
        
        collector._running = True
        
        stats = collector.get_collector_stats()
        
        assert stats["event_types_tracked"] == 2
        assert stats["worker_types_tracked"] == 2
        assert stats["total_event_metrics"] == 3
        assert stats["total_worker_metrics"] == 2
        assert stats["total_system_metrics"] == 1
        assert stats["running"] is True


class TestTimeWindowFiltering:
    """Test cases for time window filtering."""
    
    @pytest.mark.asyncio
    async def test_time_window_filtering(self):
        """Test that metrics are properly filtered by time window."""
        collector = MetricsCollector()
        
        # Mock datetime to control timestamps
        fixed_time = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        
        with patch('multiagents.monitoring.metrics_collector.datetime') as mock_dt:
            mock_dt.now.return_value = fixed_time
            mock_dt.fromisoformat.side_effect = datetime.fromisoformat
            mock_dt.timezone = timezone
            
            # Create timestamps - one recent, one old
            recent_time = fixed_time - timedelta(minutes=30)  # Within 60-minute window
            old_time = fixed_time - timedelta(minutes=90)     # Outside 60-minute window
            
            recent_timestamp = recent_time.isoformat().replace("+00:00", "Z")
            old_timestamp = old_time.isoformat().replace("+00:00", "Z")
            
            # Manually add metrics with specific timestamps
            collector._event_metrics["test_event"].append({
                "timestamp": recent_timestamp,
                "event_type": "test_event",
                "duration": 1.0,
                "success": True
            })
            collector._event_metrics["test_event"].append({
                "timestamp": old_timestamp,
                "event_type": "test_event",
                "duration": 2.0,
                "success": True
            })
            
            # Get metrics with 60-minute window
            result = await collector.get_system_metrics(time_window_minutes=60)
            
            # Should only include recent metric
            assert result["event_metrics"]["total_events"] == 1
            
            # Get metrics with 120-minute window
            result = await collector.get_system_metrics(time_window_minutes=120)
            
            # Should include both metrics
            assert result["event_metrics"]["total_events"] == 2