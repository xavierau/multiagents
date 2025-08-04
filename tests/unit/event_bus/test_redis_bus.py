"""
Comprehensive unit tests for Redis Event Bus.
"""
import pytest
import asyncio
import json
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime, date
import uuid

from multiagents.event_bus.redis_bus import RedisEventBus, RedisStateStore, EventEncoder
from multiagents.event_bus.interface import EventHandler
from multiagents.core.exceptions import EventBusException
from multiagents.monitoring.interfaces import IEventMonitor, ILogger


class TestEventEncoder:
    """Test cases for EventEncoder."""
    
    def test_encode_datetime(self):
        """Test encoding datetime objects."""
        encoder = EventEncoder()
        dt = datetime(2024, 1, 1, 12, 0, 0)
        
        result = encoder.default(dt)
        
        assert result == "2024-01-01T12:00:00"
    
    def test_encode_date(self):
        """Test encoding date objects."""
        encoder = EventEncoder()
        d = date(2024, 1, 1)
        
        result = encoder.default(d)
        
        assert result == "2024-01-01"
    
    def test_encode_uuid(self):
        """Test encoding UUID objects."""
        encoder = EventEncoder()
        test_uuid = uuid.UUID('12345678-1234-5678-9012-123456789012')
        
        result = encoder.default(test_uuid)
        
        assert result == "12345678-1234-5678-9012-123456789012"
    
    def test_encode_unsupported_type(self):
        """Test encoding unsupported type falls back to parent."""
        encoder = EventEncoder()
        
        with pytest.raises(TypeError):
            encoder.default(object())
    
    def test_full_json_encoding(self):
        """Test full JSON encoding with custom objects."""
        test_data = {
            "timestamp": datetime(2024, 1, 1, 12, 0, 0),
            "id": uuid.UUID('12345678-1234-5678-9012-123456789012'),
            "date": date(2024, 1, 1),
            "message": "test"
        }
        
        result = json.dumps(test_data, cls=EventEncoder)
        decoded = json.loads(result)
        
        assert decoded["timestamp"] == "2024-01-01T12:00:00"
        assert decoded["id"] == "12345678-1234-5678-9012-123456789012"
        assert decoded["date"] == "2024-01-01"
        assert decoded["message"] == "test"


class TestRedisEventBusInitialization:
    """Test cases for RedisEventBus initialization."""
    
    def test_init_with_defaults(self):
        """Test initialization with default parameters."""
        bus = RedisEventBus()
        
        assert bus.redis_url == "redis://localhost:6379"
        assert bus.channel_prefix == "multiagent:"
        assert bus.redis_client is None
        assert bus.pubsub is None
        assert bus.handlers == {}
        assert bus._running is False
        assert bus._listener_task is None
    
    def test_init_with_custom_params(self):
        """Test initialization with custom parameters."""
        mock_monitor = Mock(spec=IEventMonitor)
        mock_logger = Mock(spec=ILogger)
        
        bus = RedisEventBus(
            redis_url="redis://example.com:6380",
            channel_prefix="test:",
            event_monitor=mock_monitor,
            logger=mock_logger
        )
        
        assert bus.redis_url == "redis://example.com:6380"
        assert bus.channel_prefix == "test:"
        assert bus.event_monitor == mock_monitor
        assert bus.monitoring_logger == mock_logger
    
    def test_init_auto_monitoring(self):
        """Test auto-initialization of monitoring components."""
        with patch('multiagents.monitoring.config.MonitoringConfig') as mock_config_class, \
             patch('multiagents.monitoring.event_monitor.EventMonitor') as mock_monitor_class, \
             patch('multiagents.monitoring.metrics_collector.MetricsCollector') as mock_metrics_class:
            
            mock_config_instance = Mock()
            mock_logger = Mock(spec=ILogger)
            mock_config_instance.create_logger.return_value = mock_logger
            mock_config_class.return_value = mock_config_instance
            
            mock_monitor_instance = Mock(spec=IEventMonitor)
            mock_monitor_class.return_value = mock_monitor_instance
            
            mock_metrics_instance = Mock()
            mock_metrics_class.return_value = mock_metrics_instance
            
            bus = RedisEventBus()
            
            mock_config_class.assert_called_once()
            mock_config_instance.create_logger.assert_called_once()
            mock_monitor_class.assert_called_once_with(logger=mock_logger)
            assert bus.event_monitor == mock_monitor_instance
            assert bus.monitoring_logger == mock_logger
            assert bus.metrics_collector == mock_metrics_instance


