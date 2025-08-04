# Performance & Scaling Guide

Comprehensive guide to optimizing and scaling the MultiAgents Framework for production workloads.

## Table of Contents

- [Performance Overview](#performance-overview)
- [Bottleneck Analysis](#bottleneck-analysis)
- [Event Bus Optimization](#event-bus-optimization)
- [Worker Performance](#worker-performance)
- [State Management](#state-management)
- [Memory Optimization](#memory-optimization)
- [Horizontal Scaling](#horizontal-scaling)
- [Load Testing](#load-testing)
- [Best Practices](#best-practices)

## Performance Overview

### Performance Characteristics

The MultiAgents Framework is designed for high-throughput, low-latency distributed processing:

```
┌─────────────────────────────────────────────────────────────────────┐
│                    PERFORMANCE ARCHITECTURE                        │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐ │
│  │    Event Bus    │    │   Orchestrator  │    │ Worker Manager  │ │
│  │                 │    │                 │    │                 │ │
│  │ • Redis Pub/Sub │    │ • Async state   │    │ • Concurrent    │ │
│  │ • Connection    │    │ • Non-blocking  │    │   execution     │ │
│  │   pooling       │    │ • Batch ops     │    │ • Load balance  │ │
│  │ • Pipelining    │    │ • Memory cache  │    │ • Health checks │ │
│  └─────────────────┘    └─────────────────┘    └─────────────────┘ │
│           │                       │                       │         │
│           └───────────────────────┼───────────────────────┘         │
│                                   │                                 │
│                    ┌─────────────────┐                              │
│                    │  PERFORMANCE    │                              │
│                    │   METRICS       │                              │
│                    │                 │                              │
│                    │ • Throughput    │                              │
│                    │ • Latency P95   │                              │
│                    │ • CPU/Memory    │                              │
│                    │ • Error rates   │                              │
│                    └─────────────────┘                              │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### Key Performance Metrics

- **Throughput**: Events/workflows processed per second
- **Latency**: End-to-end workflow completion time
- **Resource Utilization**: CPU, memory, network usage
- **Scalability**: Performance under increasing load
- **Reliability**: Error rates and system stability

## Bottleneck Analysis

### Identifying Bottlenecks

```python
import asyncio
import time
from typing import Dict, Any, List
from dataclasses import dataclass

@dataclass
class PerformanceMetrics:
    """Performance metrics for analysis."""
    component: str
    operation: str
    duration_ms: float
    throughput_per_sec: float
    resource_usage: Dict[str, float]
    timestamp: float

class PerformanceProfiler:
    """Profile framework performance to identify bottlenecks."""
    
    def __init__(self):
        self.metrics: List[PerformanceMetrics] = []
        self.active_operations: Dict[str, float] = {}
    
    def start_operation(self, component: str, operation: str) -> str:
        """Start timing an operation."""
        operation_id = f"{component}:{operation}:{time.time()}"
        self.active_operations[operation_id] = time.time()
        return operation_id
    
    def end_operation(self, operation_id: str, throughput: float = 0, 
                     resource_usage: Dict[str, float] = None):
        """End timing an operation and record metrics."""
        if operation_id not in self.active_operations:
            return
        
        start_time = self.active_operations.pop(operation_id)
        duration_ms = (time.time() - start_time) * 1000
        
        component, operation, _ = operation_id.split(":", 2)
        
        metrics = PerformanceMetrics(
            component=component,
            operation=operation,
            duration_ms=duration_ms,
            throughput_per_sec=throughput,
            resource_usage=resource_usage or {},
            timestamp=time.time()
        )
        
        self.metrics.append(metrics)
    
    def get_bottleneck_analysis(self, time_window_seconds: int = 300) -> Dict[str, Any]:
        """Analyze metrics to identify bottlenecks."""
        
        cutoff_time = time.time() - time_window_seconds
        recent_metrics = [m for m in self.metrics if m.timestamp >= cutoff_time]
        
        if not recent_metrics:
            return {"error": "No metrics available"}
        
        # Group by component and operation
        grouped_metrics = {}
        for metric in recent_metrics:
            key = f"{metric.component}:{metric.operation}"
            if key not in grouped_metrics:
                grouped_metrics[key] = []
            grouped_metrics[key].append(metric)
        
        # Analyze each group
        analysis = {}
        for key, metrics_list in grouped_metrics.items():
            durations = [m.duration_ms for m in metrics_list]
            throughputs = [m.throughput_per_sec for m in metrics_list if m.throughput_per_sec > 0]
            
            analysis[key] = {
                "count": len(metrics_list),
                "avg_duration_ms": sum(durations) / len(durations),
                "max_duration_ms": max(durations),
                "min_duration_ms": min(durations),
                "p95_duration_ms": sorted(durations)[int(len(durations) * 0.95)],
                "avg_throughput": sum(throughputs) / len(throughputs) if throughputs else 0,
                "bottleneck_score": self._calculate_bottleneck_score(metrics_list)
            }
        
        # Identify top bottlenecks
        bottlenecks = sorted(
            analysis.items(),
            key=lambda x: x[1]["bottleneck_score"],
            reverse=True
        )
        
        return {
            "analysis_period": f"{time_window_seconds} seconds",
            "total_operations": len(recent_metrics),
            "component_analysis": analysis,
            "top_bottlenecks": bottlenecks[:5],
            "recommendations": self._generate_recommendations(bottlenecks[:3])
        }
    
    def _calculate_bottleneck_score(self, metrics_list: List[PerformanceMetrics]) -> float:
        """Calculate bottleneck score for a set of metrics."""
        if not metrics_list:
            return 0
        
        durations = [m.duration_ms for m in metrics_list]
        avg_duration = sum(durations) / len(durations)
        max_duration = max(durations)
        
        # Score based on average duration, variance, and frequency
        frequency_score = len(metrics_list) / 100  # Higher frequency = higher score
        duration_score = avg_duration / 1000  # Higher average duration = higher score
        variance_score = (max_duration - min(durations)) / 1000  # Higher variance = higher score
        
        return frequency_score + duration_score + variance_score
    
    def _generate_recommendations(self, top_bottlenecks: List[tuple]) -> List[str]:
        """Generate performance recommendations based on bottlenecks."""
        recommendations = []
        
        for operation_key, metrics in top_bottlenecks:
            component, operation = operation_key.split(":", 1)
            
            if component == "event_bus":
                if metrics["avg_duration_ms"] > 100:
                    recommendations.append(
                        f"Event bus {operation} is slow ({metrics['avg_duration_ms']:.1f}ms avg). "
                        "Consider connection pooling or Redis clustering."
                    )
            
            elif component == "orchestrator":
                if metrics["avg_duration_ms"] > 50:
                    recommendations.append(
                        f"Orchestrator {operation} is slow ({metrics['avg_duration_ms']:.1f}ms avg). "
                        "Consider state caching or batch operations."
                    )
            
            elif component == "worker_manager":
                if metrics["avg_throughput"] < 10:
                    recommendations.append(
                        f"Worker manager throughput is low ({metrics['avg_throughput']:.1f}/sec). "
                        "Consider increasing worker concurrency."
                    )
        
        return recommendations

# Usage
profiler = PerformanceProfiler()

# In framework components
async def profile_event_bus_operation():
    """Example of profiling event bus operations."""
    op_id = profiler.start_operation("event_bus", "publish_event")
    
    # Simulate event bus operation
    await asyncio.sleep(0.05)  # 50ms operation
    
    profiler.end_operation(op_id, throughput=20.0)

# Get analysis
analysis = profiler.get_bottleneck_analysis()
print("Performance Analysis:", analysis)
```

## Event Bus Optimization

### Redis Connection Optimization

```python
import redis.asyncio as redis
from redis.connection import ConnectionPool
import asyncio

class OptimizedRedisEventBus:
    """Optimized Redis event bus with connection pooling and pipelining."""
    
    def __init__(self, redis_url: str = "redis://localhost:6379", 
                 max_connections: int = 50, 
                 min_connections: int = 5):
        
        # Create connection pool
        self.connection_pool = ConnectionPool.from_url(
            redis_url,
            max_connections=max_connections,
            retry_on_timeout=True,
            socket_keepalive=True,
            socket_keepalive_options={},
            health_check_interval=30
        )
        
        self.redis = redis.Redis(connection_pool=self.connection_pool)
        self.batch_queue = asyncio.Queue(maxsize=1000)
        self.batch_size = 50
        self.batch_timeout = 0.01  # 10ms
        self.stats = {
            "events_published": 0,
            "batches_sent": 0,
            "avg_batch_size": 0
        }
    
    async def start(self):
        """Start the event bus with batch processing."""
        # Start batch processor
        asyncio.create_task(self._batch_processor())
    
    async def publish_event(self, channel: str, event_data: dict):
        """Publish event with batching."""
        try:
            await self.batch_queue.put((channel, event_data), timeout=0.001)
        except asyncio.TimeoutError:
            # Queue full, publish directly
            await self._publish_single(channel, event_data)
    
    async def _batch_processor(self):
        """Process events in batches for better performance."""
        batch = []
        last_send = time.time()
        
        while True:
            try:
                # Wait for events with timeout
                try:
                    channel, event_data = await asyncio.wait_for(
                        self.batch_queue.get(), 
                        timeout=self.batch_timeout
                    )
                    batch.append((channel, event_data))
                except asyncio.TimeoutError:
                    pass
                
                # Send batch if conditions met
                should_send = (
                    len(batch) >= self.batch_size or
                    (batch and time.time() - last_send > self.batch_timeout)
                )
                
                if should_send and batch:
                    await self._send_batch(batch)
                    batch.clear()
                    last_send = time.time()
                
            except Exception as e:
                print(f"Batch processor error: {e}")
                await asyncio.sleep(0.1)
    
    async def _send_batch(self, batch: List[tuple]):
        """Send a batch of events using Redis pipeline."""
        if not batch:
            return
        
        try:
            # Use pipeline for batch operations
            pipeline = self.redis.pipeline()
            
            for channel, event_data in batch:
                event_json = json.dumps(event_data)
                pipeline.publish(channel, event_json)
            
            # Execute all operations in one round trip
            await pipeline.execute()
            
            # Update stats
            self.stats["events_published"] += len(batch)
            self.stats["batches_sent"] += 1
            self.stats["avg_batch_size"] = (
                self.stats["events_published"] / self.stats["batches_sent"]
            )
            
        except Exception as e:
            print(f"Batch send error: {e}")
            # Fallback to individual sends
            for channel, event_data in batch:
                await self._publish_single(channel, event_data)
    
    async def _publish_single(self, channel: str, event_data: dict):
        """Publish single event as fallback."""
        try:
            event_json = json.dumps(event_data)
            await self.redis.publish(channel, event_json)
            self.stats["events_published"] += 1
        except Exception as e:
            print(f"Single publish error: {e}")
    
    async def subscribe_with_backpressure(self, channels: List[str], 
                                        handler: callable, 
                                        max_queue_size: int = 1000):
        """Subscribe with backpressure handling."""
        
        pubsub = self.redis.pubsub()
        await pubsub.subscribe(*channels)
        
        # Queue for message buffering
        message_queue = asyncio.Queue(maxsize=max_queue_size)
        
        # Start message processor
        asyncio.create_task(self._process_messages(message_queue, handler))
        
        try:
            async for message in pubsub.listen():
                if message["type"] == "message":
                    try:
                        # Non-blocking queue put with backpressure
                        message_queue.put_nowait(message)
                    except asyncio.QueueFull:
                        # Drop oldest message if queue is full
                        try:
                            message_queue.get_nowait()
                            message_queue.put_nowait(message)
                        except asyncio.QueueEmpty:
                            pass
        finally:
            await pubsub.unsubscribe()
    
    async def _process_messages(self, message_queue: asyncio.Queue, handler: callable):
        """Process messages from queue with concurrency control."""
        
        # Semaphore to limit concurrent processing
        semaphore = asyncio.Semaphore(20)  # Max 20 concurrent handlers
        
        while True:
            try:
                message = await message_queue.get()
                
                # Process message with concurrency limit
                asyncio.create_task(
                    self._handle_message_with_semaphore(message, handler, semaphore)
                )
                
            except Exception as e:
                print(f"Message processing error: {e}")
    
    async def _handle_message_with_semaphore(self, message, handler, semaphore):
        """Handle message with semaphore for concurrency control."""
        async with semaphore:
            try:
                event_data = json.loads(message["data"])
                await handler(event_data)
            except Exception as e:
                print(f"Handler error: {e}")
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get event bus performance statistics."""
        return {
            **self.stats,
            "connection_pool_stats": {
                "created_connections": self.connection_pool.created_connections,
                "available_connections": len(self.connection_pool._available_connections),
                "in_use_connections": len(self.connection_pool._in_use_connections)
            }
        }
```

### Event Serialization Optimization

```python
import orjson  # Fast JSON library
import msgpack  # Binary serialization
import pickle
import gzip
from typing import Any

class OptimizedEventSerializer:
    """Optimized event serialization with multiple formats."""
    
    def __init__(self, format: str = "orjson", compression: bool = False):
        self.format = format
        self.compression = compression
        self.stats = {
            "serializations": 0,
            "deserializations": 0,
            "total_bytes": 0,
            "avg_size": 0
        }
    
    def serialize(self, data: Any) -> bytes:
        """Serialize data with chosen format and optional compression."""
        
        if self.format == "orjson":
            serialized = orjson.dumps(data)
        elif self.format == "msgpack":
            serialized = msgpack.packb(data, use_bin_type=True)
        elif self.format == "pickle":
            serialized = pickle.dumps(data, protocol=pickle.HIGHEST_PROTOCOL)
        else:  # fallback to standard json
            serialized = json.dumps(data).encode('utf-8')
        
        if self.compression:
            serialized = gzip.compress(serialized)
        
        # Update stats
        self.stats["serializations"] += 1
        self.stats["total_bytes"] += len(serialized)
        self.stats["avg_size"] = self.stats["total_bytes"] / self.stats["serializations"]
        
        return serialized
    
    def deserialize(self, data: bytes) -> Any:
        """Deserialize data."""
        
        if self.compression:
            data = gzip.decompress(data)
        
        if self.format == "orjson":
            result = orjson.loads(data)
        elif self.format == "msgpack":
            result = msgpack.unpackb(data, raw=False)
        elif self.format == "pickle":
            result = pickle.loads(data)
        else:  # fallback to standard json
            result = json.loads(data.decode('utf-8'))
        
        self.stats["deserializations"] += 1
        return result
    
    def benchmark_formats(self, test_data: Any, iterations: int = 1000) -> Dict[str, Any]:
        """Benchmark different serialization formats."""
        
        formats = ["json", "orjson", "msgpack", "pickle"]
        results = {}
        
        for fmt in formats:
            # Test serialization
            serializer = OptimizedEventSerializer(format=fmt, compression=False)
            
            start_time = time.time()
            total_size = 0
            
            for _ in range(iterations):
                serialized = serializer.serialize(test_data)
                total_size += len(serialized)
                deserialized = serializer.deserialize(serialized)
            
            duration = time.time() - start_time
            
            results[fmt] = {
                "duration_ms": duration * 1000,
                "ops_per_second": iterations / duration,
                "avg_size_bytes": total_size / iterations,
                "throughput_mb_per_sec": (total_size / (1024 * 1024)) / duration
            }
        
        return results
```

## Worker Performance

### Async Worker Optimization

```python
import asyncio
from typing import Dict, Any, List, Callable
from concurrent.futures import ThreadPoolExecutor
import psutil

class OptimizedWorkerManager:
    """Optimized worker manager with performance enhancements."""
    
    def __init__(self, max_concurrent_workers: int = None, 
                 thread_pool_size: int = None):
        
        # Auto-detect optimal concurrency
        cpu_count = psutil.cpu_count()
        self.max_concurrent_workers = max_concurrent_workers or (cpu_count * 4)
        self.thread_pool_size = thread_pool_size or cpu_count
        
        # Create semaphore for concurrency control
        self.worker_semaphore = asyncio.Semaphore(self.max_concurrent_workers)
        
        # Thread pool for CPU-bound tasks
        self.thread_pool = ThreadPoolExecutor(max_workers=self.thread_pool_size)
        
        # Worker registry and performance tracking
        self.workers: Dict[str, Callable] = {}
        self.worker_stats: Dict[str, Dict] = {}
        
        # Circuit breaker for failing workers
        self.circuit_breakers: Dict[str, Dict] = {}
    
    def register_worker(self, name: str, worker_func: Callable, 
                       worker_type: str = "async"):
        """Register worker with type specification."""
        
        self.workers[name] = {
            "function": worker_func,
            "type": worker_type
        }
        
        self.worker_stats[name] = {
            "executions": 0,
            "successes": 0,
            "failures": 0,
            "total_duration": 0.0,
            "avg_duration": 0.0
        }
        
        self.circuit_breakers[name] = {
            "state": "closed",  # closed, open, half-open
            "failure_count": 0,
            "last_failure": None,
            "failure_threshold": 5,
            "timeout_seconds": 60
        }
    
    async def execute_worker(self, worker_name: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute worker with performance optimizations."""
        
        # Check circuit breaker
        if not self._check_circuit_breaker(worker_name):
            return {
                "error": f"Worker {worker_name} circuit breaker is open",
                "circuit_breaker_state": "open"
            }
        
        # Use semaphore for concurrency control
        async with self.worker_semaphore:
            start_time = time.time()
            
            try:
                worker_info = self.workers[worker_name]
                worker_func = worker_info["function"]
                worker_type = worker_info["type"]
                
                # Execute based on worker type
                if worker_type == "async":
                    result = await worker_func(context)
                elif worker_type == "sync":
                    # Run sync worker in thread pool
                    loop = asyncio.get_event_loop()
                    result = await loop.run_in_executor(
                        self.thread_pool, worker_func, context
                    )
                elif worker_type == "cpu_bound":
                    # Use thread pool for CPU-bound tasks
                    loop = asyncio.get_event_loop()
                    result = await loop.run_in_executor(
                        self.thread_pool, worker_func, context
                    )
                else:
                    result = await worker_func(context)
                
                # Record success
                duration = time.time() - start_time
                self._record_worker_success(worker_name, duration)
                
                return result
                
            except Exception as e:
                # Record failure
                duration = time.time() - start_time
                self._record_worker_failure(worker_name, duration, str(e))
                
                return {
                    "error": str(e),
                    "worker_name": worker_name,
                    "execution_time": duration
                }
    
    def _check_circuit_breaker(self, worker_name: str) -> bool:
        """Check if circuit breaker allows execution."""
        
        cb = self.circuit_breakers[worker_name]
        
        if cb["state"] == "closed":
            return True
        
        elif cb["state"] == "open":
            # Check if timeout period has passed
            if cb["last_failure"]:
                time_since_failure = time.time() - cb["last_failure"]
                if time_since_failure > cb["timeout_seconds"]:
                    cb["state"] = "half-open"
                    return True
            return False
        
        elif cb["state"] == "half-open":
            # Allow one attempt
            return True
        
        return False
    
    def _record_worker_success(self, worker_name: str, duration: float):
        """Record successful worker execution."""
        
        stats = self.worker_stats[worker_name]
        stats["executions"] += 1
        stats["successes"] += 1
        stats["total_duration"] += duration
        stats["avg_duration"] = stats["total_duration"] / stats["executions"]
        
        # Reset circuit breaker on success
        cb = self.circuit_breakers[worker_name]
        if cb["state"] == "half-open":
            cb["state"] = "closed"
            cb["failure_count"] = 0
    
    def _record_worker_failure(self, worker_name: str, duration: float, error: str):
        """Record failed worker execution."""
        
        stats = self.worker_stats[worker_name]
        stats["executions"] += 1
        stats["failures"] += 1
        stats["total_duration"] += duration
        stats["avg_duration"] = stats["total_duration"] / stats["executions"]
        
        # Update circuit breaker
        cb = self.circuit_breakers[worker_name]
        cb["failure_count"] += 1
        cb["last_failure"] = time.time()
        
        if cb["failure_count"] >= cb["failure_threshold"]:
            cb["state"] = "open"
    
    async def execute_workers_batch(self, worker_requests: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Execute multiple workers concurrently."""
        
        tasks = []
        for request in worker_requests:
            task = self.execute_worker(
                request["worker_name"],
                request["context"]
            )
            tasks.append(task)
        
        # Execute all workers concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                processed_results.append({
                    "error": str(result),
                    "worker_name": worker_requests[i]["worker_name"],
                    "exception_type": type(result).__name__
                })
            else:
                processed_results.append(result)
        
        return processed_results
    
    def get_performance_report(self) -> Dict[str, Any]:
        """Get comprehensive performance report."""
        
        total_executions = sum(stats["executions"] for stats in self.worker_stats.values())
        total_successes = sum(stats["successes"] for stats in self.worker_stats.values())
        
        return {
            "summary": {
                "total_workers": len(self.workers),
                "total_executions": total_executions,
                "overall_success_rate": total_successes / total_executions if total_executions > 0 else 0,
                "max_concurrent_workers": self.max_concurrent_workers,
                "thread_pool_size": self.thread_pool_size
            },
            "worker_stats": self.worker_stats,
            "circuit_breakers": {
                name: {
                    "state": cb["state"],
                    "failure_count": cb["failure_count"]
                }
                for name, cb in self.circuit_breakers.items()
            }
        }
```

## State Management

### State Store Optimization

```python
import asyncio
from typing import Optional, Dict, Any
import msgpack
import time

class OptimizedStateStore:
    """Optimized state store with caching and batch operations."""
    
    def __init__(self, redis_client, cache_size: int = 1000, 
                 cache_ttl: int = 300):
        self.redis = redis_client
        self.cache_size = cache_size
        self.cache_ttl = cache_ttl
        
        # In-memory cache for frequently accessed state
        self.cache: Dict[str, Dict] = {}
        self.cache_timestamps: Dict[str, float] = {}
        
        # Batch operations
        self.pending_writes: Dict[str, Any] = {}
        self.batch_write_interval = 0.1  # 100ms
        
        # Performance metrics
        self.metrics = {
            "cache_hits": 0,
            "cache_misses": 0,
            "batch_writes": 0,
            "single_writes": 0
        }
        
        # Start batch writer
        asyncio.create_task(self._batch_writer())
    
    async def save_context(self, transaction_id: str, context: Dict[str, Any], 
                          batch: bool = True):
        """Save context with optional batching."""
        
        if batch:
            # Add to batch queue
            self.pending_writes[transaction_id] = {
                "context": context,
                "timestamp": time.time()
            }
        else:
            # Write immediately
            await self._write_context_to_redis(transaction_id, context)
            self.metrics["single_writes"] += 1
        
        # Update in-memory cache
        self._update_cache(transaction_id, context)
    
    async def load_context(self, transaction_id: str) -> Optional[Dict[str, Any]]:
        """Load context with caching."""
        
        # Check cache first
        cached_context = self._get_from_cache(transaction_id)
        if cached_context is not None:
            self.metrics["cache_hits"] += 1
            return cached_context
        
        self.metrics["cache_misses"] += 1
        
        # Load from Redis
        context = await self._load_context_from_redis(transaction_id)
        
        if context:
            self._update_cache(transaction_id, context)
        
        return context
    
    async def _batch_writer(self):
        """Background task to write pending contexts in batches."""
        
        while True:
            try:
                await asyncio.sleep(self.batch_write_interval)
                
                if not self.pending_writes:
                    continue
                
                # Get batch to write
                batch = dict(self.pending_writes)
                self.pending_writes.clear()
                
                # Write batch to Redis using pipeline
                if batch:
                    await self._write_batch_to_redis(batch)
                    self.metrics["batch_writes"] += 1
                
            except Exception as e:
                print(f"Batch writer error: {e}")
    
    async def _write_batch_to_redis(self, batch: Dict[str, Any]):
        """Write multiple contexts to Redis using pipeline."""
        
        pipeline = self.redis.pipeline()
        
        for transaction_id, data in batch.items():
            context = data["context"]
            
            # Use msgpack for binary serialization (faster than JSON)
            serialized = msgpack.packb(context, use_bin_type=True)
            
            # Set with TTL
            pipeline.setex(
                f"context:{transaction_id}",
                3600,  # 1 hour TTL
                serialized
            )
        
        await pipeline.execute()
    
    async def _write_context_to_redis(self, transaction_id: str, context: Dict[str, Any]):
        """Write single context to Redis."""
        
        serialized = msgpack.packb(context, use_bin_type=True)
        await self.redis.setex(
            f"context:{transaction_id}",
            3600,
            serialized
        )
    
    async def _load_context_from_redis(self, transaction_id: str) -> Optional[Dict[str, Any]]:
        """Load context from Redis."""
        
        serialized = await self.redis.get(f"context:{transaction_id}")
        
        if serialized:
            return msgpack.unpackb(serialized, raw=False)
        
        return None
    
    def _update_cache(self, transaction_id: str, context: Dict[str, Any]):
        """Update in-memory cache."""
        
        # Evict old entries if cache is full
        if len(self.cache) >= self.cache_size:
            self._evict_oldest_cache_entry()
        
        self.cache[transaction_id] = context
        self.cache_timestamps[transaction_id] = time.time()
    
    def _get_from_cache(self, transaction_id: str) -> Optional[Dict[str, Any]]:
        """Get context from cache if not expired."""
        
        if transaction_id not in self.cache:
            return None
        
        # Check TTL
        timestamp = self.cache_timestamps.get(transaction_id, 0)
        if time.time() - timestamp > self.cache_ttl:
            # Expired
            del self.cache[transaction_id]
            del self.cache_timestamps[transaction_id]
            return None
        
        return self.cache[transaction_id]
    
    def _evict_oldest_cache_entry(self):
        """Evict the oldest cache entry."""
        
        if not self.cache_timestamps:
            return
        
        oldest_key = min(self.cache_timestamps.keys(), 
                        key=lambda k: self.cache_timestamps[k])
        
        del self.cache[oldest_key]
        del self.cache_timestamps[oldest_key]
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache performance statistics."""
        
        total_requests = self.metrics["cache_hits"] + self.metrics["cache_misses"]
        hit_rate = self.metrics["cache_hits"] / total_requests if total_requests > 0 else 0
        
        return {
            "cache_size": len(self.cache),
            "max_cache_size": self.cache_size,
            "hit_rate": hit_rate,
            "total_requests": total_requests,
            **self.metrics
        }
```

## Memory Optimization

### Memory Usage Monitoring

```python
import psutil
import gc
import sys
from typing import Dict, Any

class MemoryOptimizer:
    """Monitor and optimize memory usage."""
    
    def __init__(self, gc_threshold: float = 0.8, warning_threshold: float = 0.7):
        self.gc_threshold = gc_threshold  # Trigger GC at 80% memory
        self.warning_threshold = warning_threshold  # Warning at 70%
        self.process = psutil.Process()
        
        self.memory_stats = {
            "peak_memory_mb": 0,
            "gc_collections": 0,
            "memory_warnings": 0
        }
    
    def get_memory_usage(self) -> Dict[str, Any]:
        """Get current memory usage statistics."""
        
        # Process memory info
        memory_info = self.process.memory_info()
        memory_percent = self.process.memory_percent()
        
        # System memory info
        system_memory = psutil.virtual_memory()
        
        # Python object stats
        object_stats = self._get_object_stats()
        
        current_memory_mb = memory_info.rss / (1024 * 1024)
        
        # Update peak memory
        if current_memory_mb > self.memory_stats["peak_memory_mb"]:
            self.memory_stats["peak_memory_mb"] = current_memory_mb
        
        return {
            "process": {
                "rss_mb": current_memory_mb,
                "vms_mb": memory_info.vms / (1024 * 1024),
                "percent": memory_percent,
                "peak_mb": self.memory_stats["peak_memory_mb"]
            },
            "system": {
                "total_mb": system_memory.total / (1024 * 1024),
                "available_mb": system_memory.available / (1024 * 1024),
                "percent": system_memory.percent
            },
            "python_objects": object_stats,
            "gc_stats": {
                "collections": self.memory_stats["gc_collections"],
                "thresholds": gc.get_threshold(),
                "counts": gc.get_count()
            }
        }
    
    def _get_object_stats(self) -> Dict[str, int]:
        """Get Python object statistics."""
        
        object_count = {}
        
        for obj in gc.get_objects():
            obj_type = type(obj).__name__
            object_count[obj_type] = object_count.get(obj_type, 0) + 1
        
        # Get top 10 object types
        top_objects = dict(sorted(object_count.items(), 
                                key=lambda x: x[1], reverse=True)[:10])
        
        return {
            "total_objects": len(gc.get_objects()),
            "top_types": top_objects
        }
    
    async def monitor_memory(self):
        """Monitor memory usage and trigger cleanup if needed."""
        
        memory_info = self.get_memory_usage()
        memory_percent = memory_info["process"]["percent"]
        
        if memory_percent > self.gc_threshold:
            # Trigger garbage collection
            collected = gc.collect()
            self.memory_stats["gc_collections"] += 1
            
            print(f"Memory usage high ({memory_percent:.1f}%), "
                  f"triggered GC and collected {collected} objects")
        
        elif memory_percent > self.warning_threshold:
            self.memory_stats["memory_warnings"] += 1
            print(f"Memory usage warning: {memory_percent:.1f}%")
        
        return memory_info
    
    def optimize_memory(self):
        """Perform memory optimization."""
        
        # Force garbage collection
        collected = gc.collect()
        
        # Optimize dictionary memory usage
        self._optimize_dictionaries()
        
        print(f"Memory optimization completed, collected {collected} objects")
        
        return self.get_memory_usage()
    
    def _optimize_dictionaries(self):
        """Optimize memory usage of dictionaries."""
        
        # This is a placeholder for dictionary optimization
        # In practice, you might implement specific optimizations
        # based on your application's data structures
        pass

# Usage
memory_optimizer = MemoryOptimizer()

async def memory_monitoring_loop():
    """Background memory monitoring."""
    while True:
        await memory_optimizer.monitor_memory()
        await asyncio.sleep(30)  # Check every 30 seconds

# Start monitoring
asyncio.create_task(memory_monitoring_loop())
```

## Horizontal Scaling

### Load Balancing Strategies

```python
import random
import hashlib
from typing import List, Dict, Any

class LoadBalancer:
    """Load balancer for distributing workflows across multiple instances."""
    
    def __init__(self, instances: List[str], strategy: str = "round_robin"):
        self.instances = instances
        self.strategy = strategy
        self.current_index = 0
        self.instance_weights = {instance: 1.0 for instance in instances}
        self.instance_health = {instance: True for instance in instances}
    
    def select_instance(self, workflow_id: str = None, 
                       context: Dict[str, Any] = None) -> str:
        """Select an instance based on the load balancing strategy."""
        
        healthy_instances = [
            instance for instance in self.instances 
            if self.instance_health[instance]
        ]
        
        if not healthy_instances:
            raise Exception("No healthy instances available")
        
        if self.strategy == "round_robin":
            return self._round_robin_select(healthy_instances)
        
        elif self.strategy == "random":
            return random.choice(healthy_instances)
        
        elif self.strategy == "hash":
            return self._hash_select(healthy_instances, workflow_id or "default")
        
        elif self.strategy == "weighted":
            return self._weighted_select(healthy_instances)
        
        else:
            return healthy_instances[0]
    
    def _round_robin_select(self, instances: List[str]) -> str:
        """Round-robin selection."""
        instance = instances[self.current_index % len(instances)]
        self.current_index += 1
        return instance
    
    def _hash_select(self, instances: List[str], key: str) -> str:
        """Consistent hash-based selection."""
        hash_value = int(hashlib.md5(key.encode()).hexdigest(), 16)
        return instances[hash_value % len(instances)]
    
    def _weighted_select(self, instances: List[str]) -> str:
        """Weighted random selection."""
        weights = [self.instance_weights[instance] for instance in instances]
        total_weight = sum(weights)
        
        if total_weight == 0:
            return random.choice(instances)
        
        # Weighted random selection
        r = random.uniform(0, total_weight)
        cumulative_weight = 0
        
        for i, instance in enumerate(instances):
            cumulative_weight += weights[i]
            if r <= cumulative_weight:
                return instance
        
        return instances[-1]
    
    def update_instance_weight(self, instance: str, weight: float):
        """Update instance weight for load balancing."""
        if instance in self.instance_weights:
            self.instance_weights[instance] = weight
    
    def mark_instance_unhealthy(self, instance: str):
        """Mark instance as unhealthy."""
        if instance in self.instance_health:
            self.instance_health[instance] = False
    
    def mark_instance_healthy(self, instance: str):
        """Mark instance as healthy."""
        if instance in self.instance_health:
            self.instance_health[instance] = True

class ClusterManager:
    """Manage a cluster of MultiAgents Framework instances."""
    
    def __init__(self, cluster_config: Dict[str, Any]):
        self.instances = cluster_config.get("instances", [])
        self.load_balancer = LoadBalancer(
            self.instances, 
            cluster_config.get("load_balancing_strategy", "round_robin")
        )
        
        self.health_check_interval = cluster_config.get("health_check_interval", 30)
        self.cluster_stats = {
            "total_requests": 0,
            "requests_per_instance": {instance: 0 for instance in self.instances}
        }
    
    async def execute_workflow_on_cluster(self, workflow_id: str, 
                                        context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute workflow on the cluster."""
        
        # Select instance
        instance = self.load_balancer.select_instance(workflow_id, context)
        
        try:
            # Execute on selected instance
            result = await self._execute_on_instance(instance, workflow_id, context)
            
            # Update stats
            self.cluster_stats["total_requests"] += 1
            self.cluster_stats["requests_per_instance"][instance] += 1
            
            return result
            
        except Exception as e:
            # Mark instance as unhealthy and retry
            self.load_balancer.mark_instance_unhealthy(instance)
            
            # Retry on another instance
            retry_instance = self.load_balancer.select_instance(workflow_id, context)
            return await self._execute_on_instance(retry_instance, workflow_id, context)
    
    async def _execute_on_instance(self, instance: str, workflow_id: str, 
                                 context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute workflow on specific instance."""
        
        # This would typically make an HTTP request to the instance
        # For this example, we'll simulate it
        await asyncio.sleep(0.1)  # Simulate network latency
        
        return {
            "instance": instance,
            "workflow_id": workflow_id,
            "status": "completed",
            "result": "simulated_result"
        }
    
    async def health_check_loop(self):
        """Continuously check instance health."""
        
        while True:
            for instance in self.instances:
                is_healthy = await self._check_instance_health(instance)
                
                if is_healthy:
                    self.load_balancer.mark_instance_healthy(instance)
                else:
                    self.load_balancer.mark_instance_unhealthy(instance)
            
            await asyncio.sleep(self.health_check_interval)
    
    async def _check_instance_health(self, instance: str) -> bool:
        """Check if instance is healthy."""
        
        try:
            # Simulate health check (would be HTTP request in practice)
            await asyncio.sleep(0.01)
            
            # Simulate occasional health check failures
            return random.random() > 0.05  # 5% failure rate
            
        except Exception:
            return False
    
    def get_cluster_stats(self) -> Dict[str, Any]:
        """Get cluster performance statistics."""
        
        healthy_instances = [
            instance for instance in self.instances
            if self.load_balancer.instance_health[instance]
        ]
        
        return {
            "total_instances": len(self.instances),
            "healthy_instances": len(healthy_instances),
            "total_requests": self.cluster_stats["total_requests"],
            "requests_per_instance": self.cluster_stats["requests_per_instance"],
            "load_balancing_strategy": self.load_balancer.strategy,
            "instance_health": self.load_balancer.instance_health
        }
```

## Load Testing

### Performance Testing Framework

```python
import asyncio
import time
import statistics
from typing import List, Dict, Any, Callable
from dataclasses import dataclass

@dataclass
class LoadTestResult:
    """Result of a load test."""
    total_requests: int
    successful_requests: int
    failed_requests: int
    duration_seconds: float
    requests_per_second: float
    avg_response_time: float
    p95_response_time: float
    p99_response_time: float
    error_rate: float
    errors: List[str]

class LoadTester:
    """Load testing framework for the MultiAgents Framework."""
    
    def __init__(self):
        self.results: List[LoadTestResult] = []
    
    async def run_load_test(self, 
                          target_function: Callable,
                          request_generator: Callable,
                          duration_seconds: int = 60,
                          requests_per_second: int = 10,
                          max_concurrent: int = 100) -> LoadTestResult:
        """Run a load test against the target function."""
        
        print(f"Starting load test: {requests_per_second} RPS for {duration_seconds}s")
        
        # Semaphore to control concurrency
        semaphore = asyncio.Semaphore(max_concurrent)
        
        # Stats tracking
        start_time = time.time()
        end_time = start_time + duration_seconds
        
        request_count = 0
        successful_requests = 0
        failed_requests = 0
        response_times = []
        errors = []
        
        # Request generation loop
        async def generate_requests():
            nonlocal request_count
            
            while time.time() < end_time:
                # Generate request
                request_data = request_generator()
                
                # Create task with semaphore
                task = asyncio.create_task(
                    self._execute_request_with_semaphore(
                        target_function, request_data, semaphore
                    )
                )
                
                request_count += 1
                
                # Control rate
                await asyncio.sleep(1.0 / requests_per_second)
        
        # Start request generation
        generator_task = asyncio.create_task(generate_requests())
        
        # Collect all pending tasks
        all_tasks = []
        
        while time.time() < end_time:
            await asyncio.sleep(0.1)
            
            # Get current tasks
            current_tasks = [task for task in asyncio.all_tasks() 
                           if not task.done() and task != asyncio.current_task()]
            all_tasks.extend(current_tasks)
        
        # Wait for all requests to complete
        if all_tasks:
            results = await asyncio.gather(*all_tasks, return_exceptions=True)
            
            # Process results
            for result in results:
                if isinstance(result, Exception):
                    failed_requests += 1
                    errors.append(str(result))
                elif isinstance(result, dict) and "error" in result:
                    failed_requests += 1
                    errors.append(result["error"])
                elif isinstance(result, dict) and "response_time" in result:
                    successful_requests += 1
                    response_times.append(result["response_time"])
        
        actual_duration = time.time() - start_time
        
        # Calculate statistics
        if response_times:
            avg_response_time = statistics.mean(response_times)
            p95_response_time = statistics.quantiles(response_times, n=20)[18]  # 95th percentile
            p99_response_time = statistics.quantiles(response_times, n=100)[98]  # 99th percentile
        else:
            avg_response_time = 0
            p95_response_time = 0
            p99_response_time = 0
        
        result = LoadTestResult(
            total_requests=request_count,
            successful_requests=successful_requests,
            failed_requests=failed_requests,
            duration_seconds=actual_duration,
            requests_per_second=request_count / actual_duration,
            avg_response_time=avg_response_time,
            p95_response_time=p95_response_time,
            p99_response_time=p99_response_time,
            error_rate=failed_requests / request_count if request_count > 0 else 0,
            errors=errors[:10]  # Keep only first 10 errors
        )
        
        self.results.append(result)
        return result
    
    async def _execute_request_with_semaphore(self, target_function: Callable, 
                                            request_data: Any, 
                                            semaphore: asyncio.Semaphore) -> Dict[str, Any]:
        """Execute request with semaphore control."""
        
        async with semaphore:
            start_time = time.time()
            
            try:
                result = await target_function(request_data)
                response_time = time.time() - start_time
                
                return {
                    "result": result,
                    "response_time": response_time
                }
                
            except Exception as e:
                return {
                    "error": str(e),
                    "response_time": time.time() - start_time
                }
    
    async def run_stress_test(self, target_function: Callable,
                            request_generator: Callable,
                            max_rps: int = 1000,
                            rps_increment: int = 50,
                            test_duration: int = 30) -> List[LoadTestResult]:
        """Run stress test with increasing load."""
        
        print(f"Starting stress test: 0 to {max_rps} RPS")
        
        stress_results = []
        current_rps = rps_increment
        
        while current_rps <= max_rps:
            print(f"Testing {current_rps} RPS...")
            
            result = await self.run_load_test(
                target_function=target_function,
                request_generator=request_generator,
                duration_seconds=test_duration,
                requests_per_second=current_rps,
                max_concurrent=min(current_rps * 2, 500)
            )
            
            stress_results.append(result)
            
            # Stop if error rate is too high
            if result.error_rate > 0.1:  # 10% error rate
                print(f"Stopping stress test due to high error rate: {result.error_rate:.1%}")
                break
            
            current_rps += rps_increment
        
        return stress_results
    
    def print_results(self, result: LoadTestResult):
        """Print load test results."""
        
        print(f"\n{'='*50}")
        print(f"LOAD TEST RESULTS")
        print(f"{'='*50}")
        print(f"Duration: {result.duration_seconds:.1f}s")
        print(f"Total Requests: {result.total_requests}")
        print(f"Successful: {result.successful_requests}")
        print(f"Failed: {result.failed_requests}")
        print(f"Requests/Second: {result.requests_per_second:.1f}")
        print(f"Success Rate: {(1-result.error_rate)*100:.1f}%")
        print(f"Avg Response Time: {result.avg_response_time*1000:.1f}ms")
        print(f"P95 Response Time: {result.p95_response_time*1000:.1f}ms")
        print(f"P99 Response Time: {result.p99_response_time*1000:.1f}ms")
        
        if result.errors:
            print(f"\nSample Errors:")
            for error in result.errors[:5]:
                print(f"  - {error}")

# Usage example
async def test_workflow_performance():
    """Example load test for workflow execution."""
    
    load_tester = LoadTester()
    
    # Mock target function
    async def mock_execute_workflow(request_data):
        await asyncio.sleep(0.1)  # Simulate processing time
        if random.random() < 0.05:  # 5% error rate
            raise Exception("Simulated error")
        return {"status": "completed", "result": "success"}
    
    # Request generator
    def generate_request():
        return {
            "workflow_id": "test_workflow",
            "context": {"data": f"test_{random.randint(1, 1000)}"}
        }
    
    # Run load test
    result = await load_tester.run_load_test(
        target_function=mock_execute_workflow,
        request_generator=generate_request,
        duration_seconds=30,
        requests_per_second=50,
        max_concurrent=100
    )
    
    load_tester.print_results(result)
```

## Best Practices

### 1. Performance Monitoring

```python
# Continuous performance monitoring
async def performance_monitoring_loop():
    """Continuously monitor and log performance metrics."""
    
    while True:
        # Collect metrics
        memory_usage = memory_optimizer.get_memory_usage()
        event_bus_stats = optimized_event_bus.get_performance_stats()
        worker_stats = optimized_worker_manager.get_performance_report()
        
        # Log performance summary
        print(f"Performance Summary:")
        print(f"  Memory: {memory_usage['process']['percent']:.1f}%")
        print(f"  Event Bus: {event_bus_stats['avg_batch_size']:.1f} avg batch size")
        print(f"  Workers: {worker_stats['summary']['overall_success_rate']:.1%} success rate")
        
        await asyncio.sleep(60)  # Check every minute
```

### 2. Auto-scaling Configuration

```python
class AutoScaler:
    """Auto-scaling based on performance metrics."""
    
    def __init__(self, min_instances: int = 1, max_instances: int = 10):
        self.min_instances = min_instances
        self.max_instances = max_instances
        self.current_instances = min_instances
    
    async def check_scaling_conditions(self, metrics: Dict[str, Any]):
        """Check if scaling is needed."""
        
        cpu_usage = metrics.get("cpu_usage_percent", 0)
        memory_usage = metrics.get("memory_usage_percent", 0)
        error_rate = metrics.get("error_rate", 0)
        avg_latency = metrics.get("avg_latency_ms", 0)
        
        # Scale up conditions
        if (cpu_usage > 70 or memory_usage > 70 or 
            error_rate > 0.05 or avg_latency > 5000):
            
            if self.current_instances < self.max_instances:
                await self.scale_up()
        
        # Scale down conditions
        elif (cpu_usage < 30 and memory_usage < 30 and 
              error_rate < 0.01 and avg_latency < 1000):
            
            if self.current_instances > self.min_instances:
                await self.scale_down()
    
    async def scale_up(self):
        """Scale up instances."""
        self.current_instances += 1
        print(f"Scaling up to {self.current_instances} instances")
        # Implementation would add new instances
    
    async def scale_down(self):
        """Scale down instances."""
        self.current_instances -= 1
        print(f"Scaling down to {self.current_instances} instances")
        # Implementation would remove instances
```

### 3. Performance Tuning Checklist

```python
def performance_tuning_checklist():
    """Checklist for performance optimization."""
    
    checklist = {
        "Event Bus": [
            "✓ Connection pooling configured",
            "✓ Batch processing enabled", 
            "✓ Pipeline operations used",
            "✓ Serialization optimized (msgpack/orjson)",
            "✓ Compression enabled for large payloads"
        ],
        "Workers": [
            "✓ Concurrency limits set appropriately",
            "✓ Thread pool for CPU-bound tasks",
            "✓ Circuit breakers implemented",
            "✓ Timeout handling configured",
            "✓ Resource cleanup in finally blocks"
        ],
        "State Management": [
            "✓ In-memory caching enabled",
            "✓ Batch writes configured",
            "✓ TTL set for stored data",
            "✓ Binary serialization used",
            "✓ Cache eviction policy implemented"
        ],
        "Memory": [
            "✓ Garbage collection monitoring",
            "✓ Memory usage thresholds set",
            "✓ Object pooling for frequent allocations",
            "✓ Large object cleanup automated",
            "✓ Memory profiling enabled"
        ],
        "Monitoring": [
            "✓ Performance metrics collected",
            "✓ Alerting thresholds configured",
            "✓ Load testing performed",
            "✓ Bottleneck analysis automated",
            "✓ Performance dashboards created"
        ]
    }
    
    return checklist
```

This comprehensive performance guide provides the tools and strategies needed to optimize and scale the MultiAgents Framework for production workloads!