#!/usr/bin/env python
"""
Main load test runner for the MultiAgents framework.
Provides CLI interface for running various load test scenarios.
"""
import argparse
import asyncio
import sys
from pathlib import Path
from datetime import datetime
import tempfile

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from multiagents.event_bus import RedisEventBus
from multiagents.orchestrator import Orchestrator
from multiagents.worker_sdk import WorkerManager
from multiagents.monitoring import EventMonitor, WorkerMonitor, MonitoringConfig

from tests.load.scenarios.workflow_load_test import WorkflowLoadTest
from tests.load.scenarios.component_load_test import CombinedComponentLoadTest
from tests.load.utils.load_generator import create_load_configs


async def create_test_system():
    """Create a complete system for load testing."""
    # Create monitoring config
    with tempfile.TemporaryDirectory() as temp_dir:
        log_path = Path(temp_dir) / "load_test.log"
        
        config = MonitoringConfig(
            log_level="INFO",
            log_file_path=str(log_path),
            event_trace_retention_hours=1,
            metrics_retention_hours=1
        )
        
        logger = config.create_logger()
        event_monitor = EventMonitor(logger=logger)
        worker_monitor = WorkerMonitor(logger=logger)
        
        # Create event bus
        event_bus = RedisEventBus(
            redis_url="redis://localhost:6379/14",  # Use DB 14 for load tests
            channel_prefix="load_test:",
            event_monitor=event_monitor,
            logger=logger
        )
        
        # Create orchestrator
        import redis.asyncio as redis
        redis_client = await redis.from_url("redis://localhost:6379/14")
        
        orchestrator = Orchestrator(
            event_bus=event_bus,
            state_store=redis_client,
            logger=logger
        )
        
        # Create worker manager
        worker_manager = WorkerManager(
            event_bus=event_bus,
            worker_monitor=worker_monitor,
            logger=logger
        )
        
        # Start all components
        await event_bus.start()
        await orchestrator.start()
        await worker_manager.start()
        
        return event_bus, orchestrator, worker_manager, redis_client


async def cleanup_system(event_bus, orchestrator, worker_manager, redis_client):
    """Clean up the test system."""
    try:
        await worker_manager.stop()
        await orchestrator.stop()
        await event_bus.stop()
        await redis_client.close()
    except Exception as e:
        print(f"Error during cleanup: {e}")


async def run_workflow_load_tests(event_bus, orchestrator, worker_manager, output_dir):
    """Run workflow-focused load tests."""
    print("Starting Workflow Load Tests")
    print("="*80)
    
    workflow_test = WorkflowLoadTest(orchestrator, worker_manager)
    results = await workflow_test.run_load_test_suite(output_dir)
    
    return results


async def run_component_load_tests(event_bus, orchestrator, worker_manager, output_dir):
    """Run component-focused load tests."""
    print("Starting Component Load Tests")
    print("="*80)
    
    component_test = CombinedComponentLoadTest(event_bus, worker_manager, orchestrator)
    results = await component_test.run_comprehensive_load_test(output_dir)
    
    return results


async def run_quick_smoke_test(event_bus, orchestrator, worker_manager):
    """Run a quick smoke test to verify system functionality."""
    print("Running Quick Smoke Test")
    print("="*30)
    
    workflow_test = WorkflowLoadTest(orchestrator, worker_manager)
    await workflow_test.setup()
    
    # Run a single simple workflow
    try:
        result = await workflow_test.create_simple_workflow_task()
        if result["success"]:
            print("✅ Smoke test PASSED - System is functional")
            return True
        else:
            print("❌ Smoke test FAILED - System has issues")
            return False
    except Exception as e:
        print(f"❌ Smoke test FAILED with error: {e}")
        return False


async def run_benchmark_suite(event_bus, orchestrator, worker_manager, output_dir):
    """Run the full benchmark suite."""
    print("Starting Full Benchmark Suite")
    print("="*80)
    
    all_results = []
    
    # 1. Smoke test first
    smoke_passed = await run_quick_smoke_test(event_bus, orchestrator, worker_manager)
    if not smoke_passed:
        print("Smoke test failed - aborting benchmark suite")
        return []
    
    print("\n")
    
    # 2. Workflow tests
    workflow_results = await run_workflow_load_tests(
        event_bus, orchestrator, worker_manager, 
        output_dir / "workflow_tests" if output_dir else None
    )
    all_results.extend(workflow_results)
    
    # 3. Component tests
    component_results = await run_component_load_tests(
        event_bus, orchestrator, worker_manager,
        output_dir / "component_tests" if output_dir else None
    )
    all_results.extend(component_results)
    
    return all_results