class TestRedisEventBusLifecycle:
    """Test cases for start/stop lifecycle."""
    
    @pytest.mark.asyncio
    @patch('multiagents.event_bus.redis_bus.redis.from_url')
    async def test_start_success(self, mock_from_url):
        """Test successful event bus start."""
        mock_redis = Mock()
        mock_pubsub = Mock()
        mock_redis.pubsub.return_value = mock_pubsub
        
        # Make from_url an async function that returns the mock redis client
        async def async_from_url(*args, **kwargs):
            return mock_redis
        mock_from_url.side_effect = async_from_url
        
        mock_monitor = Mock(spec=IEventMonitor)
        mock_monitor.start = AsyncMock()
        mock_logger = Mock(spec=ILogger)
        
        bus = RedisEventBus(event_monitor=mock_monitor, logger=mock_logger)
        
        # Ensure metrics_collector has the required async methods
        bus.metrics_collector.start = AsyncMock()
        bus.metrics_collector.stop = AsyncMock()
        
        await bus.start()
        
        assert bus.redis_client == mock_redis
        assert bus.pubsub == mock_pubsub
        assert bus._running is True
        mock_monitor.start.assert_called_once()
        bus.metrics_collector.start.assert_called_once()
    
    @pytest.mark.asyncio
    @patch('multiagents.event_bus.redis_bus.redis.from_url')
    async def test_start_failure(self, mock_from_url):
        """Test event bus start failure."""
        async def async_from_url_failure(*args, **kwargs):
            raise Exception("Connection failed")
        mock_from_url.side_effect = async_from_url_failure
        
        bus = RedisEventBus()
        
        with pytest.raises(EventBusException) as exc_info:
            await bus.start()
        
        assert "Failed to start event bus" in str(exc_info.value)
        assert bus._running is False
    
    @pytest.mark.asyncio
    async def test_stop_with_monitoring(self):
        """Test stopping event bus with monitoring components."""
        mock_monitor = Mock(spec=IEventMonitor)
        mock_monitor.stop = AsyncMock()
        mock_logger = Mock(spec=ILogger)
        
        bus = RedisEventBus(event_monitor=mock_monitor, logger=mock_logger)
        
        # Set up mocks for components that would be created during init
        mock_metrics = Mock()
        mock_metrics.stop = AsyncMock()
        bus.metrics_collector = mock_metrics
        
        # Create an actual async task for realistic testing
        async def dummy_task():
            await asyncio.sleep(10)
        
        mock_task = asyncio.create_task(dummy_task())
        mock_pubsub = Mock()
        mock_pubsub.close = AsyncMock()
        mock_redis = Mock()
        mock_redis.close = AsyncMock()
        
        bus._listener_task = mock_task
        bus.pubsub = mock_pubsub
        bus.redis_client = mock_redis
        bus._running = True
        
        await bus.stop()
        
        assert bus._running is False
        mock_monitor.stop.assert_called_once()
        mock_metrics.stop.assert_called_once()
        assert mock_task.cancelled()  # Check if task was cancelled
        mock_pubsub.close.assert_called_once()
        mock_redis.close.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_stop_with_cancelled_task(self):
        """Test stopping with cancelled listener task."""
        # Create an actual asyncio Task that we can cancel
        async def dummy_coroutine():
            await asyncio.sleep(10)  # This will be cancelled
        
        mock_task = asyncio.create_task(dummy_coroutine())
        
        bus = RedisEventBus()
        bus._listener_task = mock_task
        bus._running = True
        
        # Should handle CancelledError gracefully
        await bus.stop()
        
        assert bus._running is False
        assert mock_task.cancelled()  # Check if task was cancelled


