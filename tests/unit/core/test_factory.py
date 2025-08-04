"""
Tests for the factory module for creating framework components.
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock, ANY
from multiagents.core.factory import (
    MultiAgentSystem,
    MultiAgentSystemFactory,
    create_framework_components,
    create_simple_framework
)
from multiagents.monitoring.config import MonitoringConfig
from multiagents.orchestrator.workflow import WorkflowDefinition


class TestMultiAgentSystem:
    """Test cases for MultiAgentSystem class."""
    
    def test_initialization(self):
        """Test MultiAgentSystem initialization with all components."""
        # Arrange
        event_bus = Mock()
        worker_manager = Mock()
        orchestrator = Mock()
        event_monitor = Mock()
        worker_monitor = Mock()
        metrics_collector = Mock()
        
        # Act
        system = MultiAgentSystem(
            event_bus=event_bus,
            worker_manager=worker_manager,
            orchestrator=orchestrator,
            event_monitor=event_monitor,
            worker_monitor=worker_monitor,
            metrics_collector=metrics_collector
        )
        
        # Assert
        assert system.event_bus == event_bus
        assert system.worker_manager == worker_manager
        assert system.orchestrator == orchestrator
        assert system.event_monitor == event_monitor
        assert system.worker_monitor == worker_monitor
        assert system.metrics_collector == metrics_collector
    
    @pytest.mark.asyncio
    async def test_shutdown_all_components(self):
        """Test shutdown calls stop on all components."""
        # Arrange
        event_bus = AsyncMock()
        worker_manager = AsyncMock()
        orchestrator = AsyncMock()
        event_monitor = AsyncMock()
        worker_monitor = AsyncMock()
        metrics_collector = AsyncMock()
        
        system = MultiAgentSystem(
            event_bus=event_bus,
            worker_manager=worker_manager,
            orchestrator=orchestrator,
            event_monitor=event_monitor,
            worker_monitor=worker_monitor,
            metrics_collector=metrics_collector
        )
        
        # Act
        await system.shutdown()
        
        # Assert
        orchestrator.stop.assert_called_once()
        worker_manager.stop.assert_called_once()
        event_bus.stop.assert_called_once()
        event_monitor.stop.assert_called_once()
        worker_monitor.stop.assert_called_once()
        metrics_collector.stop.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_shutdown_with_none_components(self):
        """Test shutdown handles None components gracefully."""
        # Arrange
        system = MultiAgentSystem(
            event_bus=None,
            worker_manager=None,
            orchestrator=None,
            event_monitor=None,
            worker_monitor=None,
            metrics_collector=None
        )
        
        # Act & Assert - should not raise
        await system.shutdown()


class TestMultiAgentSystemFactory:
    """Test cases for MultiAgentSystemFactory."""
    
    @pytest.mark.asyncio
    @patch('multiagents.core.factory.RedisEventBus')
    @patch('multiagents.core.factory.WorkerManager')
    @patch('multiagents.core.factory.Orchestrator')
    @patch('multiagents.core.factory.EventMonitor')
    @patch('multiagents.core.factory.WorkerMonitor')
    @patch('multiagents.core.factory.MetricsCollector')
    async def test_create_system_with_defaults(
        self, 
        mock_metrics_collector,
        mock_worker_monitor,
        mock_event_monitor,
        mock_orchestrator,
        mock_worker_manager,
        mock_redis_event_bus
    ):
        """Test system creation with default configuration."""
        # Arrange
        mock_event_monitor_instance = AsyncMock()
        mock_worker_monitor_instance = AsyncMock()
        mock_metrics_collector_instance = AsyncMock()
        
        mock_event_monitor.return_value = mock_event_monitor_instance
        mock_worker_monitor.return_value = mock_worker_monitor_instance
        mock_metrics_collector.return_value = mock_metrics_collector_instance
        
        # Act
        system = await MultiAgentSystemFactory.create_system()
        
        # Assert
        assert isinstance(system, MultiAgentSystem)
        
        # Verify monitoring components were started
        mock_event_monitor_instance.start.assert_called_once()
        mock_worker_monitor_instance.start.assert_called_once()
        mock_metrics_collector_instance.start.assert_called_once()
        
        # Verify event bus was created with correct params
        mock_redis_event_bus.assert_called_once_with(
            redis_url="redis://localhost:6379",
            event_monitor=mock_event_monitor_instance,
            logger=ANY
        )
        
        # Verify worker manager was created with monitoring
        mock_worker_manager.assert_called_once_with(
            mock_redis_event_bus.return_value,
            event_monitor=mock_event_monitor_instance,
            worker_monitor=mock_worker_monitor_instance,
            logger=ANY
        )
        
        # Verify orchestrator was created
        mock_orchestrator.assert_called_once_with(
            event_bus=mock_redis_event_bus.return_value,
            logger=ANY
        )
    
    @pytest.mark.asyncio
    @patch('multiagents.core.factory.RedisEventBus')
    @patch('multiagents.core.factory.WorkerManager')
    @patch('multiagents.core.factory.Orchestrator')
    @patch('multiagents.core.factory.EventMonitor')
    @patch('multiagents.core.factory.WorkerMonitor')
    @patch('multiagents.core.factory.MetricsCollector')
    async def test_create_system_with_custom_config(
        self,
        mock_metrics_collector,
        mock_worker_monitor,
        mock_event_monitor,
        mock_orchestrator,
        mock_worker_manager,
        mock_redis_event_bus
    ):
        """Test system creation with custom monitoring configuration."""
        # Arrange
        custom_config = Mock(spec=MonitoringConfig)
        custom_logger = Mock()
        custom_config.create_logger.return_value = custom_logger
        
        mock_event_monitor_instance = AsyncMock()
        mock_worker_monitor_instance = AsyncMock()
        mock_metrics_collector_instance = AsyncMock()
        
        mock_event_monitor.return_value = mock_event_monitor_instance
        mock_worker_monitor.return_value = mock_worker_monitor_instance
        mock_metrics_collector.return_value = mock_metrics_collector_instance
        
        # Act
        system = await MultiAgentSystemFactory.create_system(
            redis_url="redis://custom:6380",
            monitoring_config=custom_config
        )
        
        # Assert
        custom_config.create_logger.assert_called_once()
        
        # Verify monitoring components created with custom logger
        mock_event_monitor.assert_called_once_with(logger=custom_logger)
        mock_worker_monitor.assert_called_once_with(logger=custom_logger)
        mock_metrics_collector.assert_called_once_with(logger=custom_logger)
        
        # Verify custom Redis URL was used
        mock_redis_event_bus.assert_called_once_with(
            redis_url="redis://custom:6380",
            event_monitor=mock_event_monitor_instance,
            logger=custom_logger
        )


class TestCreateFrameworkComponents:
    """Test cases for create_framework_components function."""
    
    @pytest.mark.asyncio
    @patch('multiagents.core.factory.RedisEventBus')
    @patch('multiagents.core.factory.WorkerManager')
    @patch('multiagents.core.factory.Orchestrator')
    @patch('multiagents.core.factory.EventMonitor')
    @patch('multiagents.core.factory.WorkerMonitor')
    @patch('multiagents.core.factory.MetricsCollector')
    async def test_create_components_with_workflow(
        self,
        mock_metrics_collector,
        mock_worker_monitor,
        mock_event_monitor,
        mock_orchestrator,
        mock_worker_manager,
        mock_redis_event_bus
    ):
        """Test creating components with workflow and default config."""
        # Arrange
        workflow = Mock(spec=WorkflowDefinition)
        
        mock_event_monitor_instance = AsyncMock()
        mock_worker_monitor_instance = AsyncMock()
        mock_metrics_collector_instance = AsyncMock()
        mock_event_bus_instance = Mock()
        mock_worker_manager_instance = Mock()
        mock_orchestrator_instance = Mock()
        
        mock_event_monitor.return_value = mock_event_monitor_instance
        mock_worker_monitor.return_value = mock_worker_monitor_instance
        mock_metrics_collector.return_value = mock_metrics_collector_instance
        mock_redis_event_bus.return_value = mock_event_bus_instance
        mock_worker_manager.return_value = mock_worker_manager_instance
        mock_orchestrator.return_value = mock_orchestrator_instance
        
        # Act
        result = await create_framework_components(workflow)
        
        # Assert
        assert len(result) == 6
        event_bus, worker_manager, orchestrator, event_monitor, worker_monitor, metrics_collector = result
        
        assert event_bus == mock_event_bus_instance
        assert worker_manager == mock_worker_manager_instance
        assert orchestrator == mock_orchestrator_instance
        assert event_monitor == mock_event_monitor_instance
        assert worker_monitor == mock_worker_monitor_instance
        assert metrics_collector == mock_metrics_collector_instance
        
        # Verify monitoring components were started
        mock_event_monitor_instance.start.assert_called_once()
        mock_worker_monitor_instance.start.assert_called_once()
        mock_metrics_collector_instance.start.assert_called_once()
        
        # Verify orchestrator was created with workflow
        mock_orchestrator.assert_called_once_with(
            workflow,
            mock_event_bus_instance,
            logger=ANY
        )
    
    @pytest.mark.asyncio
    @patch('multiagents.core.factory.RedisEventBus')
    @patch('multiagents.core.factory.WorkerManager')
    @patch('multiagents.core.factory.Orchestrator')
    @patch('multiagents.core.factory.EventMonitor')
    @patch('multiagents.core.factory.WorkerMonitor')
    @patch('multiagents.core.factory.MetricsCollector')
    async def test_create_components_with_custom_params(
        self,
        mock_metrics_collector,
        mock_worker_monitor,
        mock_event_monitor,
        mock_orchestrator,
        mock_worker_manager,
        mock_redis_event_bus
    ):
        """Test creating components with custom parameters."""
        # Arrange
        workflow = Mock(spec=WorkflowDefinition)
        custom_config = Mock(spec=MonitoringConfig)
        custom_logger = Mock()
        custom_config.create_logger.return_value = custom_logger
        
        mock_event_monitor_instance = AsyncMock()
        mock_worker_monitor_instance = AsyncMock()
        mock_metrics_collector_instance = AsyncMock()
        
        mock_event_monitor.return_value = mock_event_monitor_instance
        mock_worker_monitor.return_value = mock_worker_monitor_instance
        mock_metrics_collector.return_value = mock_metrics_collector_instance
        
        # Act
        result = await create_framework_components(
            workflow,
            redis_url="redis://custom:6380",
            monitoring_config=custom_config
        )
        
        # Assert
        custom_config.create_logger.assert_called_once()
        
        # Verify custom Redis URL was used
        mock_redis_event_bus.assert_called_once_with(
            redis_url="redis://custom:6380",
            event_monitor=mock_event_monitor_instance,
            logger=custom_logger
        )


class TestCreateSimpleFramework:
    """Test cases for create_simple_framework function."""
    
    @pytest.mark.asyncio
    @patch('multiagents.core.factory.RedisEventBus')
    @patch('multiagents.core.factory.WorkerManager')
    @patch('multiagents.core.factory.Orchestrator')
    async def test_create_simple_framework_minimal(
        self,
        mock_orchestrator,
        mock_worker_manager,
        mock_redis_event_bus
    ):
        """Test creating framework with minimal setup."""
        # Arrange
        workflow = Mock(spec=WorkflowDefinition)
        
        mock_event_bus_instance = Mock()
        mock_worker_manager_instance = Mock()
        mock_orchestrator_instance = Mock()
        
        mock_redis_event_bus.return_value = mock_event_bus_instance
        mock_worker_manager.return_value = mock_worker_manager_instance
        mock_orchestrator.return_value = mock_orchestrator_instance
        
        # Act
        result = await create_simple_framework(workflow)
        
        # Assert
        assert len(result) == 3
        event_bus, worker_manager, orchestrator = result
        
        assert event_bus == mock_event_bus_instance
        assert worker_manager == mock_worker_manager_instance
        assert orchestrator == mock_orchestrator_instance
        
        # Verify components created with minimal params
        mock_redis_event_bus.assert_called_once_with(redis_url="redis://localhost:6379")
        mock_worker_manager.assert_called_once_with(mock_event_bus_instance)
        mock_orchestrator.assert_called_once_with(workflow, mock_event_bus_instance)
    
    @pytest.mark.asyncio
    @patch('multiagents.core.factory.RedisEventBus')
    @patch('multiagents.core.factory.WorkerManager')
    @patch('multiagents.core.factory.Orchestrator')
    async def test_create_simple_framework_custom_redis(
        self,
        mock_orchestrator,
        mock_worker_manager,
        mock_redis_event_bus
    ):
        """Test creating framework with custom Redis URL."""
        # Arrange
        workflow = Mock(spec=WorkflowDefinition)
        custom_redis_url = "redis://custom:6380"
        
        # Act
        await create_simple_framework(workflow, redis_url=custom_redis_url)
        
        # Assert
        mock_redis_event_bus.assert_called_once_with(redis_url=custom_redis_url)