import asyncio
import json
from typing import Dict, Any, List, Optional
import redis.asyncio as redis
import structlog
from collections import defaultdict
from datetime import datetime, date
import uuid

from .interface import IEventBus, EventHandler
from .events import Event
from ..core.exceptions import EventBusException
from ..monitoring.interfaces import IEventMonitor, ILogger

logger = structlog.get_logger()


class EventEncoder(json.JSONEncoder):
    """Custom JSON encoder for event data that handles datetime objects."""
    
    def default(self, obj):
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        elif isinstance(obj, uuid.UUID):
            return str(obj)
        return super().default(obj)


class RedisEventBus(IEventBus):
    """
    Redis Pub/Sub implementation of the event bus.
    Follows Liskov Substitution Principle - can replace any IEventBus.
    """

    def __init__(self, redis_url: str = "redis://localhost:6379", 
                 channel_prefix: str = "multiagent:",
                 event_monitor: Optional[IEventMonitor] = None,
                 logger: Optional[ILogger] = None,
                 monitoring_config: Optional['MonitoringConfig'] = None):
        self.redis_url = redis_url
        self.channel_prefix = channel_prefix
        self.redis_client: Optional[redis.Redis] = None
        self.pubsub: Optional[redis.client.PubSub] = None
        self.handlers: Dict[str, List[EventHandler]] = defaultdict(list)
        self._running = False
        self._listener_task: Optional[asyncio.Task] = None
        
        # Monitoring integration - auto-initialize if not provided
        if event_monitor is None or logger is None:
            from ..monitoring.config import MonitoringConfig
            from ..monitoring.event_monitor import EventMonitor
            from ..monitoring.metrics_collector import MetricsCollector
            
            config = monitoring_config or MonitoringConfig()
            if logger is None:
                logger = config.create_logger()
            if event_monitor is None:
                event_monitor = EventMonitor(logger=logger)
        
        # Create metrics collector automatically
        if not hasattr(self, 'metrics_collector'):
            from ..monitoring.metrics_collector import MetricsCollector
            self.metrics_collector = MetricsCollector(logger=logger)
        
        self.event_monitor = event_monitor
        self.monitoring_logger = logger

    async def start(self) -> None:
        """Start the event bus and begin processing events."""
        try:
            # Create Redis client
            self.redis_client = await redis.from_url(self.redis_url)
            self.pubsub = self.redis_client.pubsub()
            
            # Start monitoring if available
            if self.event_monitor:
                await self.event_monitor.start()
            if hasattr(self, 'metrics_collector') and self.metrics_collector:
                await self.metrics_collector.start()
            
            # Mark as running but don't start listener until first subscription
            self._running = True
            
            logger.info("Redis event bus started", redis_url=self.redis_url)
            
        except Exception as e:
            logger.error("Failed to start Redis event bus", error=str(e))
            raise EventBusException(f"Failed to start event bus: {str(e)}") from e

    async def stop(self) -> None:
        """Stop the event bus and clean up resources."""
        self._running = False
        
        # Stop monitoring if available
        if self.event_monitor:
            await self.event_monitor.stop()
        if hasattr(self, 'metrics_collector') and self.metrics_collector:
            await self.metrics_collector.stop()
        
        if self._listener_task:
            self._listener_task.cancel()
            try:
                await self._listener_task
            except asyncio.CancelledError:
                pass
        
        if self.pubsub:
            await self.pubsub.close()
        
        if self.redis_client:
            await self.redis_client.close()
        
        logger.info("Redis event bus stopped")

    async def publish(self, event_type: str, event_data: Dict[str, Any]) -> None:
        """Publish an event to Redis."""
        if not self.redis_client:
            raise EventBusException("Event bus not started")
        
        try:
            # Create channel name
            channel = f"{self.channel_prefix}{event_type}"
            
            # Track event dispatch if monitoring is enabled
            if self.event_monitor and "id" in event_data:
                await self.event_monitor.track_event_dispatch(
                    event_id=event_data["id"],
                    event_type=event_data.get("type", event_type),
                    transaction_id=event_data.get("metadata", {}).get("transaction_id", "unknown"),
                    correlation_id=event_data.get("metadata", {}).get("correlation_id", "unknown"),
                    source="redis_event_bus",
                    metadata={"channel": channel, "event_type": event_type}
                )
            
            # Serialize event data with custom encoder for datetime objects
            message = json.dumps(event_data, cls=EventEncoder)
            
            # Publish to Redis
            await self.redis_client.publish(channel, message)
            
            logger.debug("Event published", event_type=event_type, channel=channel)
            
            # Log to monitoring logger
            if self.monitoring_logger:
                await self.monitoring_logger.debug("Event published",
                    event_type=event_type,
                    channel=channel,
                    event_id=event_data.get("id", "unknown")
                )
            
        except Exception as e:
            logger.error("Failed to publish event", event_type=event_type, error=str(e))
            
            # Log error to monitoring logger
            if self.monitoring_logger:
                await self.monitoring_logger.error("Failed to publish event", 
                    error=e,
                    event_type=event_type,
                    event_id=event_data.get("id", "unknown")
                )
            
            raise EventBusException(f"Failed to publish event: {str(e)}") from e

    async def subscribe(self, event_type: str, handler: EventHandler) -> None:
        """Subscribe to events of a specific type."""
        # Check if this is the first handler for this event type
        is_first_handler = len(self.handlers[event_type]) == 0
        
        # Check if this is the very first subscription
        has_any_handlers = any(len(handlers) > 0 for handlers in self.handlers.values())
        
        # Add handler to local registry
        self.handlers[event_type].append(handler)
        
        # Subscribe to Redis channel if this is the first handler for this event type
        if self.pubsub and is_first_handler:
            channel = f"{self.channel_prefix}{event_type}"
            await self.pubsub.subscribe(channel)
            logger.info("Subscribed to event type", event_type=event_type, channel=channel)
            
            # Start listener task if this is the very first subscription
            if not has_any_handlers and not self._listener_task:
                self._listener_task = asyncio.create_task(self._listen_for_messages())
                logger.info("Started message listener")

    async def unsubscribe(self, event_type: str, handler: EventHandler) -> None:
        """Unsubscribe a handler from an event type."""
        if event_type in self.handlers and handler in self.handlers[event_type]:
            self.handlers[event_type].remove(handler)
            
            # If no more handlers for this event type, unsubscribe from Redis
            if not self.handlers[event_type]:
                if self.pubsub:
                    channel = f"{self.channel_prefix}{event_type}"
                    await self.pubsub.unsubscribe(channel)
                del self.handlers[event_type]
                logger.info("Unsubscribed from event type", event_type=event_type)

    async def _listen_for_messages(self) -> None:
        """Listen for messages from Redis and dispatch to handlers."""
        if not self.pubsub:
            return
        
        try:
            while self._running:
                try:
                    # Get message with timeout to allow checking _running flag
                    message = await asyncio.wait_for(
                        self.pubsub.get_message(ignore_subscribe_messages=True),
                        timeout=1.0
                    )
                    
                    if message and message['type'] == 'message':
                        await self._handle_message(message)
                        
                except asyncio.TimeoutError:
                    # Timeout is expected, continue loop
                    continue
                    
        except Exception as e:
            logger.error("Error in message listener", error=str(e))
            if self._running:
                # Restart listener if still running
                self._listener_task = asyncio.create_task(self._listen_for_messages())

    async def _handle_message(self, message: Dict[str, Any]) -> None:
        """Handle a message from Redis."""
        try:
            # Extract channel and data
            channel = message['channel'].decode('utf-8')
            data = json.loads(message['data'])
            
            # Extract event type from channel
            event_type = channel.replace(self.channel_prefix, '')
            
            # Dispatch to handlers
            if event_type in self.handlers:
                for handler in self.handlers[event_type]:
                    try:
                        await handler(data)
                    except Exception as e:
                        logger.error("Handler error", 
                                   event_type=event_type, 
                                   handler=handler, 
                                   error=str(e))
                        
        except Exception as e:
            logger.error("Failed to handle message", message=message, error=str(e))