class TestRedisEventBusPublish:
    """Test cases for event publishing."""
    
    @pytest.mark.asyncio
    async def test_publish_not_started(self):
        """Test publishing when bus not started."""
        bus = RedisEventBus()
        
        with pytest.raises(EventBusException) as exc_info:
            await bus.publish("test_event", {"data": "test"})
        
        assert "Event bus not started" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_publish_success_with_monitoring(self):
        """Test successful event publishing with monitoring."""
        mock_redis = AsyncMock()
        mock_monitor = AsyncMock(spec=IEventMonitor)
        mock_logger = AsyncMock(spec=ILogger)
        
        bus = RedisEventBus(event_monitor=mock_monitor, logger=mock_logger)
        bus.redis_client = mock_redis
        
        event_data = {
            "id": "event-123",
            "type": "test_event",
            "metadata": {
                "transaction_id": "txn-123",
                "correlation_id": "corr-123"
            },
            "data": "test"
        }
        
        await bus.publish("test_event", event_data)
        
        # Check Redis publish was called
        mock_redis.publish.assert_called_once()
        call_args = mock_redis.publish.call_args
        assert call_args[0][0] == "multiagent:test_event"
        
        # Check event monitoring
        mock_monitor.track_event_dispatch.assert_called_once_with(
            event_id="event-123",
            event_type="test_event",
            transaction_id="txn-123",
            correlation_id="corr-123",
            source="redis_event_bus",
            metadata={"channel": "multiagent:test_event", "event_type": "test_event"}
        )
        
        # Check monitoring logger
        mock_logger.debug.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_publish_without_monitoring_data(self):
        """Test publishing event without monitoring data."""
        mock_redis = AsyncMock()
        
        bus = RedisEventBus()
        bus.redis_client = mock_redis
        
        event_data = {"data": "test"}
        
        await bus.publish("test_event", event_data)
        
        # Should still publish successfully
        mock_redis.publish.assert_called_once()
        call_args = mock_redis.publish.call_args
        assert call_args[0][0] == "multiagent:test_event"
    
    @pytest.mark.asyncio
    async def test_publish_failure(self):
        """Test event publishing failure."""
        mock_redis = AsyncMock()
        mock_redis.publish.side_effect = Exception("Redis error")
        mock_logger = AsyncMock(spec=ILogger)
        
        bus = RedisEventBus(logger=mock_logger)
        bus.redis_client = mock_redis
        
        event_data = {"id": "event-123", "data": "test"}
        
        with pytest.raises(EventBusException) as exc_info:
            await bus.publish("test_event", event_data)
        
        assert "Failed to publish event" in str(exc_info.value)
        mock_logger.error.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_publish_with_custom_encoder(self):
        """Test publishing with custom encoder for datetime objects."""
        mock_redis = AsyncMock()
        
        bus = RedisEventBus()
        bus.redis_client = mock_redis
        
        event_data = {
            "timestamp": datetime(2024, 1, 1, 12, 0, 0),
            "id": uuid.UUID('12345678-1234-5678-9012-123456789012')
        }
        
        await bus.publish("test_event", event_data)
        
        # Check that data was serialized with custom encoder
        mock_redis.publish.assert_called_once()
        call_args = mock_redis.publish.call_args
        serialized_data = call_args[0][1]
        parsed_data = json.loads(serialized_data)
        
        assert parsed_data["timestamp"] == "2024-01-01T12:00:00"
        assert parsed_data["id"] == "12345678-1234-5678-9012-123456789012"


