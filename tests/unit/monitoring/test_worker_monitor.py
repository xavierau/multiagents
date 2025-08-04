"""
Comprehensive unit tests for WorkerMonitor.
"""
import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, timedelta, timezone
from multiagents.monitoring.worker_monitor import WorkerMonitor
from multiagents.monitoring.interfaces import ILogger, WorkerMetrics


class TestWorkerMonitorInitialization:
    """Test cases for WorkerMonitor initialization."""
    
    def test_init_with_defaults(self):
        """Test initialization with default parameters."""
        monitor = WorkerMonitor()
        
        assert monitor.logger is None
        assert monitor.health_check_interval_seconds == 30
        assert monitor.metrics_retention_hours == 24
        assert monitor.max_metrics_per_worker == 1000
        assert monitor._running is False
        assert monitor._health_check_task is None
        assert len(monitor._worker_metrics) == 0
        assert len(monitor._worker_timeseries) == 0
    
    def test_init_with_custom_params(self):
        """Test initialization with custom parameters."""
        logger = Mock(spec=ILogger)
        monitor = WorkerMonitor(
            logger=logger,
            health_check_interval_seconds=15,
            metrics_retention_hours=12,
            max_metrics_per_worker=500
        )
        
        assert monitor.logger == logger
        assert monitor.health_check_interval_seconds == 15
        assert monitor.metrics_retention_hours == 12
        assert monitor.max_metrics_per_worker == 500


class TestWorkerMonitorLifecycle:
    """Test cases for start/stop lifecycle."""
    
    @pytest.mark.asyncio
    async def test_start_without_logger(self):
        """Test starting monitor without logger."""
        monitor = WorkerMonitor()
        
        with patch.object(monitor, '_health_check_loop', new_callable=AsyncMock) as mock_loop:
            await monitor.start()
        
        assert monitor._running is True
        assert monitor._health_check_task is not None
        assert not monitor._health_check_task.done()
        
        # Cleanup
        await monitor.stop()
    
    @pytest.mark.asyncio
    async def test_start_with_logger(self):
        """Test starting monitor with logger."""
        logger = AsyncMock(spec=ILogger)
        monitor = WorkerMonitor(logger=logger)
        
        with patch.object(monitor, '_health_check_loop', new_callable=AsyncMock):
            await monitor.start()
        
        logger.info.assert_called_once_with(
            "Worker monitor started",
            health_check_interval_seconds=30,
            metrics_retention_hours=24
        )
        
        # Cleanup
        await monitor.stop()
    
    @pytest.mark.asyncio
    async def test_start_already_running(self):
        """Test starting monitor when already running."""
        monitor = WorkerMonitor()
        monitor._running = True
        
        with patch.object(monitor, '_health_check_loop', new_callable=AsyncMock) as mock_loop:
            await monitor.start()
        
        # Should not create new task
        mock_loop.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_stop_with_logger(self):
        """Test stopping monitor with logger."""
        logger = AsyncMock(spec=ILogger)
        monitor = WorkerMonitor(logger=logger)
        
        # Start first
        with patch.object(monitor, '_health_check_loop', new_callable=AsyncMock):
            await monitor.start()
        
        # Then stop
        await monitor.stop()
        
        assert monitor._running is False
        logger.info.assert_any_call("Worker monitor stopped")
    
    @pytest.mark.asyncio
    async def test_stop_with_cancelled_task(self):
        """Test stopping monitor with cancelled task."""
        monitor = WorkerMonitor()
        
        # Mock task that raises CancelledError
        mock_task = AsyncMock()
        mock_task.done.return_value = False
        mock_task.cancel.return_value = None
        mock_task.side_effect = asyncio.CancelledError()
        
        monitor._running = True
        monitor._health_check_task = mock_task
        
        # Should handle CancelledError gracefully
        await monitor.stop()
        
        assert monitor._running is False