class RedisStateStore:
    """Redis-based state store for saga contexts."""

    def __init__(self, redis_url: str = "redis://localhost:6379",
                 key_prefix: str = "saga:"):
        self.redis_url = redis_url
        self.key_prefix = key_prefix
        self.redis_client: Optional[redis.Redis] = None

    async def connect(self) -> None:
        """Connect to Redis."""
        self.redis_client = await redis.from_url(self.redis_url)

    async def disconnect(self) -> None:
        """Disconnect from Redis."""
        if self.redis_client:
            await self.redis_client.close()

    async def save_context(self, context: 'SagaContext') -> None:
        """Save a saga context to Redis."""
        if not self.redis_client:
            raise EventBusException("State store not connected")
        
        key = f"{self.key_prefix}{context.transaction_id}"
        value = json.dumps(context.to_dict())
        
        # Set with expiration (7 days by default)
        await self.redis_client.setex(key, 604800, value)

    async def load_context(self, transaction_id: str) -> Optional[Dict[str, Any]]:
        """Load a saga context from Redis."""
        if not self.redis_client:
            raise EventBusException("State store not connected")
        
        key = f"{self.key_prefix}{transaction_id}"
        value = await self.redis_client.get(key)
        
        if value:
            return json.loads(value)
        return None

    async def delete_context(self, transaction_id: str) -> bool:
        """Delete a saga context from Redis."""
        if not self.redis_client:
            raise EventBusException("State store not connected")
        
        key = f"{self.key_prefix}{transaction_id}"
        deleted = await self.redis_client.delete(key)
        return deleted > 0

    async def list_contexts(self, pattern: str = "*") -> List[str]:
        """List transaction IDs matching pattern."""
        if not self.redis_client:
            raise EventBusException("State store not connected")
        
        search_pattern = f"{self.key_prefix}{pattern}"
        keys = []
        
        async for key in self.redis_client.scan_iter(match=search_pattern):
            # Extract transaction ID from key
            transaction_id = key.decode('utf-8').replace(self.key_prefix, '')
            keys.append(transaction_id)
        
        return keys