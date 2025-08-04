from abc import ABC, abstractmethod
from typing import Dict, Any, Callable, Awaitable, Optional
from dataclasses import dataclass

EventHandler = Callable[[Dict[str, Any]], Awaitable[None]]


class IEventBus(ABC):
    """
    Event Bus interface following Dependency Inversion Principle.
    All implementations must provide these core capabilities.
    """

    @abstractmethod
    async def publish(self, event_type: str, event_data: Dict[str, Any]) -> None:
        """
        Publish an event to the bus.
        
        Args:
            event_type: The type/topic of the event
            event_data: The event payload including metadata
        """
        pass

    @abstractmethod
    async def subscribe(self, event_type: str, handler: EventHandler) -> None:
        """
        Subscribe to events of a specific type.
        
        Args:
            event_type: The type/topic of events to subscribe to
            handler: Async function to handle events
        """
        pass

    @abstractmethod
    async def unsubscribe(self, event_type: str, handler: EventHandler) -> None:
        """
        Unsubscribe a handler from an event type.
        
        Args:
            event_type: The event type to unsubscribe from
            handler: The handler to remove
        """
        pass

    @abstractmethod
    async def start(self) -> None:
        """Start the event bus and begin processing events."""
        pass

    @abstractmethod
    async def stop(self) -> None:
        """Stop the event bus and clean up resources."""
        pass


class IEventPublisher(ABC):
    """Interface for components that publish events."""

    @abstractmethod
    async def publish_event(self, event: 'Event') -> None:
        """Publish a single event."""
        pass


class IEventSubscriber(ABC):
    """Interface for components that subscribe to events."""

    @abstractmethod
    async def handle_event(self, event: 'Event') -> None:
        """Handle an incoming event."""
        pass

    @abstractmethod
    def get_subscribed_events(self) -> list[str]:
        """Return list of event types this subscriber handles."""
        pass