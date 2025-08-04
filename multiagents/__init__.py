"""
MultiAgents - Hybrid Event-Driven Orchestration Framework

A framework for building scalable, fault-tolerant distributed systems
using a hybrid orchestration/choreography pattern.
"""

from .orchestrator import Orchestrator, WorkflowBuilder, WorkflowDefinition
from .worker_sdk import worker, dspy_worker, BaseWorker, DSPyAgent, WorkerManager
from .event_bus import IEventBus, Event, CommandEvent, ResultEvent
from .monitoring import (
    MonitoringConfig, EventMonitor, WorkerMonitor, MetricsCollector,
    ILogger, FileLogger, ConsoleLogger, CompositeLogger
)

__version__ = "0.1.0"

__all__ = [
    # Orchestrator
    "Orchestrator",
    "WorkflowBuilder", 
    "WorkflowDefinition",
    
    # Worker SDK
    "worker",
    "dspy_worker",
    "BaseWorker",
    "DSPyAgent",
    "WorkerManager",
    
    # Event Bus
    "IEventBus",
    "Event",
    "CommandEvent",
    "ResultEvent",
    
    # Monitoring
    "MonitoringConfig",
    "EventMonitor",
    "WorkerMonitor", 
    "MetricsCollector",
    "ILogger",
    "FileLogger",
    "ConsoleLogger",
    "CompositeLogger",
]