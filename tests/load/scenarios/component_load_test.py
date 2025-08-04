"""
Load tests for individual components.
Tests event bus, worker manager, and orchestrator performance independently.
"""
import asyncio
import random
import time
from typing import Dict, Any, List
from pathlib import Path

from multiagents.event_bus.events import CommandEvent, EventMetadata
from multiagents.worker_sdk import worker
from tests.load.utils.metrics_collector import PerformanceCollector, LoadTestReporter
from tests.load.utils.load_generator import LoadGenerator, LoadConfig, LoadPattern, create_load_configs


class EventBusLoadTest:
    """Load testing for event bus performance."""
    
    def __init__(self, event_bus):
        self.event_bus = event_bus
        self.metrics = PerformanceCollector()
        self.received_events = []
    
    async def setup(self):
        """Set up event handlers for testing."""
        # Subscribe to test events
        await self.event_bus.subscribe("load_test_worker", self._handle_test_event)
    
    async def _handle_test_event(self, event):
        """Handle incoming test events."""
        self.received_events.append({
            'event_id': event.id,
            'received_at': time.time(),
            'payload': event.payload
        })
    
    async def create_event_publish_task(self) -> Dict[str, Any]:
        """Create a task that publishes an event."""
        start_time = self.metrics.record_request_start(workflow_type="event_publish")
        
        try:
            # Create test event
            metadata = EventMetadata(
                transaction_id=f"load-{random.randint(1000, 9999)}",
                correlation_id=f"corr-{random.randint(1000, 9999)}",
                source="load_test"
            )
            
            event = CommandEvent(
                metadata=metadata,
                worker_type="load_test_worker",
                payload={
                    "test_data": f"payload-{random.randint(1, 1000)}",
                    "timestamp": time.time()
                }
            )
            
            # Publish event
            await self.event_bus.publish(event)
            
            self.metrics.record_request_end(
                start_time, True,
                transaction_id=metadata.transaction_id,
                workflow_type="event_publish"
            )
            
            return {
                "event_id": event.id,
                "success": True
            }
            
        except Exception as e:
            self.metrics.record_request_end(
                start_time, False, str(e),
                workflow_type="event_publish"
            )
            raise
    
    async def run_event_bus_load_test(self, config: LoadConfig):
        """Run load test on event bus."""
        print(f"Running event bus load test: {config.pattern.value}")
        
        await self.setup()
        
        # Clear metrics and received events
        self.metrics.clear_metrics()
        self.received_events.clear()
        
        # Start metrics collection
        self.metrics.start_collection()
        
        try:
            # Run load generator
            generator = LoadGenerator(config)
            await generator.generate_load(self.create_event_publish_task)
            
            # Wait for event processing
            await asyncio.sleep(2)
            
        finally:
            self.metrics.stop_collection()
        
        # Generate summary
        summary = self.metrics.get_summary("Event Bus Load Test")
        LoadTestReporter.print_summary(summary)
        
        # Additional event bus metrics
        published_count = summary.successful_requests
        received_count = len(self.received_events)
        
        print(f"\nEvent Bus Specific Metrics:")
        print(f"Events Published: {published_count}")
        print(f"Events Received: {received_count}")
        print(f"Event Delivery Rate: {received_count/published_count:.2%}" if published_count > 0 else "Event Delivery Rate: N/A")
        
        return summary