def print_final_summary(results):
    """Print a final summary of all test results."""
    if not results:
        print("\nNo test results to summarize.")
        return
    
    print("\n" + "="*80)
    print("FINAL BENCHMARK SUMMARY")
    print("="*80)
    
    # Calculate aggregate metrics
    total_requests = sum(r.total_requests for r in results)
    total_successful = sum(r.successful_requests for r in results)
    total_failed = sum(r.failed_requests for r in results)
    
    avg_rps = sum(r.requests_per_second for r in results) / len(results)
    avg_response_time = sum(r.avg_response_time for r in results) / len(results)
    worst_p95 = max(r.p95_response_time for r in results)
    peak_memory = max(r.peak_memory_mb for r in results)
    
    print(f"Tests Run: {len(results)}")
    print(f"Total Requests: {total_requests:,}")
    print(f"Successful Requests: {total_successful:,}")
    print(f"Failed Requests: {total_failed:,}")
    print(f"Overall Success Rate: {total_successful/total_requests:.1%}" if total_requests > 0 else "Overall Success Rate: N/A")
    print(f"Average RPS: {avg_rps:.1f}")
    print(f"Average Response Time: {avg_response_time:.3f}s")
    print(f"Worst 95th Percentile: {worst_p95:.3f}s")
    print(f"Peak Memory Usage: {peak_memory:.1f} MB")
    
    # Identify best and worst performing tests
    if len(results) > 1:
        best_rps = max(results, key=lambda r: r.requests_per_second)
        worst_error_rate = max(results, key=lambda r: r.error_rate)
        
        print(f"\nBest Throughput: {best_rps.test_name} ({best_rps.requests_per_second:.1f} RPS)")
        print(f"Highest Error Rate: {worst_error_rate.test_name} ({worst_error_rate.error_rate:.1%})")
    
    print("="*80)


async def main():
    parser = argparse.ArgumentParser(description="MultiAgents Load Test Runner")
    parser.add_argument(
        "test_type",
        choices=["smoke", "workflow", "component", "benchmark"],
        help="Type of load test to run"
    )
    parser.add_argument(
        "--output-dir", "-o",
        type=Path,
        help="Output directory for test reports"
    )
    parser.add_argument(
        "--redis-url",
        default="redis://localhost:6379/14",
        help="Redis URL for testing (default: redis://localhost:6379/14)"
    )
    parser.add_argument(
        "--skip-cleanup",
        action="store_true",
        help="Skip Redis cleanup (for debugging)"
    )
    
    args = parser.parse_args()
    
    # Create output directory if specified
    if args.output_dir:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        args.output_dir = args.output_dir / f"load_test_{timestamp}"
        args.output_dir.mkdir(parents=True, exist_ok=True)
        print(f"Output directory: {args.output_dir}")
    
    # Create test system
    print("Setting up test system...")
    try:
        event_bus, orchestrator, worker_manager, redis_client = await create_test_system()
        print("✅ Test system ready")
    except Exception as e:
        print(f"❌ Failed to set up test system: {e}")
        return 1
    
    results = []
    
    try:
        # Run selected test type
        if args.test_type == "smoke":
            await run_quick_smoke_test(event_bus, orchestrator, worker_manager)
            
        elif args.test_type == "workflow":
            results = await run_workflow_load_tests(
                event_bus, orchestrator, worker_manager, args.output_dir
            )
            
        elif args.test_type == "component":
            results = await run_component_load_tests(
                event_bus, orchestrator, worker_manager, args.output_dir
            )
            
        elif args.test_type == "benchmark":
            results = await run_benchmark_suite(
                event_bus, orchestrator, worker_manager, args.output_dir
            )
        
        # Print final summary
        if results:
            print_final_summary(results)
            
            if args.output_dir:
                print(f"\nDetailed reports saved to: {args.output_dir}")
    
    except KeyboardInterrupt:
        print("\n\nLoad test interrupted by user")
        return 1
    
    except Exception as e:
        print(f"\n❌ Load test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    finally:
        print("\nCleaning up test system...")
        if not args.skip_cleanup:
            # Clean Redis
            await redis_client.flushdb()
        
        await cleanup_system(event_bus, orchestrator, worker_manager, redis_client)
        print("✅ Cleanup complete")
    
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))