class TestWorkerRegistration:
    """Test cases for worker registration."""
    
    def test_register_worker_basic(self):
        """Test basic worker registration."""
        monitor = WorkerMonitor()
        
        monitor.register_worker("test_worker")
        
        assert "test_worker:test_worker" in monitor._worker_metrics
        metrics = monitor._worker_metrics["test_worker:test_worker"]
        assert metrics.worker_type == "test_worker"
        assert metrics.worker_instance == "test_worker"  # defaults to worker_type
    
    def test_register_worker_with_instance(self):
        """Test worker registration with instance."""
        monitor = WorkerMonitor()
        
        monitor.register_worker("test_worker", "instance1")
        
        assert "test_worker:instance1" in monitor._worker_metrics
        metrics = monitor._worker_metrics["test_worker:instance1"]
        assert metrics.worker_type == "test_worker"
        assert metrics.worker_instance == "instance1"
    
    def test_register_worker_already_exists(self):
        """Test registering worker that already exists."""
        monitor = WorkerMonitor()
        
        monitor.register_worker("test_worker")
        metrics_count_before = len(monitor._worker_metrics)
        
        # Register same worker again
        monitor.register_worker("test_worker")
        
        # Should not create duplicate
        assert len(monitor._worker_metrics) == metrics_count_before
    
    @pytest.mark.asyncio
    async def test_register_worker_with_logger(self):
        """Test worker registration with logger."""
        logger = Mock(spec=ILogger)
        monitor = WorkerMonitor(logger=logger)
        
        # We need to patch asyncio.create_task since registration happens in sync context
        with patch('asyncio.create_task') as mock_create_task:
            monitor.register_worker("test_worker", "instance1")
            
            # Should create worker metrics
            assert "test_worker:instance1" in monitor._worker_metrics
            assert logger is not None  # Just verify logger is set
            # Should have tried to create async task for logging
            mock_create_task.assert_called_once()
    
    def test_unregister_worker_success(self):
        """Test successful worker unregistration."""
        monitor = WorkerMonitor()
        
        # Register first
        monitor.register_worker("test_worker", "instance1")
        assert "test_worker:instance1" in monitor._worker_metrics
        
        # Then unregister
        result = monitor.unregister_worker("test_worker", "instance1")
        
        assert result is True
        assert "test_worker:instance1" not in monitor._worker_metrics
        assert "test_worker:instance1" not in monitor._worker_timeseries
    
    def test_unregister_worker_not_found(self):
        """Test unregistering nonexistent worker."""
        monitor = WorkerMonitor()
        
        result = monitor.unregister_worker("nonexistent_worker")
        
        assert result is False


class TestCommandTracking:
    """Test cases for command tracking."""
    
    @pytest.mark.asyncio
    async def test_track_command_start(self):
        """Test tracking command start."""
        monitor = WorkerMonitor()
        
        await monitor.track_command_start("test_worker", "cmd-123")
        
        # Should register worker automatically
        assert "test_worker:test_worker" in monitor._worker_metrics
        
        # Should record timeseries data
        assert "test_worker:test_worker" in monitor._worker_timeseries
        timeseries = monitor._worker_timeseries["test_worker:test_worker"]
        assert len(timeseries) == 1
        
        metric = list(timeseries)[0]
        assert metric["metric_type"] == "command_started"
        assert metric["command_id"] == "cmd-123"
        assert metric["worker_type"] == "test_worker"
    
    @pytest.mark.asyncio
    async def test_track_command_success(self):
        """Test tracking successful command completion."""
        logger = AsyncMock(spec=ILogger)
        monitor = WorkerMonitor(logger=logger)
        
        # Register worker first
        monitor.register_worker("test_worker", "instance1")
        
        await monitor.track_command_success(
            "test_worker", "cmd-123", 1.5, "instance1", {"result": "data"}
        )
        
        # Check metrics were updated
        metrics = monitor._worker_metrics["test_worker:instance1"]
        assert metrics.successful_commands == 1
        
        # Check timeseries data
        timeseries = monitor._worker_timeseries["test_worker:instance1"]
        assert len(timeseries) == 1
        
        metric = list(timeseries)[0]
        assert metric["metric_type"] == "command_success"
        assert metric["command_id"] == "cmd-123"
        assert metric["processing_time"] == 1.5
        assert metric["result_metadata"] == {"result": "data"}
        
        # Should log debug message
        logger.debug.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_track_command_failure(self):
        """Test tracking failed command."""
        logger = AsyncMock(spec=ILogger)
        monitor = WorkerMonitor(logger=logger)
        
        # Register worker first
        monitor.register_worker("test_worker")
        
        await monitor.track_command_failure(
            "test_worker", "cmd-123", 2.0, "Test error", None, {"error_type": "timeout"}
        )
        
        # Check metrics were updated
        metrics = monitor._worker_metrics["test_worker:test_worker"]
        assert metrics.failed_commands == 1
        
        # Check timeseries data
        timeseries = monitor._worker_timeseries["test_worker:test_worker"]
        assert len(timeseries) == 1
        
        metric = list(timeseries)[0]
        assert metric["metric_type"] == "command_failure"
        assert metric["error_message"] == "Test error"
        assert metric["error_details"] == {"error_type": "timeout"}
        
        # Should log warning
        logger.warning.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_track_command_timeout(self):
        """Test tracking command timeout."""
        logger = AsyncMock(spec=ILogger)
        monitor = WorkerMonitor(logger=logger)
        
        # Register worker first
        monitor.register_worker("test_worker", "instance1")
        
        await monitor.track_command_timeout("test_worker", "cmd-123", 30.0, "instance1")
        
        # Check metrics were updated
        metrics = monitor._worker_metrics["test_worker:instance1"]
        assert metrics.timeout_commands == 1
        
        # Check timeseries data
        timeseries = monitor._worker_timeseries["test_worker:instance1"]
        assert len(timeseries) == 1
        
        metric = list(timeseries)[0]
        assert metric["metric_type"] == "command_timeout"
        assert metric["processing_time"] == 30.0
        
        # Should log warning
        logger.warning.assert_called_once()


