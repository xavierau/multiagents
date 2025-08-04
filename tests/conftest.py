import pytest
import asyncio
from typing import AsyncGenerator
from unittest.mock import AsyncMock, MagicMock
import redis.asyncio as redis

from multiagents.event_bus import IEventBus
from multiagents.monitoring import ILogger, IEventMonitor


@pytest.fixture
def event_loop():
    """Create an event loop for each test."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def mock_redis():
    """Create a mock Redis client."""
    mock = AsyncMock()
    mock_pubsub = AsyncMock()
    mock_pubsub.close = AsyncMock()
    mock_pubsub.subscribe = AsyncMock()
    mock_pubsub.listen = AsyncMock()
    # pubsub() is not async, so use MagicMock instead of AsyncMock for the method itself
    mock.pubsub = MagicMock(return_value=mock_pubsub)
    mock.get = AsyncMock()
    mock.set = AsyncMock()
    mock.delete = AsyncMock()
    mock.publish = AsyncMock()
    mock.ping = AsyncMock()
    mock.close = AsyncMock()
    mock.aclose = AsyncMock()
    return mock


@pytest.fixture
def mock_logger():
    """Create a mock logger."""
    logger = MagicMock(spec=ILogger)
    logger.info = AsyncMock()
    logger.error = AsyncMock()
    logger.warning = AsyncMock()
    logger.debug = AsyncMock()
    logger.critical = AsyncMock()
    logger.log = AsyncMock()
    logger.close = AsyncMock()
    return logger


@pytest.fixture
def mock_event_monitor():
    """Create a mock event monitor."""
    monitor = MagicMock(spec=IEventMonitor)
    monitor.start = AsyncMock()
    monitor.stop = AsyncMock()
    monitor.track_event_dispatch = AsyncMock()
    monitor.track_event_pickup = AsyncMock()
    monitor.track_event_processing = AsyncMock()
    monitor.track_event_completion = AsyncMock()
    monitor.track_event_failure = AsyncMock()
    monitor._cleanup_old_traces = AsyncMock()
    monitor.get_event_trace = AsyncMock()
    monitor.get_transaction_events = AsyncMock()
    monitor.get_event_metrics = AsyncMock()
    return monitor


@pytest.fixture
def mock_worker_monitor():
    """Create a mock worker monitor."""
    from multiagents.monitoring import WorkerMonitor
    monitor = MagicMock(spec=WorkerMonitor)
    monitor.worker_registered = MagicMock()
    monitor.worker_unregistered = MagicMock()
    monitor.track_worker_processing_started = MagicMock()
    monitor.track_worker_processing_completed = MagicMock()
    monitor.track_worker_processing_failed = MagicMock()
    monitor.check_worker_health = MagicMock()
    monitor.get_worker_metrics = MagicMock()
    monitor.generate_report = MagicMock()
    return monitor


@pytest.fixture
def mock_event_bus():
    """Create a mock event bus."""
    bus = AsyncMock(spec=IEventBus)
    bus.publish = AsyncMock()
    bus.subscribe = AsyncMock()
    bus.unsubscribe = AsyncMock()
    bus.close = AsyncMock()
    return bus


@pytest.fixture
def sample_transaction_id():
    """Generate a sample transaction ID."""
    return "test-transaction-123"


@pytest.fixture
def sample_correlation_id():
    """Generate a sample correlation ID."""
    return "test-correlation-456"