class TestRedisEventBusSubscription:
    """Test cases for event subscription."""
    
    @pytest.mark.asyncio
    async def test_subscribe_first_handler(self):
        """Test subscribing first handler for an event type."""
        mock_pubsub = AsyncMock()
        
        bus = RedisEventBus()
        bus.pubsub = mock_pubsub
        
        handler = AsyncMock()
        
        await bus.subscribe("test_event", handler)
        
        # Check handler was added
        assert "test_event" in bus.handlers
        assert handler in bus.handlers["test_event"]
        
        # Check Redis subscription
        mock_pubsub.subscribe.assert_called_once_with("multiagent:test_event")
    
    @pytest.mark.asyncio
    async def test_subscribe_additional_handler(self):
        """Test subscribing additional handler for existing event type."""
        mock_pubsub = AsyncMock()
        
        bus = RedisEventBus()
        bus.pubsub = mock_pubsub
        
        handler1 = AsyncMock()
        handler2 = AsyncMock()
        
        # Subscribe first handler
        await bus.subscribe("test_event", handler1)
        mock_pubsub.reset_mock()
        
        # Subscribe second handler
        await bus.subscribe("test_event", handler2)
        
        # Check both handlers are registered
        assert len(bus.handlers["test_event"]) == 2
        assert handler1 in bus.handlers["test_event"]
        assert handler2 in bus.handlers["test_event"]
        
        # Should not subscribe to Redis again
        mock_pubsub.subscribe.assert_not_called()
    
    @pytest.mark.asyncio
    @patch('asyncio.create_task')
    async def test_subscribe_starts_listener(self, mock_create_task):
        """Test that first subscription starts listener task."""
        mock_pubsub = AsyncMock()
        mock_task = AsyncMock()
        mock_create_task.return_value = mock_task
        
        bus = RedisEventBus()
        bus.pubsub = mock_pubsub
        
        handler = AsyncMock()
        
        await bus.subscribe("test_event", handler)
        
        # Check listener task was created
        mock_create_task.assert_called_once()
        assert bus._listener_task == mock_task
    
    @pytest.mark.asyncio
    async def test_unsubscribe_handler(self):
        """Test unsubscribing a handler."""
        mock_pubsub = AsyncMock()
        
        bus = RedisEventBus()
        bus.pubsub = mock_pubsub
        
        handler1 = AsyncMock()
        handler2 = AsyncMock()
        
        # Subscribe both handlers
        await bus.subscribe("test_event", handler1)
        await bus.subscribe("test_event", handler2)
        
        # Unsubscribe one handler
        await bus.unsubscribe("test_event", handler1)
        
        # Check handler was removed
        assert handler1 not in bus.handlers["test_event"]
        assert handler2 in bus.handlers["test_event"]
        
        # Should not unsubscribe from Redis yet
        mock_pubsub.unsubscribe.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_unsubscribe_last_handler(self):
        """Test unsubscribing the last handler for an event type."""
        mock_pubsub = AsyncMock()
        
        bus = RedisEventBus()
        bus.pubsub = mock_pubsub
        
        handler = AsyncMock()
        
        # Subscribe and then unsubscribe
        await bus.subscribe("test_event", handler)
        await bus.unsubscribe("test_event", handler)
        
        # Check event type was removed
        assert "test_event" not in bus.handlers
        
        # Check Redis unsubscription
        mock_pubsub.unsubscribe.assert_called_once_with("multiagent:test_event")
    
    @pytest.mark.asyncio
    async def test_unsubscribe_nonexistent_handler(self):
        """Test unsubscribing a handler that doesn't exist."""
        bus = RedisEventBus()
        
        handler = AsyncMock()
        
        # Should not raise error
        await bus.unsubscribe("nonexistent_event", handler)
        
        assert "nonexistent_event" not in bus.handlers