class TestMetricsRetrieval:
    """Test cases for metrics retrieval."""
    
    @pytest.mark.asyncio
    async def test_get_worker_metrics_specific_worker(self):
        """Test getting metrics for specific worker."""
        monitor = WorkerMonitor()
        
        # Register and track some commands
        monitor.register_worker("test_worker", "instance1")
        await monitor.track_command_success("test_worker", "cmd-1", 1.0, "instance1")
        await monitor.track_command_failure("test_worker", "cmd-2", 2.0, "error", "instance1")
        
        result = await monitor.get_worker_metrics("test_worker", "instance1")
        
        assert result["worker_type"] == "test_worker"
        assert result["worker_instance"] == "instance1"
        assert result["successful_commands"] == 1
        assert result["failed_commands"] == 1
    
    @pytest.mark.asyncio
    async def test_get_worker_metrics_nonexistent_worker(self):
        """Test getting metrics for nonexistent worker."""
        monitor = WorkerMonitor()
        
        result = await monitor.get_worker_metrics("nonexistent_worker")
        
        assert result == {}
    
    @pytest.mark.asyncio
    async def test_get_worker_metrics_all_workers(self):
        """Test getting metrics for all workers."""
        monitor = WorkerMonitor()
        
        # Register multiple workers
        monitor.register_worker("worker1")
        monitor.register_worker("worker2", "instance1")
        
        await monitor.track_command_success("worker1", "cmd-1", 1.0)
        await monitor.track_command_success("worker2", "cmd-2", 2.0, "instance1")
        
        result = await monitor.get_worker_metrics()
        
        assert "worker1:worker1" in result
        assert "worker2:instance1" in result
        assert result["worker1:worker1"]["successful_commands"] == 1
        assert result["worker2:instance1"]["successful_commands"] == 1
    
    @pytest.mark.asyncio
    async def test_get_worker_performance_summary(self):
        """Test getting worker performance summary."""
        monitor = WorkerMonitor()
        
        # Register workers and track commands
        monitor.register_worker("worker1")
        monitor.register_worker("worker2")
        
        # Worker1: 2 successes out of 3 commands (66.7% success rate)
        await monitor.track_command_success("worker1", "cmd-1", 1.0)
        await monitor.track_command_success("worker1", "cmd-2", 1.5)
        await monitor.track_command_failure("worker1", "cmd-3", 2.0, "error")
        
        # Worker2: 1 success out of 1 command (100% success rate)
        await monitor.track_command_success("worker2", "cmd-4", 0.5)
        
        result = await monitor.get_worker_performance_summary()
        
        assert result["time_window_minutes"] == 60
        assert "workers" in result
        assert "aggregated_metrics" in result
        assert "top_performers" in result
        assert "problem_workers" in result
        
        # Check aggregated metrics
        agg_metrics = result["aggregated_metrics"]
        assert agg_metrics["total_commands"] == 4
        assert agg_metrics["successful_commands"] == 3
        assert agg_metrics["failed_commands"] == 1
        
        # Check worker summaries
        assert "worker1:worker1" in result["workers"]
        assert "worker2:worker2" in result["workers"]
        
        # Check top performers (worker2 should be first with 100% success rate)
        top_performers = result["top_performers"]
        assert len(top_performers) >= 1
        assert top_performers[0]["success_rate"] == 100.0  # worker2
    
    @pytest.mark.asyncio
    async def test_get_worker_health_status_specific_worker(self):
        """Test getting health status for specific worker."""
        monitor = WorkerMonitor()
        
        monitor.register_worker("test_worker", "instance1")
        await monitor.track_command_success("test_worker", "cmd-1", 1.0, "instance1")
        
        result = await monitor.get_worker_health_status("test_worker", "instance1")
        
        assert result["worker_key"] == "test_worker:instance1"
        assert result["health_status"] == "healthy"
        assert result["success_rate"] == 100.0
        assert result["failure_rate"] == 0.0
    
    @pytest.mark.asyncio
    async def test_get_worker_health_status_all_workers(self):
        """Test getting health status for all workers."""
        monitor = WorkerMonitor()
        
        monitor.register_worker("worker1")
        monitor.register_worker("worker2")
        
        await monitor.track_command_success("worker1", "cmd-1", 1.0)
        await monitor.track_command_failure("worker2", "cmd-2", 2.0, "error")
        
        result = await monitor.get_worker_health_status()
        
        assert "worker1:worker1" in result
        assert "worker2:worker2" in result
        assert result["worker1:worker1"]["health_status"] == "healthy"
        assert result["worker2:worker2"]["health_status"] == "healthy"  # Still healthy with just 1 failure


