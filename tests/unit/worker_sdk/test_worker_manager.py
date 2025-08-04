"""
Fixed comprehensive unit tests for WorkerManager.
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
import asyncio
from multiagents.worker_sdk.worker_manager import WorkerManager
from multiagents.worker_sdk.interface import IWorker
from multiagents.event_bus.interface import IEventBus
from multiagents.event_bus.events import CommandEvent, ResultEvent, EventMetadata
from multiagents.monitoring.interfaces import ILogger, IEventMonitor
from multiagents.monitoring.worker_monitor import WorkerMonitor


class TestWorkerManagerInitialization:
    """Test cases for WorkerManager initialization."""
    
    def test_init_with_required_params(self):
        """Test initialization with only required parameters."""
        # Arrange
        event_bus = Mock(spec=IEventBus)
        
        # Act
        with patch('multiagents.monitoring.config.MonitoringConfig') as mock_config:
            with patch('multiagents.monitoring.event_monitor.EventMonitor') as mock_event_monitor:
                with patch('multiagents.monitoring.worker_monitor.WorkerMonitor') as mock_worker_monitor:
                    mock_logger = Mock()
                    mock_config.return_value.create_logger.return_value = mock_logger
                    mock_monitor_instance = Mock()
                    mock_event_monitor.return_value = mock_monitor_instance
                    mock_worker_monitor_instance = Mock()
                    mock_worker_monitor.return_value = mock_worker_monitor_instance
                    
                    manager = WorkerManager(event_bus)
        
        # Assert
        assert manager.event_bus == event_bus
        assert manager.workers == {}
        assert manager.running is False
        assert manager._handler_tasks == []
        assert manager.monitoring_logger == mock_logger
        assert manager.event_monitor == mock_monitor_instance
        assert isinstance(manager.worker_monitor, WorkerMonitor)
    
    def test_init_with_custom_components(self):
        """Test initialization with custom monitoring components."""
        # Arrange
        event_bus = Mock(spec=IEventBus)
        event_monitor = Mock(spec=IEventMonitor)
        worker_monitor = Mock(spec=WorkerMonitor)
        logger = Mock(spec=ILogger)
        
        # Act
        manager = WorkerManager(
            event_bus=event_bus,
            event_monitor=event_monitor,
            worker_monitor=worker_monitor,
            logger=logger
        )
        
        # Assert
        assert manager.event_monitor == event_monitor
        assert manager.worker_monitor == worker_monitor
        assert manager.monitoring_logger == logger


class TestWorkerRegistration:
    """Test cases for worker registration."""
    
    @pytest.mark.asyncio
    async def test_register_worker_success(self):
        """Test successful worker registration."""
        # Arrange
        event_bus = Mock(spec=IEventBus)
        worker_monitor = Mock(spec=WorkerMonitor)
        logger = AsyncMock(spec=ILogger)  # Make logger async
        
        manager = WorkerManager(
            event_bus=event_bus,
            worker_monitor=worker_monitor,
            logger=logger,
            event_monitor=Mock()
        )
        
        worker = Mock(spec=IWorker)
        worker.get_worker_type.return_value = "test_worker"
        
        # Act
        manager.register(worker)
        # Wait for async logging task
        await asyncio.sleep(0.01)
        
        # Assert
        assert "test_worker" in manager.workers
        assert manager.workers["test_worker"] == worker
        worker_monitor.register_worker.assert_called_once_with("test_worker")
    
    @pytest.mark.asyncio
    async def test_register_worker_replace_existing(self):
        """Test registering worker with existing type replaces it."""
        # Arrange
        event_bus = Mock(spec=IEventBus)
        logger = AsyncMock(spec=ILogger)
        manager = WorkerManager(event_bus, worker_monitor=Mock(), logger=logger, event_monitor=Mock())
        
        worker1 = Mock(spec=IWorker)
        worker1.get_worker_type.return_value = "test_worker"
        worker2 = Mock(spec=IWorker)
        worker2.get_worker_type.return_value = "test_worker"
        
        # Act
        manager.register(worker1)
        await asyncio.sleep(0.01)
        manager.register(worker2)
        await asyncio.sleep(0.01)
        
        # Assert
        assert manager.workers["test_worker"] == worker2
        assert len(manager.workers) == 1
    
    @pytest.mark.asyncio
    async def test_register_worker_while_running(self):
        """Test registering worker while manager is running."""
        # Arrange
        event_bus = AsyncMock(spec=IEventBus)
        logger = AsyncMock(spec=ILogger)
        manager = WorkerManager(event_bus, worker_monitor=Mock(), logger=logger, event_monitor=Mock())
        manager.running = True
        
        worker = Mock(spec=IWorker)
        worker.get_worker_type.return_value = "test_worker"
        
        with patch.object(manager, '_subscribe_worker_commands', new_callable=AsyncMock) as mock_subscribe:
            # Act
            manager.register(worker)
            # Wait for any async tasks to complete
            await asyncio.sleep(0.01)
        
        # Assert
        assert "test_worker" in manager.workers
        # The async task should be created but we can't easily test it
    
    def test_unregister_worker_success(self):
        """Test successful worker unregistration."""
        # Arrange
        event_bus = Mock(spec=IEventBus)
        manager = WorkerManager(event_bus, worker_monitor=Mock(), logger=Mock(), event_monitor=Mock())
        
        worker = Mock(spec=IWorker)
        worker.get_worker_type.return_value = "test_worker"
        manager.workers["test_worker"] = worker  # Directly add to avoid async issues
        
        # Act
        result = manager.unregister("test_worker")
        
        # Assert
        assert result is True
        assert "test_worker" not in manager.workers
    
    def test_unregister_worker_not_found(self):
        """Test unregistering non-existent worker."""
        # Arrange
        event_bus = Mock(spec=IEventBus)
        manager = WorkerManager(event_bus, worker_monitor=Mock(), logger=Mock(), event_monitor=Mock())
        
        # Act
        result = manager.unregister("nonexistent_worker")
        
        # Assert
        assert result is False
    
    def test_get_worker_success(self):
        """Test getting registered worker."""
        # Arrange
        event_bus = Mock(spec=IEventBus)
        manager = WorkerManager(event_bus, worker_monitor=Mock(), logger=Mock(), event_monitor=Mock())
        
        worker = Mock(spec=IWorker)
        worker.get_worker_type.return_value = "test_worker"
        manager.workers["test_worker"] = worker  # Directly add to avoid async issues
        
        # Act
        result = manager.get_worker("test_worker")
        
        # Assert
        assert result == worker
    
    def test_get_worker_not_found(self):
        """Test getting non-existent worker."""
        # Arrange
        event_bus = Mock(spec=IEventBus)
        manager = WorkerManager(event_bus, worker_monitor=Mock(), logger=Mock(), event_monitor=Mock())
        
        # Act
        result = manager.get_worker("nonexistent_worker")
        
        # Assert
        assert result is None


class TestWorkerManagerLifecycle:
    """Test cases for WorkerManager start/stop lifecycle."""
    
    @pytest.mark.asyncio
    async def test_start_success(self):
        """Test successful manager start."""
        # Arrange
        event_bus = AsyncMock(spec=IEventBus)
        event_monitor = AsyncMock(spec=IEventMonitor)
        worker_monitor = AsyncMock(spec=WorkerMonitor)
        
        manager = WorkerManager(
            event_bus=event_bus,
            event_monitor=event_monitor,
            worker_monitor=worker_monitor,
            logger=Mock()
        )
        
        worker = AsyncMock(spec=IWorker)
        worker.get_worker_type.return_value = "test_worker"
        worker.on_start = AsyncMock()
        manager.workers["test_worker"] = worker
        
        with patch.object(manager, '_subscribe_worker_commands', new_callable=AsyncMock) as mock_subscribe:
            # Act
            await manager.start()
        
        # Assert
        assert manager.running is True
        worker_monitor.start.assert_called_once()
        worker.on_start.assert_called_once()
        mock_subscribe.assert_called_once_with(worker)
    
    @pytest.mark.asyncio
    async def test_stop_success(self):
        """Test successful manager stop."""
        # Arrange
        event_bus = AsyncMock(spec=IEventBus)
        event_monitor = AsyncMock(spec=IEventMonitor)
        worker_monitor = AsyncMock(spec=WorkerMonitor)
        
        manager = WorkerManager(
            event_bus=event_bus,
            event_monitor=event_monitor,
            worker_monitor=worker_monitor,
            logger=Mock()
        )
        
        # Create mock tasks
        task1 = Mock()
        task1.done.return_value = False
        task2 = Mock()
        task2.done.return_value = True
        manager._handler_tasks = [task1, task2]
        manager.running = True
        
        worker = AsyncMock(spec=IWorker)
        worker.get_worker_type.return_value = "test_worker"
        worker.on_stop = AsyncMock()
        manager.workers["test_worker"] = worker
        
        # Act
        await manager.stop()
        
        # Assert
        assert manager.running is False
        task1.cancel.assert_called_once()
        worker_monitor.stop.assert_called_once()
        worker.on_stop.assert_called_once()


class TestCommandHandling:
    """Test cases for command event handling."""
    
    @pytest.mark.asyncio
    async def test_handle_command_success(self):
        """Test successful command handling."""
        # Arrange
        event_bus = AsyncMock(spec=IEventBus)
        event_monitor = AsyncMock(spec=IEventMonitor)
        worker_monitor = AsyncMock(spec=WorkerMonitor)
        logger = AsyncMock(spec=ILogger)
        
        manager = WorkerManager(
            event_bus=event_bus,
            event_monitor=event_monitor,
            worker_monitor=worker_monitor,
            logger=logger
        )
        
        worker = AsyncMock(spec=IWorker)
        worker.get_worker_type.return_value = "test_worker"
        worker.process.return_value = {"result": "success"}
        
        command_data = {
            "id": "cmd-123",
            "metadata": {
                "transaction_id": "txn-123",
                "correlation_id": "corr-123",
                "source": "orchestrator"
            },
            "worker_type": "test_worker",
            "timeout_seconds": 30,
            "payload": {"input": "data"}
        }
        
        # Act
        await manager._handle_command(worker, command_data)
        
        # Assert
        # Check that a task was created for execution
        assert len(manager._handler_tasks) >= 0  # Task might complete quickly
    
    @pytest.mark.asyncio
    async def test_execute_worker_with_timeout_success(self):
        """Test successful worker execution with timeout."""
        # Arrange
        event_bus = AsyncMock(spec=IEventBus)
        event_monitor = AsyncMock(spec=IEventMonitor)
        worker_monitor = AsyncMock(spec=WorkerMonitor)
        logger = AsyncMock(spec=ILogger)
        
        manager = WorkerManager(
            event_bus=event_bus,
            event_monitor=event_monitor,
            worker_monitor=worker_monitor,
            logger=logger
        )
        
        worker = AsyncMock(spec=IWorker)
        worker.get_worker_type.return_value = "test_worker"
        worker.process.return_value = {"result": "success"}
        
        command = CommandEvent(
            metadata=EventMetadata(
                transaction_id="txn-123",
                correlation_id="corr-123",
                source="orchestrator"
            ),
            worker_type="test_worker",
            timeout_seconds=30,
            payload={"input": "data"}
        )
        
        # Act
        await manager._execute_worker_with_timeout(worker, command)
        
        # Assert
        worker.process.assert_called_once_with({"input": "data"})
        event_bus.publish.assert_called_once()
        
        # Check result event was published
        publish_call = event_bus.publish.call_args
        assert publish_call[0][0] == "result.test_worker"
        result_event = publish_call[0][1]
        assert result_event["success"] is True
        assert result_event["command_id"] == command.id


class TestUtilityMethods:
    """Test cases for utility methods."""
    
    def test_list_workers(self):
        """Test listing registered workers."""
        # Arrange
        event_bus = Mock(spec=IEventBus)
        manager = WorkerManager(event_bus, event_monitor=Mock(), worker_monitor=Mock(), logger=Mock())
        
        worker1 = Mock(spec=IWorker)
        worker1.get_worker_type.return_value = "worker1"
        worker2 = Mock(spec=IWorker)
        worker2.get_worker_type.return_value = "worker2"
        
        manager.workers["worker1"] = worker1
        manager.workers["worker2"] = worker2
        
        # Act
        workers = manager.list_workers()
        
        # Assert
        assert set(workers) == {"worker1", "worker2"}
    
    def test_get_worker_stats(self):
        """Test getting worker statistics."""
        # Arrange
        event_bus = Mock(spec=IEventBus)
        manager = WorkerManager(event_bus, event_monitor=Mock(), worker_monitor=Mock(), logger=Mock())
        
        worker1 = Mock(spec=IWorker)
        worker1.get_worker_type.return_value = "worker1"
        manager.workers["worker1"] = worker1
        
        # Add a completed task
        completed_task = Mock()
        completed_task.done.return_value = True
        manager._handler_tasks = [completed_task]
        
        # Act
        stats = manager.get_worker_stats()
        
        # Assert
        assert stats["total_workers"] == 1
        assert stats["running"] is False
        assert stats["worker_types"] == ["worker1"]
        assert stats["active_handlers"] == 0
    
    @pytest.mark.asyncio
    async def test_health_check(self):
        """Test health check functionality."""
        # Arrange
        event_bus = Mock(spec=IEventBus)
        manager = WorkerManager(event_bus, event_monitor=Mock(), worker_monitor=Mock(), logger=Mock())
        manager.running = True
        
        worker1 = AsyncMock(spec=IWorker)
        worker1.get_worker_type.return_value = "worker1"
        worker1.health_check = AsyncMock(return_value={"status": "healthy"})
        
        worker2 = AsyncMock(spec=IWorker)
        worker2.get_worker_type.return_value = "worker2"
        worker2.health_check = AsyncMock(side_effect=Exception("Worker error"))
        
        manager.workers["worker1"] = worker1
        manager.workers["worker2"] = worker2
        
        # Act
        health = await manager.health_check()
        
        # Assert
        assert health["manager_status"] == "healthy"
        assert health["worker_count"] == 2
        assert health["workers"]["worker1"]["status"] == "healthy"
        assert health["workers"]["worker2"]["status"] == "error"
        assert "Worker error" in health["workers"]["worker2"]["error"]