class TestRedisEventBusMessageHandling:
    """Test cases for message handling."""
    
    @pytest.mark.asyncio
    async def test_listen_for_messages_normal_operation(self):
        """Test normal message listening operation."""
        mock_pubsub = AsyncMock()
        
        # Simulate getting a message and then stopping
        message = {
            'type': 'message',
            'channel': b'multiagent:test_event',
            'data': b'{"id": "test", "data": "message"}'
        }
        mock_pubsub.get_message.side_effect = [message, asyncio.TimeoutError()]
        
        bus = RedisEventBus()
        bus.pubsub = mock_pubsub
        bus._running = True
        
        # Mock message handler
        with patch.object(bus, '_handle_message', new_callable=AsyncMock) as mock_handle:
            # Start listener and stop it after short time
            task = asyncio.create_task(bus._listen_for_messages())
            await asyncio.sleep(0.01)  # Let it process one message
            bus._running = False
            await task
            
            # Check message was handled
            mock_handle.assert_called_once_with(message)
    
    @pytest.mark.asyncio
    async def test_listen_for_messages_timeout_handling(self):
        """Test listener handles timeouts gracefully."""
        mock_pubsub = AsyncMock()
        
        # Create a side effect that raises TimeoutError a few times then stops
        call_count = 0
        async def timeout_side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count <= 2:  # Only raise TimeoutError twice
                raise asyncio.TimeoutError()
            else:
                # After 2 calls, just block (won't be reached since we stop the bus)
                await asyncio.sleep(10)
        
        mock_pubsub.get_message.side_effect = timeout_side_effect
        
        bus = RedisEventBus()
        bus.pubsub = mock_pubsub
        bus._running = True
        
        # Start listener and stop quickly to avoid infinite loop
        task = asyncio.create_task(bus._listen_for_messages())
        
        # Give it time to handle a couple timeouts
        await asyncio.sleep(0.1)
        
        # Stop the bus
        bus._running = False
        
        # Wait for task to complete
        try:
            await asyncio.wait_for(task, timeout=1.0)
        except asyncio.TimeoutError:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
        
        # Should complete without error
        assert True
    
    @pytest.mark.asyncio
    async def test_listen_for_messages_error_recovery(self):
        """Test listener recovers from errors."""
        mock_pubsub = AsyncMock()
        mock_pubsub.get_message.side_effect = Exception("Test error")
        
        bus = RedisEventBus()
        bus.pubsub = mock_pubsub
        bus._running = True
        
        # Start listener and stop quickly
        task = asyncio.create_task(bus._listen_for_messages())
        await asyncio.sleep(0.01)
        bus._running = False
        
        try:
            await asyncio.wait_for(task, timeout=1.0)
        except asyncio.TimeoutError:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
        
        # Should complete without raising error
        assert True
    
    @pytest.mark.asyncio
    async def test_handle_message_success(self):
        """Test successful message handling."""
        handler1 = AsyncMock()
        handler2 = AsyncMock()
        
        bus = RedisEventBus()
        bus.handlers["test_event"] = [handler1, handler2]
        
        message = {
            'channel': b'multiagent:test_event',
            'data': b'{"id": "test", "data": "message"}'
        }
        
        await bus._handle_message(message)
        
        # Check both handlers were called
        expected_data = {"id": "test", "data": "message"}
        handler1.assert_called_once_with(expected_data)
        handler2.assert_called_once_with(expected_data)
    
    @pytest.mark.asyncio
    async def test_handle_message_handler_error(self):
        """Test message handling when handler raises error."""
        handler1 = AsyncMock()
        handler2 = AsyncMock()
        handler1.side_effect = Exception("Handler error")
        
        bus = RedisEventBus()
        bus.handlers["test_event"] = [handler1, handler2]
        
        message = {
            'channel': b'multiagent:test_event',
            'data': b'{"id": "test", "data": "message"}'
        }
        
        # Should not raise error, should continue processing
        await bus._handle_message(message)
        
        # Second handler should still be called
        handler2.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_handle_message_no_handlers(self):
        """Test handling message with no registered handlers."""
        bus = RedisEventBus()
        
        message = {
            'channel': b'multiagent:unknown_event',
            'data': b'{"id": "test", "data": "message"}'
        }
        
        # Should not raise error
        await bus._handle_message(message)
    
    @pytest.mark.asyncio
    async def test_handle_message_invalid_json(self):
        """Test handling message with invalid JSON."""
        bus = RedisEventBus()
        
        message = {
            'channel': b'multiagent:test_event',
            'data': b'invalid json'
        }
        
        # Should not raise error
        await bus._handle_message(message)
    
    @pytest.mark.asyncio
    async def test_listen_for_messages_no_pubsub(self):
        """Test listener when pubsub is None."""
        bus = RedisEventBus()
        bus.pubsub = None
        
        # Should return immediately
        await bus._listen_for_messages()
        
        assert True  # Should complete without error