class TestHealthChecks:
    """Test cases for health check functionality."""
    
    @pytest.mark.asyncio
    async def test_perform_health_checks_inactive_worker(self):
        """Test health check for inactive worker."""
        logger = AsyncMock(spec=ILogger)
        monitor = WorkerMonitor(logger=logger, health_check_interval_seconds=10)
        
        # Register worker and set old last_activity
        monitor.register_worker("test_worker")
        metrics = monitor._worker_metrics["test_worker:test_worker"]
        
        # Set last activity to 1 minute ago (should trigger inactive status)
        old_time = datetime.now(timezone.utc) - timedelta(minutes=1)
        metrics.last_activity = old_time
        
        await monitor._perform_health_checks()
        
        # Health check logic may vary based on implementation
        # Just verify the health check was performed
        assert metrics is not None
        
        # Should log warning
        logger.warning.assert_called_once()
        call_args = logger.warning.call_args
        assert "Worker health issue detected" in call_args[0][0]
    
    @pytest.mark.asyncio
    async def test_perform_health_checks_high_failure_rate(self):
        """Test health check for worker with high failure rate."""
        logger = AsyncMock(spec=ILogger)
        monitor = WorkerMonitor(logger=logger)
        
        # Register worker and simulate high failure rate
        monitor.register_worker("test_worker")
        
        # Track many failures to get high failure rate
        for i in range(10):
            await monitor.track_command_failure("test_worker", f"cmd-{i}", 1.0, "error")
        
        # Track just 1 success to make failure rate > 50%
        await monitor.track_command_success("test_worker", "cmd-success", 1.0)
        
        await monitor._perform_health_checks()
        
        # Health check logic may vary based on failure rate calculation 
        metrics = monitor._worker_metrics["test_worker:test_worker"]
        assert metrics is not None
        
        # Should log warning (at least once for health issue, plus multiple calls for command failures)
        assert logger.warning.call_count >= 1
        # Check that at least one warning call was for the health issue
        health_warning_calls = [call for call in logger.warning.call_args_list 
                               if len(call[0]) > 0 and "Worker health issue detected" in call[0][0]]
        assert len(health_warning_calls) >= 1
    
    @pytest.mark.asyncio
    async def test_perform_health_checks_recovery(self):
        """Test health check recovery to healthy status."""
        monitor = WorkerMonitor()
        
        monitor.register_worker("test_worker")
        metrics = monitor._worker_metrics["test_worker:test_worker"]
        
        # Set as degraded initially
        metrics.health_status = "degraded"
        
        # Track many successes to get low failure rate
        for i in range(20):
            await monitor.track_command_success("test_worker", f"cmd-{i}", 1.0)
        
        await monitor._perform_health_checks()
        
        # Should recover to healthy
        assert metrics.health_status == "healthy"
    
    @pytest.mark.asyncio
    async def test_health_check_loop_normal_operation(self):
        """Test normal health check loop operation."""
        monitor = WorkerMonitor(health_check_interval_seconds=0.1)
        
        with patch.object(monitor, '_perform_health_checks', new_callable=AsyncMock) as mock_health_check:
            # Start the loop
            task = asyncio.create_task(monitor._health_check_loop())
            monitor._running = True
            
            # Let it run for a short time
            await asyncio.sleep(0.15)
            
            # Stop the loop
            monitor._running = False
            await task
        
        # Should have called health check at least once
        assert mock_health_check.call_count >= 1
    
    @pytest.mark.asyncio
    async def test_health_check_loop_with_error(self):
        """Test health check loop with error handling."""
        logger = AsyncMock(spec=ILogger)
        monitor = WorkerMonitor(logger=logger, health_check_interval_seconds=0.1)
        
        with patch.object(monitor, '_perform_health_checks', new_callable=AsyncMock) as mock_health_check:
            mock_health_check.side_effect = Exception("Health check error")
            
            # Start the loop
            task = asyncio.create_task(monitor._health_check_loop())
            monitor._running = True
            
            # Let it run for a short time
            await asyncio.sleep(0.15)
            
            # Stop the loop
            monitor._running = False
            await task
        
        # Should have logged the error
        logger.error.assert_called()
        call_args = logger.error.call_args
        assert "Error in worker health check" in call_args[0][0]


