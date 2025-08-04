import asyncio
from typing import Dict, Any, Optional
import structlog
from datetime import datetime

from .interface import IOrchestrator, IWorkflowDefinition, IStateStore
from .workflow import WorkflowDefinition
from ..event_bus.interface import IEventBus
from ..event_bus.events import (
    CommandEvent, ResultEvent, StatusEvent, CompensationEvent,
    EventMetadata, EventType
)
from ..event_bus.redis_bus import RedisStateStore
from ..core.saga_context import SagaContext, SagaState
from ..core.exceptions import WorkflowException

logger = structlog.get_logger()


class Orchestrator(IOrchestrator):
    """
    Main orchestrator implementation that manages workflow execution.
    Acts as the central coordinator for the saga pattern.
    """

    def __init__(self, 
                 workflow: IWorkflowDefinition,
                 event_bus: IEventBus,
                 state_store: Optional[IStateStore] = None,
                 logger: Optional['ILogger'] = None,
                 monitoring_config: Optional['MonitoringConfig'] = None):
        self.workflow = workflow
        self.event_bus = event_bus
        self.state_store = state_store or RedisStateStore()
        self.active_workflows: Dict[str, SagaContext] = {}
        self._running = False
        
        # Auto-initialize logger if not provided
        if logger is None:
            from ..monitoring.config import MonitoringConfig
            config = monitoring_config or MonitoringConfig()
            logger = config.create_logger()
        
        self.monitoring_logger = logger

    async def start(self) -> None:
        """Start the orchestrator and subscribe to events."""
        # Connect state store if Redis-based
        if isinstance(self.state_store, RedisStateStore):
            await self.state_store.connect()
        
        # Subscribe to result events for all worker types in the workflow
        for step in self.workflow.get_steps():
            result_event_type = f"result.{step.worker_type}"
            await self.event_bus.subscribe(result_event_type, self._handle_result_event)
        
        self._running = True
        logger.info("Orchestrator started", workflow_id=self.workflow.get_id())

    async def stop(self) -> None:
        """Stop the orchestrator."""
        self._running = False
        
        # Disconnect state store
        if isinstance(self.state_store, RedisStateStore):
            await self.state_store.disconnect()
        
        logger.info("Orchestrator stopped", workflow_id=self.workflow.get_id())

    async def execute_workflow(self, workflow_id: str, initial_context: Dict[str, Any]) -> str:
        """Start a new workflow instance."""
        # Create new saga context
        context = SagaContext(
            workflow_id=workflow_id,
            data=initial_context,
            state=SagaState.RUNNING
        )
        
        # Store in memory and persistent store
        self.active_workflows[context.transaction_id] = context
        await self.state_store.save_context(context)
        
        # Publish status event
        await self._publish_status_event(context, "Workflow started")
        
        # Start with the first step
        initial_step = self.workflow.get_initial_step()
        if initial_step:
            await self._execute_step(context, initial_step)
        else:
            raise WorkflowException("No initial step defined in workflow")
        
        logger.info("Workflow started", 
                   workflow_id=workflow_id, 
                   transaction_id=context.transaction_id)
        
        return context.transaction_id

    async def get_status(self, transaction_id: str) -> Dict[str, Any]:
        """Get current status of a workflow instance."""
        # Check memory first
        if transaction_id in self.active_workflows:
            context = self.active_workflows[transaction_id]
        else:
            # Load from persistent store
            context_data = await self.state_store.load_context(transaction_id)
            if not context_data:
                raise WorkflowException(f"Workflow {transaction_id} not found")
            
            # Reconstruct context
            context = self._reconstruct_context(context_data)
        
        return {
            "transaction_id": context.transaction_id,
            "workflow_id": context.workflow_id,
            "state": context.state.value,
            "current_step": context.current_step,
            "created_at": context.created_at.isoformat(),
            "updated_at": context.updated_at.isoformat(),
            "step_results": context.step_results,
            "error": context.error,
            "execution_history": [
                {
                    "step": e.step_name,
                    "status": e.status,
                    "started_at": e.started_at.isoformat(),
                    "completed_at": e.completed_at.isoformat() if e.completed_at else None,
                }
                for e in context.execution_history
            ]
        }

    async def cancel_workflow(self, transaction_id: str) -> bool:
        """Cancel a running workflow."""
        # Load context
        context = await self._load_context(transaction_id)
        if not context:
            return False
        
        # Update state
        context.state = SagaState.CANCELLED
        context.updated_at = datetime.utcnow()
        
        # Save state
        await self.state_store.save_context(context)
        
        # Trigger compensations if needed
        if context.current_step:
            await self._trigger_compensations(context)
        
        # Publish status event
        await self._publish_status_event(context, "Workflow cancelled")
        
        logger.info("Workflow cancelled", transaction_id=transaction_id)
        
        return True

    async def _execute_step(self, context: SagaContext, step: 'WorkflowStep') -> None:
        """Execute a single workflow step."""
        try:
            # Create command event
            command = CommandEvent(
                metadata=EventMetadata(
                    transaction_id=context.transaction_id,
                    correlation_id=f"{context.transaction_id}.{step.name}",
                    source=self.workflow.get_id()
                ),
                worker_type=step.worker_type,
                timeout_seconds=step.timeout_seconds,
                retry_policy=step.retry_policy,
                payload=context.data
            )
            
            # Record step start
            context.record_step_start(step.name, command.id)
            
            # Save state
            await self.state_store.save_context(context)
            
            # Publish command event
            await self.event_bus.publish(
                f"command.{step.worker_type}",
                command.dict()
            )
            
            logger.info("Step started", 
                       transaction_id=context.transaction_id,
                       step=step.name,
                       worker_type=step.worker_type)
            
        except Exception as e:
            logger.error("Failed to execute step", 
                        transaction_id=context.transaction_id,
                        step=step.name,
                        error=str(e))
            context.record_step_failure(step.name, str(e))
            await self.state_store.save_context(context)
            await self._trigger_compensations(context)

    async def _handle_result_event(self, event_data: Dict[str, Any]) -> None:
        """Handle result events from workers."""
        try:
            # Parse result event
            result = ResultEvent(**event_data)
            
            # Load context
            context = await self._load_context(result.metadata.transaction_id)
            if not context:
                logger.warning("Context not found for result", 
                             transaction_id=result.metadata.transaction_id)
                return
            
            # Find current step
            current_step = None
            for step in self.workflow.get_steps():
                if step.name == context.current_step:
                    current_step = step
                    break
            
            if not current_step:
                logger.error("Current step not found", 
                           transaction_id=context.transaction_id,
                           current_step=context.current_step)
                return
            
            # Handle result
            if result.success:
                # Record success
                context.record_step_completion(current_step.name, result.payload)
                
                # Determine next step
                next_step = self.workflow.get_next_step(current_step.name, context)
                
                if next_step:
                    # Execute next step
                    await self._execute_step(context, next_step)
                else:
                    # Workflow completed
                    context.state = SagaState.COMPLETED
                    await self.state_store.save_context(context)
                    await self._publish_status_event(context, "Workflow completed")
                    
                    # Remove from active workflows
                    if context.transaction_id in self.active_workflows:
                        del self.active_workflows[context.transaction_id]
                    
                    logger.info("Workflow completed", 
                               transaction_id=context.transaction_id)
            else:
                # Handle failure
                context.record_step_failure(current_step.name, 
                                          result.error_message or "Unknown error")
                await self.state_store.save_context(context)
                
                # Trigger compensations
                await self._trigger_compensations(context)
                
        except Exception as e:
            logger.error("Failed to handle result event", 
                        event_data=event_data,
                        error=str(e))

    async def _trigger_compensations(self, context: SagaContext) -> None:
        """Trigger compensation actions for a failed workflow."""
        context.state = SagaState.COMPENSATING
        await self.state_store.save_context(context)
        
        # Get compensation steps
        compensation_steps = []
        for step in reversed(context.execution_history):
            if step.status == "completed":
                workflow_step = next(
                    (s for s in self.workflow.get_steps() if s.name == step.step_name),
                    None
                )
                if workflow_step and workflow_step.compensation:
                    compensation_steps.append((step, workflow_step))
        
        # Execute compensations
        for executed_step, workflow_step in compensation_steps:
            compensation_event = CompensationEvent(
                metadata=EventMetadata(
                    transaction_id=context.transaction_id,
                    correlation_id=f"{context.transaction_id}.comp.{executed_step.step_name}",
                    source=self.workflow.get_id()
                ),
                original_command_id=executed_step.command_id or "",
                compensation_type=workflow_step.compensation,
                payload=context.data
            )
            
            await self.event_bus.publish(
                f"compensation.{workflow_step.compensation}",
                compensation_event.dict()
            )
            
            logger.info("Compensation triggered",
                       transaction_id=context.transaction_id,
                       step=executed_step.step_name,
                       compensation=workflow_step.compensation)
        
        # Update final state
        context.state = SagaState.COMPENSATED
        await self.state_store.save_context(context)
        await self._publish_status_event(context, "Workflow compensated")

    async def _publish_status_event(self, context: SagaContext, message: str) -> None:
        """Publish a status update event."""
        status_event = StatusEvent(
            metadata=EventMetadata(
                transaction_id=context.transaction_id,
                correlation_id=context.transaction_id,
                source=self.workflow.get_id()
            ),
            status=context.state.value,
            message=message,
            payload={
                "workflow_id": context.workflow_id,
                "current_step": context.current_step,
                "step_results": context.step_results
            }
        )
        
        await self.event_bus.publish("status.workflow", status_event.dict())

    async def _load_context(self, transaction_id: str) -> Optional[SagaContext]:
        """Load context from memory or persistent store."""
        if transaction_id in self.active_workflows:
            return self.active_workflows[transaction_id]
        
        context_data = await self.state_store.load_context(transaction_id)
        if context_data:
            context = self._reconstruct_context(context_data)
            self.active_workflows[transaction_id] = context
            return context
        
        return None

    def _reconstruct_context(self, data: Dict[str, Any]) -> SagaContext:
        """Reconstruct SagaContext from dictionary."""
        from datetime import datetime
        
        context = SagaContext(
            transaction_id=data["transaction_id"],
            workflow_id=data["workflow_id"],
            state=SagaState(data["state"]),
            current_step=data.get("current_step"),
            data=data.get("data", {}),
            step_results=data.get("step_results", {}),
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
            error=data.get("error"),
            metadata=data.get("metadata", {})
        )
        
        # Reconstruct execution history
        for exec_data in data.get("execution_history", []):
            from ..core.saga_context import StepExecution
            execution = StepExecution(
                step_name=exec_data["step_name"],
                status=exec_data["status"],
                started_at=datetime.fromisoformat(exec_data["started_at"]),
                completed_at=datetime.fromisoformat(exec_data["completed_at"]) 
                           if exec_data.get("completed_at") else None,
                result=exec_data.get("result"),
                error=exec_data.get("error"),
                command_id=exec_data.get("command_id")
            )
            context.execution_history.append(execution)
        
        return context