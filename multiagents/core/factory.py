"""
Factory functions for creating framework components with automatic monitoring setup.
"""
from typing import Optional, Tuple
from ..event_bus.redis_bus import RedisEventBus
from ..worker_sdk.worker_manager import WorkerManager
from ..orchestrator.orchestrator import Orchestrator
from ..orchestrator.workflow import WorkflowDefinition
from ..monitoring.config import MonitoringConfig
from ..monitoring.event_monitor import EventMonitor
from ..monitoring.worker_monitor import WorkerMonitor
from ..monitoring.metrics_collector import MetricsCollector


class MultiAgentSystem:
    """Complete multi-agent system with all components."""
    
    def __init__(
        self, 
        event_bus: RedisEventBus,
        worker_manager: WorkerManager, 
        orchestrator: Orchestrator,
        event_monitor: EventMonitor,
        worker_monitor: WorkerMonitor,
        metrics_collector: MetricsCollector
    ):
        self.event_bus = event_bus
        self.worker_manager = worker_manager
        self.orchestrator = orchestrator
        self.event_monitor = event_monitor
        self.worker_monitor = worker_monitor
        self.metrics_collector = metrics_collector
    
    async def shutdown(self):
        """Shutdown all system components."""
        if self.orchestrator:
            await self.orchestrator.stop()
        if self.worker_manager:
            await self.worker_manager.stop()
        if self.event_bus:
            await self.event_bus.stop()
        if self.event_monitor:
            await self.event_monitor.stop()
        if self.worker_monitor:
            await self.worker_monitor.stop()
        if self.metrics_collector:
            await self.metrics_collector.stop()


class MultiAgentSystemFactory:
    """Factory for creating complete multi-agent systems."""
    
    @staticmethod
    async def create_system(
        redis_url: str = "redis://localhost:6379",
        monitoring_config: Optional[MonitoringConfig] = None
    ) -> MultiAgentSystem:
        """
        Create a complete multi-agent system.
        
        Args:
            redis_url: Redis connection URL
            monitoring_config: Optional monitoring configuration
            
        Returns:
            MultiAgentSystem instance
        """
        # Use default monitoring config if not provided
        config = monitoring_config or MonitoringConfig()
        logger = config.create_logger()
        
        # Create monitoring components
        event_monitor = EventMonitor(logger=logger)
        worker_monitor = WorkerMonitor(logger=logger)
        metrics_collector = MetricsCollector(logger=logger)
        
        # Start monitoring components
        await event_monitor.start()
        await worker_monitor.start()
        await metrics_collector.start()
        
        # Create framework components with monitoring
        event_bus = RedisEventBus(
            redis_url=redis_url,
            event_monitor=event_monitor,
            logger=logger
        )
        
        worker_manager = WorkerManager(
            event_bus,
            event_monitor=event_monitor,
            worker_monitor=worker_monitor,
            logger=logger
        )
        
        # Create orchestrator without workflow (can be added later)
        orchestrator = Orchestrator(
            event_bus=event_bus,
            logger=logger
        )
        
        return MultiAgentSystem(
            event_bus=event_bus,
            worker_manager=worker_manager,
            orchestrator=orchestrator,
            event_monitor=event_monitor,
            worker_monitor=worker_monitor,
            metrics_collector=metrics_collector
        )


async def create_framework_components(
    workflow: WorkflowDefinition,
    redis_url: str = "redis://localhost:6379",
    monitoring_config: Optional[MonitoringConfig] = None
) -> Tuple[RedisEventBus, WorkerManager, Orchestrator, EventMonitor, WorkerMonitor, MetricsCollector]:
    """
    Create and configure all framework components with automatic monitoring setup.
    
    Args:
        workflow: The workflow definition to use
        redis_url: Redis connection URL
        monitoring_config: Optional monitoring configuration (uses defaults if not provided)
    
    Returns:
        Tuple of (event_bus, worker_manager, orchestrator, event_monitor, worker_monitor, metrics_collector)
    """
    # Use default monitoring config if not provided
    config = monitoring_config or MonitoringConfig()
    logger = config.create_logger()
    
    # Create monitoring components
    event_monitor = EventMonitor(logger=logger)
    worker_monitor = WorkerMonitor(logger=logger)
    metrics_collector = MetricsCollector(logger=logger)
    
    # Start monitoring components
    await event_monitor.start()
    await worker_monitor.start()
    await metrics_collector.start()
    
    # Create framework components with monitoring
    event_bus = RedisEventBus(
        redis_url=redis_url,
        event_monitor=event_monitor,
        logger=logger
    )
    
    worker_manager = WorkerManager(
        event_bus,
        event_monitor=event_monitor,
        worker_monitor=worker_monitor,
        logger=logger
    )
    
    orchestrator = Orchestrator(
        workflow,
        event_bus,
        logger=logger
    )
    
    return event_bus, worker_manager, orchestrator, event_monitor, worker_monitor, metrics_collector


async def create_simple_framework(
    workflow: WorkflowDefinition,
    redis_url: str = "redis://localhost:6379"
) -> Tuple[RedisEventBus, WorkerManager, Orchestrator]:
    """
    Create framework components with minimal setup - monitoring is auto-initialized.
    
    Args:
        workflow: The workflow definition to use
        redis_url: Redis connection URL
    
    Returns:
        Tuple of (event_bus, worker_manager, orchestrator)
        
    Note:
        Access monitoring components via:
        - event_bus.event_monitor
        - worker_manager.worker_monitor  
        - event_bus.monitoring_logger
    """
    # Create components with auto-monitoring
    event_bus = RedisEventBus(redis_url=redis_url)
    worker_manager = WorkerManager(event_bus)
    orchestrator = Orchestrator(workflow, event_bus)
    
    return event_bus, worker_manager, orchestrator