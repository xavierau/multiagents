"""
Worker Manager for managing worker lifecycle and event subscriptions.
"""
from typing import Dict, Any, List, Optional
import asyncio
import structlog
from datetime import datetime

from .interface import IWorker, IWorkerRegistry
from ..event_bus.interface import IEventBus
from ..event_bus.events import CommandEvent, ResultEvent, EventMetadata
from ..core.exceptions import WorkerException
from ..monitoring.interfaces import ILogger, IEventMonitor
from ..monitoring.worker_monitor import WorkerMonitor

logger = structlog.get_logger()


class WorkerManager(IWorkerRegistry):
    """
    Manages worker lifecycle and event subscriptions.
    Provides centralized management for all workers in the system.
    """

    def __init__(self, event_bus: IEventBus,
                 event_monitor: Optional[IEventMonitor] = None,
                 worker_monitor: Optional[WorkerMonitor] = None,
                 logger: Optional[ILogger] = None,
                 monitoring_config: Optional['MonitoringConfig'] = None):
        self.event_bus = event_bus
        self.workers: Dict[str, IWorker] = {}
        self.running = False
        self._handler_tasks: List[asyncio.Task] = []
        
        # Monitoring integration - auto-initialize if not provided
        if any(component is None for component in [event_monitor, worker_monitor, logger]):
            from ..monitoring.config import MonitoringConfig
            from ..monitoring.event_monitor import EventMonitor
            
            config = monitoring_config or MonitoringConfig()
            if logger is None:
                logger = config.create_logger()
            if event_monitor is None:
                event_monitor = EventMonitor(logger=logger)
            if worker_monitor is None:
                worker_monitor = WorkerMonitor(logger=logger)
        
        self.event_monitor = event_monitor
        self.worker_monitor = worker_monitor
        self.monitoring_logger = logger

    def register(self, worker: IWorker) -> None:
        """
        Register a worker and subscribe to its events.
        
        Args:
            worker: Worker instance to register
        """
        worker_type = worker.get_worker_type()
        
        if worker_type in self.workers:
            logger.warning(f"Worker {worker_type} already registered, replacing")
        
        self.workers[worker_type] = worker
        
        # Register with worker monitor
        if self.worker_monitor:
            self.worker_monitor.register_worker(worker_type)
        
        logger.info(f"Registered worker: {worker_type}")
        
        # Log to monitoring logger
        if self.monitoring_logger:
            asyncio.create_task(self.monitoring_logger.info("Worker registered",
                worker_type=worker_type
            ))
        
        # If manager is running, subscribe to command events immediately
        if self.running:
            asyncio.create_task(self._subscribe_worker_commands(worker))

    def unregister(self, worker_type: str) -> bool:
        """
        Unregister a worker by type.
        
        Args:
            worker_type: Type of worker to unregister
            
        Returns:
            True if worker was unregistered, False if not found
        """
        if worker_type in self.workers:
            del self.workers[worker_type]
            logger.info(f"Unregistered worker: {worker_type}")
            return True
        return False

    def get_worker(self, worker_type: str) -> Optional[IWorker]:
        """Get a worker by type."""
        return self.workers.get(worker_type)

    def list_workers(self) -> List[str]:
        """List all registered worker types."""
        return list(self.workers.keys())

    async def start(self) -> None:
        """Start all workers and subscribe to their command events."""
        if self.running:
            logger.warning("Worker manager already running")
            return

        # Start monitoring components if available
        if self.worker_monitor:
            await self.worker_monitor.start()
        
        self.running = True
        
        # Start all workers
        for worker in self.workers.values():
            try:
                await worker.on_start()
                logger.info(f"Started worker: {worker.get_worker_type()}")
            except Exception as e:
                logger.error(f"Failed to start worker {worker.get_worker_type()}: {e}")

        # Subscribe to command events for each worker
        for worker in self.workers.values():
            await self._subscribe_worker_commands(worker)

        logger.info("Worker manager started")

    async def stop(self) -> None:
        """Stop all workers and clean up."""
        if not self.running:
            return

        self.running = False

        # Stop monitoring components if available
        if self.worker_monitor:
            await self.worker_monitor.stop()

        # Cancel any pending handler tasks
        for task in self._handler_tasks:
            if not task.done():
                task.cancel()

        # Stop all workers
        for worker in self.workers.values():
            try:
                await worker.on_stop()
                logger.info(f"Stopped worker: {worker.get_worker_type()}")
            except Exception as e:
                logger.error(f"Error stopping worker {worker.get_worker_type()}: {e}")

        logger.info("Worker manager stopped")

    async def _subscribe_worker_commands(self, worker: IWorker) -> None:
        """Subscribe to command events for a specific worker."""
        worker_type = worker.get_worker_type()
        command_event_type = f"command.{worker_type}"
        
        # Create a closure to capture the worker reference
        async def create_handler(w: IWorker):
            async def handler(event_data: Dict[str, Any]):
                await self._handle_command(w, event_data)
            return handler
        
        handler = await create_handler(worker)
        await self.event_bus.subscribe(command_event_type, handler)
        logger.info(f"Subscribed to commands for worker: {worker_type}")

    async def _handle_command(self, worker: IWorker, event_data: Dict[str, Any]) -> None:
        """
        Handle incoming command for a worker.
        
        Args:
            worker: Worker to handle the command
            event_data: Command event data
        """
        worker_type = worker.get_worker_type()
        
        try:
            # Parse command event
            command = CommandEvent(**event_data)
            
            logger.info(f"Worker {worker_type} processing command", 
                       command_id=command.id,
                       transaction_id=command.metadata.transaction_id)
            
            # Create a task for handling with timeout
            task = asyncio.create_task(
                self._execute_worker_with_timeout(worker, command)
            )
            self._handler_tasks.append(task)
            
            # Clean up completed tasks
            self._handler_tasks = [t for t in self._handler_tasks if not t.done()]
            
        except Exception as e:
            logger.error(f"Failed to handle command for worker {worker_type}", 
                        error=str(e),
                        event_data=event_data)

    async def _execute_worker_with_timeout(self, worker: IWorker, command: CommandEvent) -> None:
        """
        Execute worker with timeout and publish result.
        
        Args:
            worker: Worker to execute
            command: Command event to process
        """
        worker_type = worker.get_worker_type()
        start_time = datetime.utcnow()
        
        # Track command start
        if self.worker_monitor:
            await self.worker_monitor.track_command_start(worker_type, command.id)
        
        # Track event pickup
        if self.event_monitor:
            await self.event_monitor.track_event_pickup(command.id, worker_type)
            await self.event_monitor.track_event_processing(command.id)
        
        try:
            # Execute worker with timeout
            result = await asyncio.wait_for(
                worker.process(command.payload),
                timeout=command.timeout_seconds
            )
            
            # Calculate processing time
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            
            # Track successful completion
            if self.worker_monitor:
                await self.worker_monitor.track_command_success(
                    worker_type, command.id, processing_time, 
                    result_metadata=result
                )
            
            if self.event_monitor:
                await self.event_monitor.track_event_completion(command.id, result)
            
            # Create success result event
            result_event = ResultEvent(
                metadata=EventMetadata(
                    transaction_id=command.metadata.transaction_id,
                    correlation_id=command.metadata.correlation_id,
                    source=worker_type
                ),
                command_id=command.id,
                success=True,
                payload=result
            )
            
            logger.info(f"Worker {worker_type} completed successfully",
                       command_id=command.id)
            
            if self.monitoring_logger:
                await self.monitoring_logger.info("Worker command completed",
                    worker_type=worker_type,
                    command_id=command.id,
                    processing_time=processing_time
                )
            
        except asyncio.TimeoutError:
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            
            # Track timeout
            if self.worker_monitor:
                await self.worker_monitor.track_command_timeout(
                    worker_type, command.id, processing_time
                )
            
            if self.event_monitor:
                await self.event_monitor.track_event_timeout(command.id)
            
            logger.error(f"Worker {worker_type} timed out",
                        command_id=command.id,
                        timeout=command.timeout_seconds)
            
            if self.monitoring_logger:
                await self.monitoring_logger.error("Worker command timeout",
                    worker_type=worker_type,
                    command_id=command.id,
                    timeout_seconds=command.timeout_seconds,
                    processing_time=processing_time
                )
            
            # Create timeout error result
            result_event = ResultEvent(
                metadata=EventMetadata(
                    transaction_id=command.metadata.transaction_id,
                    correlation_id=command.metadata.correlation_id,
                    source=worker_type
                ),
                command_id=command.id,
                success=False,
                error_message=f"Worker timeout after {command.timeout_seconds}s",
                error_details={"error_type": "timeout"}
            )
            
        except Exception as e:
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            
            # Track failure
            if self.worker_monitor:
                await self.worker_monitor.track_command_failure(
                    worker_type, command.id, processing_time, str(e),
                    error_details={"error_type": type(e).__name__}
                )
            
            if self.event_monitor:
                await self.event_monitor.track_event_failure(
                    command.id, str(e), 
                    error_details={"error_type": type(e).__name__}
                )
            
            logger.error(f"Worker {worker_type} failed",
                        command_id=command.id,
                        error=str(e))
            
            if self.monitoring_logger:
                await self.monitoring_logger.error("Worker command failed",
                    error=e,
                    worker_type=worker_type,
                    command_id=command.id,
                    processing_time=processing_time
                )
            
            # Create failure result
            result_event = ResultEvent(
                metadata=EventMetadata(
                    transaction_id=command.metadata.transaction_id,
                    correlation_id=command.metadata.correlation_id,
                    source=worker_type
                ),
                command_id=command.id,
                success=False,
                error_message=str(e),
                error_details={"error_type": type(e).__name__}
            )

        # Publish result
        result_event_type = f"result.{worker_type}"
        try:
            await self.event_bus.publish(result_event_type, result_event.dict())
        except Exception as e:
            logger.error(f"Failed to publish result for worker {worker_type}",
                        command_id=command.id,
                        error=str(e))
            
            if self.monitoring_logger:
                await self.monitoring_logger.error("Failed to publish worker result",
                    error=e,
                    worker_type=worker_type,
                    command_id=command.id
                )

    async def health_check(self) -> Dict[str, Any]:
        """
        Check health of all workers.
        
        Returns:
            Health status for all workers
        """
        health_status = {
            "manager_status": "healthy" if self.running else "stopped",
            "worker_count": len(self.workers),
            "workers": {}
        }
        
        for worker_type, worker in self.workers.items():
            try:
                worker_health = await worker.health_check()
                health_status["workers"][worker_type] = worker_health
            except Exception as e:
                health_status["workers"][worker_type] = {
                    "status": "error",
                    "error": str(e)
                }
        
        return health_status

    def get_worker_stats(self) -> Dict[str, Any]:
        """
        Get statistics about registered workers.
        
        Returns:
            Worker statistics
        """
        return {
            "total_workers": len(self.workers),
            "running": self.running,
            "worker_types": self.list_workers(),
            "active_handlers": len([t for t in self._handler_tasks if not t.done()])
        }