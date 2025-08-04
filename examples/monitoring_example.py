"""
Comprehensive monitoring example demonstrating observability features.
"""
import asyncio
import json
from datetime import datetime
from multiagents import (
    Orchestrator, WorkflowBuilder, WorkerManager,
    worker
)
from multiagents.event_bus.redis_bus import RedisEventBus
from multiagents.monitoring import (
    MonitoringConfig, EventMonitor, WorkerMonitor, MetricsCollector
)


# Define workers with different behaviors for monitoring demo
@worker("fast_worker")
async def fast_worker(context):
    """Worker that completes quickly."""
    await asyncio.sleep(0.1)
    return {"result": "fast_completion", "processed_at": datetime.utcnow().isoformat()}


@worker("slow_worker") 
async def slow_worker(context):
    """Worker that takes longer to complete."""
    await asyncio.sleep(2.0)
    return {"result": "slow_completion", "processed_at": datetime.utcnow().isoformat()}


@worker("failing_worker")
async def failing_worker(context):
    """Worker that sometimes fails for monitoring demo."""
    import random
    if random.random() < 0.3:  # 30% failure rate
        raise Exception("Simulated worker failure")
    await asyncio.sleep(0.5)
    return {"result": "success_after_risk", "processed_at": datetime.utcnow().isoformat()}


@worker("timeout_worker")
async def timeout_worker(context):
    """Worker that may timeout."""
    timeout = context.get("simulate_timeout", False)
    if timeout:
        await asyncio.sleep(10)  # Will timeout with default 5s timeout
    await asyncio.sleep(1.0)
    return {"result": "completed_without_timeout", "processed_at": datetime.utcnow().isoformat()}


async def setup_monitoring() -> tuple:
    """Set up comprehensive monitoring system."""
    # Load monitoring configuration
    config = MonitoringConfig()
    
    # Create logger
    logger = config.create_logger()
    
    # Create monitoring components
    event_monitor = EventMonitor(
        logger=logger,
        max_trace_history=config.event_monitoring.max_trace_history,
        cleanup_interval_minutes=config.event_monitoring.cleanup_interval_minutes,
        trace_retention_hours=config.event_monitoring.trace_retention_hours
    )
    
    worker_monitor = WorkerMonitor(
        logger=logger,
        health_check_interval_seconds=config.worker_monitoring.health_check_interval_seconds,
        metrics_retention_hours=config.worker_monitoring.metrics_retention_hours,
        max_metrics_per_worker=config.worker_monitoring.max_metrics_per_worker
    )
    
    metrics_collector = MetricsCollector(
        logger=logger,
        collection_interval_seconds=config.metrics.collection_interval_seconds,
        retention_days=config.metrics.retention_days
    )
    
    # Start monitoring components
    await event_monitor.start()
    await worker_monitor.start()
    await metrics_collector.start()
    
    print("✅ Monitoring system initialized")
    
    return logger, event_monitor, worker_monitor, metrics_collector


async def create_monitored_workflow() -> tuple:
    """Create workflow with monitoring integration."""
    # Set up monitoring
    logger, event_monitor, worker_monitor, metrics_collector = await setup_monitoring()
    
    # Create event bus with monitoring
    event_bus = RedisEventBus(
        event_monitor=event_monitor,
        logger=logger
    )
    
    # Create worker manager with monitoring
    worker_manager = WorkerManager(
        event_bus,
        event_monitor=event_monitor,
        worker_monitor=worker_monitor,
        logger=logger
    )
    
    # Create workflow
    workflow = (WorkflowBuilder("monitoring_demo_workflow")
        .add_step("fast_step", "fast_worker", timeout=5)
        .add_step("slow_step", "slow_worker", timeout=5)
        .add_step("risky_step", "failing_worker", timeout=5)
        .add_step("timeout_step", "timeout_worker", timeout=3)  # Short timeout
        .build())
    
    orchestrator = Orchestrator(workflow, event_bus)
    
    return (event_bus, worker_manager, orchestrator, 
            logger, event_monitor, worker_monitor, metrics_collector)


async def run_monitoring_demo():
    """Run monitoring demonstration."""
    print("🚀 Starting Monitoring Demo\n")
    
    # Setup components
    (event_bus, worker_manager, orchestrator,
     logger, event_monitor, worker_monitor, metrics_collector) = await create_monitored_workflow()
    
    try:
        # Start components
        print("📡 Starting components...")
        await event_bus.start()
        
        # Register workers
        print("👷 Registering workers...")
        worker_manager.register(fast_worker)
        worker_manager.register(slow_worker)
        worker_manager.register(failing_worker)
        worker_manager.register(timeout_worker)
        
        await worker_manager.start()
        await orchestrator.start()
        
        print(f"✅ Registered {len(worker_manager.list_workers())} workers\n")
        
        # Run multiple workflow instances to generate monitoring data
        print("🔄 Running multiple workflows to generate monitoring data...\n")
        
        workflow_tasks = []
        for i in range(5):
            # Some workflows will have timeout issues
            input_data = {
                "workflow_instance": i + 1,
                "simulate_timeout": i == 3  # 4th workflow will timeout
            }
            
            task = asyncio.create_task(
                orchestrator.execute_workflow(
                    orchestrator.workflow.get_id(),
                    input_data
                )
            )
            workflow_tasks.append(task)
            
            # Small delay between workflow starts
            await asyncio.sleep(0.5)
        
        # Wait for all workflows to start
        transaction_ids = await asyncio.gather(*workflow_tasks, return_exceptions=True)
        print(f"🎯 Started {len(transaction_ids)} workflow instances\n")
        
        # Monitor progress for a while
        print("📊 Monitoring workflow progress...")
        for i in range(30):  # Monitor for 30 seconds
            await asyncio.sleep(1)
            
            # Show periodic monitoring stats
            if i % 10 == 0:
                await show_monitoring_stats(event_monitor, worker_monitor, metrics_collector)
        
        # Final monitoring report
        print("\n" + "="*60)
        print("📈 FINAL MONITORING REPORT")
        print("="*60)
        await show_detailed_monitoring_report(event_monitor, worker_monitor, metrics_collector)
        
    except KeyboardInterrupt:
        print("\n⚠️  Demo interrupted by user")
    except Exception as e:
        print(f"\n❌ Demo error: {e}")
        await logger.error("Demo failed", error=e)
    finally:
        # Cleanup
        print("\n🧹 Cleaning up...")
        await worker_manager.stop()
        await orchestrator.stop() 
        await event_bus.stop()
        await event_monitor.stop()
        await worker_monitor.stop()
        await metrics_collector.stop()
        await logger.close()
        print("✅ Cleanup complete")