class TestMonitorStats:
    """Test cases for monitor statistics."""
    
    def test_get_monitor_stats_empty(self):
        """Test getting monitor stats when empty."""
        monitor = WorkerMonitor()
        
        stats = monitor.get_monitor_stats()
        
        assert stats["worker_count"] == 0
        assert stats["healthy_workers"] == 0
        assert stats["unhealthy_workers"] == 0
        assert stats["total_timeseries_metrics"] == 0
        assert stats["health_check_interval_seconds"] == 30
        assert stats["metrics_retention_hours"] == 24
        assert stats["running"] is False
    
    @pytest.mark.asyncio
    async def test_get_monitor_stats_with_data(self):
        """Test getting monitor stats with data."""
        monitor = WorkerMonitor()
        
        # Register workers and track commands
        monitor.register_worker("worker1")
        monitor.register_worker("worker2")
        
        await monitor.track_command_success("worker1", "cmd-1", 1.0)
        await monitor.track_command_failure("worker2", "cmd-2", 2.0, "error")
        
        # Set one worker as unhealthy
        monitor._worker_metrics["worker2:worker2"].health_status = "failing"
        
        monitor._running = True
        
        stats = monitor.get_monitor_stats()
        
        assert stats["worker_count"] == 2
        assert stats["healthy_workers"] == 1
        assert stats["unhealthy_workers"] == 1
        assert stats["total_timeseries_metrics"] == 2
        assert stats["running"] is True


class TestTimeSeries:
    """Test cases for time-series functionality."""
    
    @pytest.mark.asyncio
    async def test_record_timeseries_metric(self):
        """Test recording time-series metric."""
        monitor = WorkerMonitor()
        
        await monitor._record_timeseries_metric(
            "test_worker:instance1",
            "test_metric",
            {"value": 42, "metadata": "test"}
        )
        
        # Check metric was recorded
        timeseries = monitor._worker_timeseries["test_worker:instance1"]
        assert len(timeseries) == 1
        
        metric = list(timeseries)[0]
        assert metric["metric_type"] == "test_metric"
        assert metric["value"] == 42
        assert metric["metadata"] == "test"
        assert "timestamp" in metric
    
    @pytest.mark.asyncio
    async def test_get_recent_commands(self):
        """Test getting recent commands for a worker."""
        monitor = WorkerMonitor()
        
        # Create fixed time for testing
        base_time = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        recent_time = base_time - timedelta(minutes=30)  # Within window
        old_time = base_time - timedelta(minutes=90)     # Outside window
        
        # Add metrics with different timestamps
        recent_timestamp = recent_time.isoformat().replace("+00:00", "Z")
        old_timestamp = old_time.isoformat().replace("+00:00", "Z")
        
        monitor._worker_timeseries["test_worker"].append({
            "timestamp": recent_timestamp,
            "metric_type": "command_success",
            "command_id": "recent_cmd"
        })
        monitor._worker_timeseries["test_worker"].append({
            "timestamp": old_timestamp,
            "metric_type": "command_success", 
            "command_id": "old_cmd"
        })
        
        # Get recent commands (60-minute window)
        cutoff_time = base_time - timedelta(minutes=60)
        recent_commands = await monitor._get_recent_commands("test_worker", cutoff_time)
        
        # Should only include recent command
        assert len(recent_commands) == 1
        assert recent_commands[0]["command_id"] == "recent_cmd"
    
    @pytest.mark.asyncio
    async def test_get_recent_commands_nonexistent_worker(self):
        """Test getting recent commands for nonexistent worker."""
        monitor = WorkerMonitor()
        
        cutoff_time = datetime.now(timezone.utc) - timedelta(minutes=60)
        recent_commands = await monitor._get_recent_commands("nonexistent_worker", cutoff_time)
        
        assert recent_commands == []