class WorkerManagerLoadTest:
    """Load testing for worker manager performance."""
    
    def __init__(self, worker_manager):
        self.worker_manager = worker_manager
        self.metrics = PerformanceCollector()
        self._setup_complete = False
    
    async def setup(self):
        """Set up test workers."""
        if self._setup_complete:
            return
        
        @worker("load_test_worker_1", timeout=30)
        async def load_worker_1(context: Dict[str, Any]) -> Dict[str, Any]:
            processing_time = random.uniform(0.01, 0.05)
            await asyncio.sleep(processing_time)
            return {
                "worker": "load_test_worker_1",
                "processed": True,
                "processing_time": processing_time
            }
        
        @worker("load_test_worker_2", timeout=30)
        async def load_worker_2(context: Dict[str, Any]) -> Dict[str, Any]:
            processing_time = random.uniform(0.02, 0.08)
            await asyncio.sleep(processing_time)
            return {
                "worker": "load_test_worker_2", 
                "processed": True,
                "processing_time": processing_time
            }
        
        @worker("load_test_worker_3", timeout=30)
        async def load_worker_3(context: Dict[str, Any]) -> Dict[str, Any]:
            processing_time = random.uniform(0.005, 0.03)
            await asyncio.sleep(processing_time)
            return {
                "worker": "load_test_worker_3",
                "processed": True,
                "processing_time": processing_time
            }
        
        # Register workers
        await self.worker_manager.register_worker(load_worker_1)
        await self.worker_manager.register_worker(load_worker_2)
        await self.worker_manager.register_worker(load_worker_3)
        
        self._setup_complete = True
    
    async def create_worker_task(self) -> Dict[str, Any]:
        """Create a task that executes a worker directly."""
        start_time = self.metrics.record_request_start(workflow_type="worker_execution")
        
        try:
            # Choose random worker
            worker_type = random.choice([
                "load_test_worker_1", 
                "load_test_worker_2", 
                "load_test_worker_3"
            ])
            
            # Create test context
            context = {
                "test_id": f"worker-{random.randint(1000, 9999)}",
                "data": f"test-data-{random.randint(1, 100)}",
                "timestamp": time.time()
            }
            
            # Get worker and execute
            worker_instance = self.worker_manager.workers.get(worker_type)
            if not worker_instance:
                raise Exception(f"Worker {worker_type} not found")
            
            result = await worker_instance.execute(context)
            
            self.metrics.record_request_end(
                start_time, True,
                workflow_type="worker_execution"
            )
            
            return {
                "worker_type": worker_type,
                "success": True,
                "result": result
            }
            
        except Exception as e:
            self.metrics.record_request_end(
                start_time, False, str(e),
                workflow_type="worker_execution"
            )
            raise
    
    async def run_worker_load_test(self, config: LoadConfig):
        """Run load test on worker manager."""
        print(f"Running worker manager load test: {config.pattern.value}")
        
        await self.setup()
        
        # Clear metrics
        self.metrics.clear_metrics()
        
        # Start metrics collection
        self.metrics.start_collection()
        
        try:
            # Run load generator
            generator = LoadGenerator(config)
            await generator.generate_load(self.create_worker_task)
            
        finally:
            self.metrics.stop_collection()
        
        # Generate summary
        summary = self.metrics.get_summary("Worker Manager Load Test")
        LoadTestReporter.print_summary(summary)
        
        return summary