async def show_monitoring_stats(event_monitor, worker_monitor, metrics_collector):
    """Show current monitoring statistics."""
    print("\n📊 Current Monitoring Stats:")
    
    # Event metrics
    event_metrics = await event_monitor.get_event_metrics(time_window_minutes=5)
    print(f"  📨 Events (last 5 min): {event_metrics['total_events']}")
    print(f"  ✅ Success rate: {event_metrics['success_rate']:.1f}%")
    if event_metrics['average_processing_time'] > 0:
        print(f"  ⏱️  Avg processing: {event_metrics['average_processing_time']:.2f}s")
    
    # Worker performance
    worker_summary = await worker_monitor.get_worker_performance_summary(time_window_minutes=5)
    print(f"  👷 Total commands: {worker_summary['aggregated_metrics']['total_commands']}")
    print(f"  🎯 Worker success rate: {worker_summary['aggregated_metrics']['average_success_rate']:.1f}%")
    
    # Problem workers
    if worker_summary['problem_workers']:
        print(f"  ⚠️  Problem workers: {len(worker_summary['problem_workers'])}")
    
    print("-" * 40)


async def show_detailed_monitoring_report(event_monitor, worker_monitor, metrics_collector):
    """Show detailed monitoring report."""
    # Event monitoring report
    print("\n🔍 EVENT MONITORING:")
    event_metrics = await event_monitor.get_event_metrics(time_window_minutes=30)
    print(f"  Total Events: {event_metrics['total_events']}")
    print(f"  Success Rate: {event_metrics['success_rate']:.1f}%")
    print(f"  Average Duration: {event_metrics['average_processing_time']:.2f}s")
    
    if event_metrics.get('events_by_type'):
        print("\n  Events by Type:")
        for event_type, count in event_metrics['events_by_type'].items():
            print(f"    {event_type}: {count}")
    
    if event_metrics.get('events_by_status'):
        print("\n  Events by Status:")
        for status, count in event_metrics['events_by_status'].items():
            print(f"    {status}: {count}")
    
    # Worker monitoring report
    print("\n👷 WORKER MONITORING:")
    worker_summary = await worker_monitor.get_worker_performance_summary(time_window_minutes=30)
    agg = worker_summary['aggregated_metrics']
    
    print(f"  Total Commands: {agg['total_commands']}")
    print(f"  Successful: {agg['successful_commands']}")
    print(f"  Failed: {agg['failed_commands']}")
    print(f"  Timeouts: {agg['timeout_commands']}")
    print(f"  Success Rate: {agg['average_success_rate']:.1f}%")
    print(f"  Avg Processing Time: {agg['average_processing_time']:.2f}s")
    
    # Individual worker stats
    print("\n  Individual Worker Performance:")
    for worker_key, worker_data in worker_summary['workers'].items():
        print(f"    {worker_data['worker_type']}:")
        print(f"      Commands: {worker_data['recent_commands']}")
        print(f"      Success Rate: {worker_data['success_rate']:.1f}%")
        print(f"      Avg Time: {worker_data['average_processing_time']:.2f}s")
        print(f"      Health: {worker_data['health_status']}")
    
    # Problem workers
    if worker_summary['problem_workers']:
        print("\n  ⚠️ Problem Workers:")
        for worker in worker_summary['problem_workers']:
            print(f"    {worker['worker_type']}: {worker['failure_rate']:.1f}% failure rate")
    
    # System metrics
    print("\n💻 SYSTEM METRICS:")
    system_metrics = await metrics_collector.get_system_metrics(time_window_minutes=30)
    
    if system_metrics.get('system_metrics'):
        for metric_name, stats in system_metrics['system_metrics'].items():
            print(f"  {metric_name}: {stats['latest']:.2f} (avg: {stats['average']:.2f})")
    
    # Monitor statistics
    print("\n🔧 MONITORING SYSTEM STATS:")
    event_stats = event_monitor.get_monitor_stats()
    worker_stats = worker_monitor.get_monitor_stats()
    collector_stats = metrics_collector.get_collector_stats()
    
    print(f"  Event Monitor: {event_stats['active_traces']} active traces")
    print(f"  Worker Monitor: {worker_stats['worker_count']} workers tracked")
    print(f"  Metrics Collector: {collector_stats['total_event_metrics']} event metrics stored")


async def main():
    """Main entry point."""
    print("⚠️  Make sure Redis is running on localhost:6379\n")
    await run_monitoring_demo()


if __name__ == "__main__":
    asyncio.run(main())