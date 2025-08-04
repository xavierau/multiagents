"""
Load tests for workflow execution performance.
Tests how the system performs under various workflow loads.
"""
import asyncio
import random
import time
from typing import Dict, Any, List
from pathlib import Path

from multiagents.orchestrator import WorkflowBuilder
from multiagents.core.saga_context import SagaState
from multiagents.worker_sdk import worker
from tests.load.utils.metrics_collector import PerformanceCollector, LoadTestReporter
from tests.load.utils.load_generator import LoadGenerator, LoadConfig, LoadPattern, ScenarioRunner, create_load_configs


class WorkflowLoadTest:
    """Load testing for workflow execution scenarios."""
    
    def __init__(self, orchestrator, worker_manager):
        self.orchestrator = orchestrator
        self.worker_manager = worker_manager
        self.metrics = PerformanceCollector()
        self._setup_complete = False
    
    async def setup(self):
        """Set up workers and workflows for load testing."""
        if self._setup_complete:
            return
        
        # Register load test workers
        await self._register_workers()
        
        # Register workflows
        await self._register_workflows()
        
        self._setup_complete = True
    
    async def _register_workers(self):
        """Register optimized workers for load testing."""
        
        @worker("fast_validator", timeout=30)
        async def fast_validator(context: Dict[str, Any]) -> Dict[str, Any]:
            """Fast validation worker for load testing."""
            await asyncio.sleep(0.01)  # Minimal processing time
            return {
                "validated": True,
                "validation_id": f"VAL-{random.randint(1000, 9999)}",
                "timestamp": time.time()
            }
        
        @worker("quick_processor", timeout=30) 
        async def quick_processor(context: Dict[str, Any]) -> Dict[str, Any]:
            """Quick processing worker."""
            await asyncio.sleep(0.02)
            return {
                "processed": True,
                "processing_id": f"PROC-{random.randint(1000, 9999)}",
                "items_processed": context.get("item_count", 1)
            }
        
        @worker("simple_finalizer", timeout=30)
        async def simple_finalizer(context: Dict[str, Any]) -> Dict[str, Any]:
            """Simple finalization worker."""
            await asyncio.sleep(0.005)
            return {
                "finalized": True,
                "final_id": f"FINAL-{random.randint(1000, 9999)}"
            }
        
        @worker("variable_worker", timeout=60)
        async def variable_worker(context: Dict[str, Any]) -> Dict[str, Any]:
            """Worker with variable processing time."""
            # Simulate different processing times
            processing_time = random.uniform(0.01, 0.1)
            await asyncio.sleep(processing_time)
            
            return {
                "processed": True,
                "processing_time": processing_time,
                "complexity": context.get("complexity", "simple")
            }
        
        @worker("cpu_intensive_worker", timeout=60)
        async def cpu_intensive_worker(context: Dict[str, Any]) -> Dict[str, Any]:
            """CPU-intensive worker for stress testing."""
            # Simulate CPU work
            iterations = context.get("iterations", 10000)
            start = time.time()
            
            # CPU-bound calculation
            result = 0
            for i in range(iterations):
                result += i * i
            
            end = time.time()
            
            return {
                "result": result,
                "cpu_time": end - start,
                "iterations": iterations
            }
        
        @worker("memory_intensive_worker", timeout=60)
        async def memory_intensive_worker(context: Dict[str, Any]) -> Dict[str, Any]:
            """Memory-intensive worker."""
            # Allocate some memory
            size = context.get("memory_size", 1000)
            data = [random.random() for _ in range(size)]
            
            await asyncio.sleep(0.01)
            
            # Process the data
            processed_sum = sum(data)
            
            return {
                "processed_sum": processed_sum,
                "memory_used": len(data) * 8,  # Approximate bytes
                "processed_items": len(data)
            }
        
        # Failure simulation workers
        @worker("intermittent_worker", timeout=30, retry_attempts=3)
        async def intermittent_worker(context: Dict[str, Any]) -> Dict[str, Any]:
            """Worker that fails intermittently."""
            failure_rate = context.get("failure_rate", 0.1)
            
            if random.random() < failure_rate:
                raise Exception(f"Simulated failure (rate: {failure_rate})")
            
            await asyncio.sleep(0.02)
            return {"success": True, "failure_rate": failure_rate}
        
        # Register all workers
        workers = [
            fast_validator, quick_processor, simple_finalizer,
            variable_worker, cpu_intensive_worker, memory_intensive_worker,
            intermittent_worker
        ]
        
        for worker_func in workers:
            await self.worker_manager.register_worker(worker_func)
    
    async def _register_workflows(self):
        """Register workflows for load testing."""
        
        # Simple 3-step workflow
        simple_builder = WorkflowBuilder("load-test-simple")
        simple_builder.add_step("validate", "fast_validator")
        simple_builder.add_step("process", "quick_processor")
        simple_builder.add_step("finalize", "simple_finalizer")
        simple_workflow = simple_builder.build()
        
        # Complex workflow with more steps
        complex_builder = WorkflowBuilder("load-test-complex")
        complex_builder.add_step("validate", "fast_validator")
        complex_builder.add_step("process1", "quick_processor")
        complex_builder.add_step("process2", "variable_worker")
        complex_builder.add_step("process3", "quick_processor")
        complex_builder.add_step("finalize", "simple_finalizer")
        complex_workflow = complex_builder.build()
        
        # CPU-intensive workflow
        cpu_builder = WorkflowBuilder("load-test-cpu")
        cpu_builder.add_step("validate", "fast_validator")
        cpu_builder.add_step("cpu_work", "cpu_intensive_worker")
        cpu_builder.add_step("finalize", "simple_finalizer")
        cpu_workflow = cpu_builder.build()
        
        # Memory-intensive workflow
        memory_builder = WorkflowBuilder("load-test-memory")
        memory_builder.add_step("validate", "fast_validator")
        memory_builder.add_step("memory_work", "memory_intensive_worker")
        memory_builder.add_step("finalize", "simple_finalizer")
        memory_workflow = memory_builder.build()
        
        # Failure-prone workflow
        failure_builder = WorkflowBuilder("load-test-failure")
        failure_builder.add_step("validate", "fast_validator")
        failure_builder.add_step("unreliable", "intermittent_worker")
        failure_builder.add_step("finalize", "simple_finalizer")
        failure_workflow = failure_builder.build()
        
        # Register all workflows
        workflows = [
            simple_workflow, complex_workflow, cpu_workflow,
            memory_workflow, failure_workflow
        ]
        
        for workflow in workflows:
            await self.orchestrator.register_workflow(workflow)
    
    async def create_simple_workflow_task(self) -> Dict[str, Any]:
        """Create a task for simple workflow execution."""
        start_time = self.metrics.record_request_start(workflow_type="simple")
        
        try:
            # Generate test data
            data = {
                "test_id": f"load-{random.randint(1000, 9999)}",
                "item_count": random.randint(1, 10)
            }
            
            # Execute workflow
            transaction_id = await self.orchestrator.execute_workflow(
                "load-test-simple", data
            )
            
            # Wait for completion (with timeout)
            await asyncio.sleep(0.1)  # Give it time to start
            
            # Check status
            max_wait = 30  # seconds
            wait_interval = 0.1
            waited = 0
            
            while waited < max_wait:
                state = await self.orchestrator.get_workflow_state(transaction_id)
                if state and state.state in [SagaState.COMPLETED, SagaState.FAILED, SagaState.COMPENSATED]:
                    break
                await asyncio.sleep(wait_interval)
                waited += wait_interval
            
            # Record success/failure
            final_state = await self.orchestrator.get_workflow_state(transaction_id)
            success = final_state and final_state.state == SagaState.COMPLETED
            
            self.metrics.record_request_end(
                start_time, success, 
                error=None if success else "Workflow failed or timed out",
                transaction_id=transaction_id,
                workflow_type="simple",
                step_count=3
            )
            
            return {
                "transaction_id": transaction_id,
                "success": success,
                "final_state": final_state.state.value if final_state else "unknown"
            }
            
        except Exception as e:
            self.metrics.record_request_end(
                start_time, False, str(e),
                workflow_type="simple"
            )
            raise
    
    async def create_complex_workflow_task(self) -> Dict[str, Any]:
        """Create a task for complex workflow execution."""
        start_time = self.metrics.record_request_start(workflow_type="complex")
        
        try:
            data = {
                "test_id": f"complex-{random.randint(1000, 9999)}",
                "complexity": random.choice(["simple", "medium", "high"]),
                "item_count": random.randint(5, 50)
            }
            
            transaction_id = await self.orchestrator.execute_workflow(
                "load-test-complex", data
            )
            
            # Wait for completion
            await asyncio.sleep(0.2)
            
            max_wait = 60
            wait_interval = 0.1
            waited = 0
            
            while waited < max_wait:
                state = await self.orchestrator.get_workflow_state(transaction_id)
                if state and state.state in [SagaState.COMPLETED, SagaState.FAILED, SagaState.COMPENSATED]:
                    break
                await asyncio.sleep(wait_interval)
                waited += wait_interval
            
            final_state = await self.orchestrator.get_workflow_state(transaction_id)
            success = final_state and final_state.state == SagaState.COMPLETED
            
            self.metrics.record_request_end(
                start_time, success,
                error=None if success else "Complex workflow failed or timed out",
                transaction_id=transaction_id,
                workflow_type="complex",
                step_count=5
            )
            
            return {
                "transaction_id": transaction_id,
                "success": success,
                "complexity": data["complexity"]
            }
            
        except Exception as e:
            self.metrics.record_request_end(
                start_time, False, str(e),
                workflow_type="complex"
            )
            raise
    
    async def create_cpu_intensive_task(self) -> Dict[str, Any]:
        """Create a CPU-intensive workflow task."""
        start_time = self.metrics.record_request_start(workflow_type="cpu_intensive")
        
        try:
            data = {
                "test_id": f"cpu-{random.randint(1000, 9999)}",
                "iterations": random.randint(5000, 20000)
            }
            
            transaction_id = await self.orchestrator.execute_workflow(
                "load-test-cpu", data
            )
            
            # CPU tasks may take longer
            await asyncio.sleep(0.1)
            
            max_wait = 90
            wait_interval = 0.2
            waited = 0
            
            while waited < max_wait:
                state = await self.orchestrator.get_workflow_state(transaction_id)
                if state and state.state in [SagaState.COMPLETED, SagaState.FAILED, SagaState.COMPENSATED]:
                    break
                await asyncio.sleep(wait_interval)
                waited += wait_interval
            
            final_state = await self.orchestrator.get_workflow_state(transaction_id)
            success = final_state and final_state.state == SagaState.COMPLETED
            
            self.metrics.record_request_end(
                start_time, success,
                error=None if success else "CPU workflow failed or timed out",
                transaction_id=transaction_id,
                workflow_type="cpu_intensive",
                step_count=3
            )
            
            return {
                "transaction_id": transaction_id,
                "success": success,
                "iterations": data["iterations"]
            }
            
        except Exception as e:
            self.metrics.record_request_end(
                start_time, False, str(e),
                workflow_type="cpu_intensive"
            )
            raise
    
    async def create_failure_prone_task(self) -> Dict[str, Any]:
        """Create a failure-prone workflow task."""
        start_time = self.metrics.record_request_start(workflow_type="failure_prone")
        
        try:
            data = {
                "test_id": f"failure-{random.randint(1000, 9999)}",
                "failure_rate": random.uniform(0.1, 0.3)  # 10-30% failure rate
            }
            
            transaction_id = await self.orchestrator.execute_workflow(
                "load-test-failure", data
            )
            
            await asyncio.sleep(0.1)
            
            max_wait = 45  # May need retries
            wait_interval = 0.1
            waited = 0
            
            while waited < max_wait:
                state = await self.orchestrator.get_workflow_state(transaction_id)
                if state and state.state in [SagaState.COMPLETED, SagaState.FAILED, SagaState.COMPENSATED]:
                    break
                await asyncio.sleep(wait_interval)
                waited += wait_interval
            
            final_state = await self.orchestrator.get_workflow_state(transaction_id)
            success = final_state and final_state.state == SagaState.COMPLETED
            
            self.metrics.record_request_end(
                start_time, success,
                error=None if success else f"Failure-prone workflow result: {final_state.state.value if final_state else 'timeout'}",
                transaction_id=transaction_id,
                workflow_type="failure_prone",
                step_count=3
            )
            
            return {
                "transaction_id": transaction_id,
                "success": success,
                "failure_rate": data["failure_rate"],
                "final_state": final_state.state.value if final_state else "timeout"
            }
            
        except Exception as e:
            self.metrics.record_request_end(
                start_time, False, str(e),
                workflow_type="failure_prone"
            )
            raise
    
    async def run_load_test_suite(self, output_dir: Path = None):
        """Run a comprehensive load test suite."""
        if output_dir:
            output_dir.mkdir(parents=True, exist_ok=True)
        
        await self.setup()
        
        # Get predefined configurations
        configs = create_load_configs()
        
        # Create scenario runner
        runner = ScenarioRunner("Workflow Load Test Suite")
        
        # Add scenarios
        runner.add_scenario(
            "Simple Workflow - Light Load",
            configs['light'],
            self.create_simple_workflow_task,
            "Basic 3-step workflow under light load"
        )
        
        runner.add_scenario(
            "Simple Workflow - Moderate Load", 
            configs['moderate'],
            self.create_simple_workflow_task,
            "Basic 3-step workflow under moderate load"
        )
        
        runner.add_scenario(
            "Complex Workflow - Light Load",
            configs['light'],
            self.create_complex_workflow_task,
            "5-step workflow with variable processing"
        )
        
        runner.add_scenario(
            "CPU Intensive - Light Load",
            configs['smoke'],  # Use lighter load for CPU tests
            self.create_cpu_intensive_task,
            "CPU-intensive workflow testing"
        )
        
        runner.add_scenario(
            "Failure Handling - Light Load",
            configs['light'],
            self.create_failure_prone_task,
            "Workflow with intermittent failures"
        )
        
        runner.add_scenario(
            "Ramp Up Test",
            configs['ramp_up'],
            self.create_simple_workflow_task,
            "Gradual load increase"
        )
        
        runner.add_scenario(
            "Spike Test",
            configs['spike'],
            self.create_simple_workflow_task,
            "Load spikes testing"
        )
        
        # Run all scenarios
        print(f"Starting load test suite: {runner.name}")
        print("="*80)
        
        results = await runner.run_all_scenarios(self.metrics)
        
        # Generate reports
        print("\n" + "="*80)
        print("LOAD TEST SUITE RESULTS")
        print("="*80)
        
        for result in results:
            LoadTestReporter.print_summary(result)
            
            if output_dir:
                # Export detailed metrics
                test_dir = output_dir / result.test_name.replace(" ", "_").lower()
                self.metrics.export_detailed_metrics(test_dir)
                
                # Export JSON report
                json_file = test_dir / "summary.json"
                LoadTestReporter.export_json_report(result, json_file)
                
                # Export HTML report
                html_file = test_dir / "report.html"
                LoadTestReporter.generate_html_report(result, test_dir, html_file)
        
        return results