class TestRedisStateStore:
    """Test cases for RedisStateStore."""
    
    def test_init_with_defaults(self):
        """Test state store initialization with defaults."""
        store = RedisStateStore()
        
        assert store.redis_url == "redis://localhost:6379"
        assert store.key_prefix == "saga:"
        assert store.redis_client is None
    
    def test_init_with_custom_params(self):
        """Test state store initialization with custom parameters."""
        store = RedisStateStore(
            redis_url="redis://example.com:6380",
            key_prefix="test:"
        )
        
        assert store.redis_url == "redis://example.com:6380"
        assert store.key_prefix == "test:"
    
    @pytest.mark.asyncio
    @patch('multiagents.event_bus.redis_bus.redis.from_url')
    async def test_connect(self, mock_from_url):
        """Test connecting to Redis."""
        mock_redis = Mock()
        
        async def async_from_url(*args, **kwargs):
            return mock_redis
        mock_from_url.side_effect = async_from_url
        
        store = RedisStateStore()
        await store.connect()
        
        assert store.redis_client == mock_redis
        mock_from_url.assert_called_once_with("redis://localhost:6379")
    
    @pytest.mark.asyncio
    async def test_disconnect(self):
        """Test disconnecting from Redis."""
        mock_redis = AsyncMock()
        
        store = RedisStateStore()
        store.redis_client = mock_redis
        
        await store.disconnect()
        
        mock_redis.close.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_save_context(self):
        """Test saving saga context."""
        mock_redis = AsyncMock()
        mock_context = Mock()
        mock_context.transaction_id = "txn-123"
        mock_context.to_dict.return_value = {"id": "txn-123", "data": "test"}
        
        store = RedisStateStore()
        store.redis_client = mock_redis
        
        await store.save_context(mock_context)
        
        # Check Redis setex was called
        mock_redis.setex.assert_called_once()
        call_args = mock_redis.setex.call_args
        assert call_args[0][0] == "saga:txn-123"
        assert call_args[0][1] == 604800  # 7 days
        
        # Check serialized data
        serialized_data = call_args[0][2]
        parsed_data = json.loads(serialized_data)
        assert parsed_data == {"id": "txn-123", "data": "test"}
    
    @pytest.mark.asyncio
    async def test_save_context_not_connected(self):
        """Test saving context when not connected."""
        mock_context = Mock()
        
        store = RedisStateStore()
        
        with pytest.raises(EventBusException) as exc_info:
            await store.save_context(mock_context)
        
        assert "State store not connected" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_load_context_success(self):
        """Test loading existing context."""
        mock_redis = AsyncMock()
        mock_redis.get.return_value = b'{"id": "txn-123", "data": "test"}'
        
        store = RedisStateStore()
        store.redis_client = mock_redis
        
        result = await store.load_context("txn-123")
        
        assert result == {"id": "txn-123", "data": "test"}
        mock_redis.get.assert_called_once_with("saga:txn-123")
    
    @pytest.mark.asyncio
    async def test_load_context_not_found(self):
        """Test loading non-existent context."""
        mock_redis = AsyncMock()
        mock_redis.get.return_value = None
        
        store = RedisStateStore()
        store.redis_client = mock_redis
        
        result = await store.load_context("nonexistent")
        
        assert result is None
    
    @pytest.mark.asyncio
    async def test_load_context_not_connected(self):
        """Test loading context when not connected."""
        store = RedisStateStore()
        
        with pytest.raises(EventBusException) as exc_info:
            await store.load_context("txn-123")
        
        assert "State store not connected" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_delete_context_success(self):
        """Test deleting existing context."""
        mock_redis = AsyncMock()
        mock_redis.delete.return_value = 1
        
        store = RedisStateStore()
        store.redis_client = mock_redis
        
        result = await store.delete_context("txn-123")
        
        assert result is True
        mock_redis.delete.assert_called_once_with("saga:txn-123")
    
    @pytest.mark.asyncio
    async def test_delete_context_not_found(self):
        """Test deleting non-existent context."""
        mock_redis = AsyncMock()
        mock_redis.delete.return_value = 0
        
        store = RedisStateStore()
        store.redis_client = mock_redis
        
        result = await store.delete_context("nonexistent")
        
        assert result is False
    
    @pytest.mark.asyncio
    async def test_delete_context_not_connected(self):
        """Test deleting context when not connected."""
        store = RedisStateStore()
        
        with pytest.raises(EventBusException) as exc_info:
            await store.delete_context("txn-123")
        
        assert "State store not connected" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_list_contexts(self):
        """Test listing contexts."""
        mock_redis = AsyncMock()
        
        # Mock async iterator
        async def mock_scan_iter(match):
            keys = [b"saga:txn-1", b"saga:txn-2", b"saga:txn-3"]
            for key in keys:
                yield key
        
        mock_redis.scan_iter = mock_scan_iter
        
        store = RedisStateStore()
        store.redis_client = mock_redis
        
        result = await store.list_contexts()
        
        assert result == ["txn-1", "txn-2", "txn-3"]
        # scan_iter was called with the match pattern
        assert True
    
    @pytest.mark.asyncio
    async def test_list_contexts_with_pattern(self):
        """Test listing contexts with custom pattern."""
        mock_redis = AsyncMock()
        
        async def mock_scan_iter(match):
            keys = [b"saga:user-123", b"saga:user-456"]
            for key in keys:
                yield key
        
        mock_redis.scan_iter = mock_scan_iter
        
        store = RedisStateStore()
        store.redis_client = mock_redis
        
        result = await store.list_contexts("user-*")
        
        assert result == ["user-123", "user-456"]
        # scan_iter was called with the match pattern
        assert True
    
    @pytest.mark.asyncio
    async def test_list_contexts_not_connected(self):
        """Test listing contexts when not connected."""
        store = RedisStateStore()
        
        with pytest.raises(EventBusException) as exc_info:
            await store.list_contexts()
        
        assert "State store not connected" in str(exc_info.value)