class CombinedComponentLoadTest:
    """Load testing for combined component scenarios."""
    
    def __init__(self, event_bus, worker_manager, orchestrator):
        self.event_bus = event_bus
        self.worker_manager = worker_manager
        self.orchestrator = orchestrator
        self.metrics = PerformanceCollector()
    
    async def run_comprehensive_load_test(self, output_dir: Path = None):
        """Run comprehensive load tests on all components."""
        if output_dir:
            output_dir.mkdir(parents=True, exist_ok=True)
        
        results = []
        
        # Test configurations
        configs = create_load_configs()
        
        # 1. Event Bus Load Test
        print("\n" + "="*80)
        print("EVENT BUS LOAD TESTS")
        print("="*80)
        
        event_test = EventBusLoadTest(self.event_bus)
        
        for test_name, config in [
            ("Event Bus - Light", configs['light']),
            ("Event Bus - Moderate", configs['moderate']),
            ("Event Bus - Burst", configs['burst'])
        ]:
            print(f"\nRunning: {test_name}")
            summary = await event_test.run_event_bus_load_test(config)
            summary.test_name = test_name
            results.append(summary)
            
            if output_dir:
                test_dir = output_dir / test_name.replace(" ", "_").lower()
                event_test.metrics.export_detailed_metrics(test_dir)
                
                json_file = test_dir / "summary.json"
                LoadTestReporter.export_json_report(summary, json_file)
        
        # 2. Worker Manager Load Test
        print("\n" + "="*80)
        print("WORKER MANAGER LOAD TESTS")
        print("="*80)
        
        worker_test = WorkerManagerLoadTest(self.worker_manager)
        
        for test_name, config in [
            ("Worker Manager - Light", configs['light']),
            ("Worker Manager - Heavy", configs['heavy']),
            ("Worker Manager - Ramp Up", configs['ramp_up'])
        ]:
            print(f"\nRunning: {test_name}")
            summary = await worker_test.run_worker_load_test(config)
            summary.test_name = test_name
            results.append(summary)
            
            if output_dir:
                test_dir = output_dir / test_name.replace(" ", "_").lower()
                worker_test.metrics.export_detailed_metrics(test_dir)
                
                json_file = test_dir / "summary.json"
                LoadTestReporter.export_json_report(summary, json_file)
        
        # 3. Combined System Load Test (using workflow test)
        print("\n" + "="*80)
        print("INTEGRATED SYSTEM LOAD TESTS")
        print("="*80)
        
        from tests.load.scenarios.workflow_load_test import WorkflowLoadTest
        
        workflow_test = WorkflowLoadTest(self.orchestrator, self.worker_manager)
        workflow_results = await workflow_test.run_load_test_suite(output_dir)
        results.extend(workflow_results)
        
        # Generate combined report
        if output_dir:
            self._generate_combined_report(results, output_dir)
        
        return results
    
    def _generate_combined_report(self, results: List, output_dir: Path):
        """Generate a combined HTML report for all tests."""
        html_content = """
<!DOCTYPE html>
<html>
<head>
    <title>MultiAgents Load Test Suite - Combined Report</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .header { background: #f4f4f4; padding: 20px; border-radius: 5px; margin-bottom: 20px; }
        .test-section { margin: 20px 0; border: 1px solid #ddd; border-radius: 5px; }
        .test-header { background: #e8f4f8; padding: 15px; font-weight: bold; }
        .test-metrics { padding: 15px; }
        .metrics-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 10px; }
        .metric { text-align: center; }
        .metric-value { font-size: 18px; font-weight: bold; color: #007acc; }
        .metric-label { font-size: 12px; color: #666; }
        table { width: 100%; border-collapse: collapse; margin: 10px 0; }
        th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
        th { background-color: #f2f2f2; }
        .success { color: #388e3c; }
        .error { color: #d32f2f; }
    </style>
</head>
<body>
    <div class="header">
        <h1>MultiAgents Load Test Suite - Combined Report</h1>
        <p>Generated: {timestamp}</p>
        <p>Total Tests: {total_tests}</p>
    </div>
    
    <table>
        <tr>
            <th>Test Name</th>
            <th>Duration (s)</th>
            <th>Total Requests</th>
            <th>Success Rate</th>
            <th>RPS</th>
            <th>Avg Response (s)</th>
            <th>P95 Response (s)</th>
            <th>Peak Memory (MB)</th>
        </tr>
        {test_rows}
    </table>
    
    {detailed_sections}
</body>
</html>
        """
        
        from datetime import datetime
        
        # Generate table rows
        test_rows = ""
        detailed_sections = ""
        
        for result in results:
            success_rate = (1 - result.error_rate) * 100
            success_class = "success" if success_rate > 95 else "error" if success_rate < 90 else ""
            
            test_rows += f"""
        <tr>
            <td>{result.test_name}</td>
            <td>{result.duration_seconds:.1f}</td>
            <td>{result.total_requests}</td>
            <td class="{success_class}">{success_rate:.1f}%</td>
            <td>{result.requests_per_second:.1f}</td>
            <td>{result.avg_response_time:.3f}</td>
            <td>{result.p95_response_time:.3f}</td>
            <td>{result.peak_memory_mb:.1f}</td>
        </tr>
            """
            
            # Add detailed section
            detailed_sections += f"""
    <div class="test-section">
        <div class="test-header">{result.test_name}</div>
        <div class="test-metrics">
            <div class="metrics-grid">
                <div class="metric">
                    <div class="metric-value">{result.total_requests}</div>
                    <div class="metric-label">Total Requests</div>
                </div>
                <div class="metric">
                    <div class="metric-value">{result.requests_per_second:.1f}</div>
                    <div class="metric-label">Requests/sec</div>
                </div>
                <div class="metric">
                    <div class="metric-value">{result.avg_response_time:.3f}</div>
                    <div class="metric-label">Avg Response (s)</div>
                </div>
                <div class="metric">
                    <div class="metric-value">{result.p95_response_time:.3f}</div>
                    <div class="metric-label">95th Percentile (s)</div>
                </div>
                <div class="metric">
                    <div class="metric-value">{result.peak_memory_mb:.1f}</div>
                    <div class="metric-label">Peak Memory (MB)</div>
                </div>
                <div class="metric">
                    <div class="metric-value">{result.error_rate:.1%}</div>
                    <div class="metric-label">Error Rate</div>
                </div>
            </div>
        </div>
    </div>
            """
        
        html_final = html_content.format(
            timestamp=datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC"),
            total_tests=len(results),
            test_rows=test_rows,
            detailed_sections=detailed_sections
        )
        
        combined_report_file = output_dir / "combined_report.html"
        with open(combined_report_file, 'w') as f:
            f.write(html_final)
        
        print(f"\nCombined report generated: {combined_report_file}")