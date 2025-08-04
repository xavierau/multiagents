"""
Simple smoke test for load testing framework.
Verifies that load testing components work correctly.
"""
import pytest
import asyncio
from pathlib import Path
import tempfile

from tests.load.utils.metrics_collector import PerformanceCollector, LoadTestSummary
from tests.load.utils.load_generator import LoadGenerator, LoadConfig, LoadPattern


@pytest.mark.load
@pytest.mark.asyncio
class TestLoadFrameworkSmoke:
    """Smoke tests for load testing framework components."""
    
    async def test_metrics_collector_basic(self):
        """Test basic metrics collection functionality."""
        collector = PerformanceCollector(collection_interval=0.1)
        
        # Start collection
        collector.start_collection()
        
        # Simulate some requests
        for i in range(5):
            start_time = collector.record_request_start(f"test-{i}", "smoke_test")
            await asyncio.sleep(0.01)  # Simulate work
            collector.record_request_end(
                start_time, True, 
                transaction_id=f"test-{i}",
                workflow_type="smoke_test"
            )
        
        # Stop collection
        collector.stop_collection()
        
        # Generate summary
        summary = collector.get_summary("Smoke Test")
        
        assert summary.total_requests == 5
        assert summary.successful_requests == 5
        assert summary.failed_requests == 0
        assert summary.error_rate == 0.0
        assert summary.avg_response_time > 0
        assert len(collector.request_metrics) == 5
    
    async def test_load_generator_constant(self):
        """Test constant load pattern generation."""
        config = LoadConfig(
            pattern=LoadPattern.CONSTANT,
            duration_seconds=2,
            max_concurrent_requests=5,
            requests_per_second=3
        )
        
        executed_count = 0
        
        async def test_task():
            nonlocal executed_count
            executed_count += 1
            await asyncio.sleep(0.01)
            return {"success": True}
        
        generator = LoadGenerator(config)
        await generator.generate_load(test_task)
        
        # Should execute approximately 6 requests (3 RPS * 2 seconds)
        # Allow some variance due to timing
        assert 4 <= executed_count <= 8
    
    async def test_load_generator_burst(self):
        """Test burst load pattern."""
        config = LoadConfig(
            pattern=LoadPattern.CONSTANT,
            duration_seconds=1,
            max_concurrent_requests=10,
            # No RPS limit = burst mode
        )
        
        executed_count = 0
        
        async def test_task():
            nonlocal executed_count
            executed_count += 1
            await asyncio.sleep(0.01)
            return {"success": True}
        
        generator = LoadGenerator(config)
        await generator.generate_load(test_task)
        
        # Should execute exactly max_concurrent_requests in burst mode
        assert executed_count == 10
    
    async def test_error_handling_in_load_generator(self):
        """Test error handling during load generation."""
        config = LoadConfig(
            pattern=LoadPattern.CONSTANT,
            duration_seconds=1,
            max_concurrent_requests=5,
            requests_per_second=10
        )
        
        executed_count = 0
        error_count = 0
        
        async def failing_task():
            nonlocal executed_count, error_count
            executed_count += 1
            if executed_count % 2 == 0:  # Fail every second request
                error_count += 1
                raise Exception("Simulated failure")
            await asyncio.sleep(0.01)
            return {"success": True}
        
        generator = LoadGenerator(config)
        
        # Should not raise exception even with failing tasks
        await generator.generate_load(failing_task)
        
        assert executed_count > 0
        assert error_count > 0
    
    async def test_report_generation(self):
        """Test report generation functionality."""
        from tests.load.utils.metrics_collector import LoadTestReporter
        
        # Create sample summary
        summary = LoadTestSummary(
            test_name="Test Report Generation",
            duration_seconds=60.0,
            total_requests=100,
            successful_requests=95,
            failed_requests=5,
            requests_per_second=1.67,
            avg_response_time=0.05,
            min_response_time=0.01,
            max_response_time=0.15,
            p50_response_time=0.04,
            p95_response_time=0.12,
            p99_response_time=0.14,
            error_rate=0.05,
            peak_memory_mb=128.5,
            avg_cpu_percent=25.0,
            peak_cpu_percent=45.0,
            errors={"timeout": 3, "connection_error": 2}
        )
        
        # Test JSON export
        with tempfile.TemporaryDirectory() as temp_dir:
            json_file = Path(temp_dir) / "test_report.json"
            LoadTestReporter.export_json_report(summary, json_file)
            
            assert json_file.exists()
            assert json_file.stat().st_size > 0
            
            # Test HTML export
            html_file = Path(temp_dir) / "test_report.html"
            LoadTestReporter.generate_html_report(summary, Path(temp_dir), html_file)
            
            assert html_file.exists()
            assert html_file.stat().st_size > 0
            
            # Check HTML contains expected content
            html_content = html_file.read_text()
            assert "Test Report Generation" in html_content
            assert "100" in html_content  # Total requests
            assert "95.0%" in html_content  # Success rate
    
    def test_predefined_load_configs(self):
        """Test that predefined load configurations are valid."""
        from tests.load.utils.load_generator import create_load_configs
        
        configs = create_load_configs()
        
        # Check that all expected configs exist
        expected_configs = [
            'smoke', 'light', 'moderate', 'heavy', 
            'ramp_up', 'spike', 'step', 'wave', 
            'burst', 'endurance'
        ]
        
        for config_name in expected_configs:
            assert config_name in configs
            config = configs[config_name]
            
            # Validate config properties
            assert isinstance(config.pattern, LoadPattern)
            assert config.duration_seconds > 0
            assert config.max_concurrent_requests > 0
            
            # Pattern-specific validations
            if config.pattern == LoadPattern.RAMP_UP:
                assert config.ramp_up_seconds is not None
            elif config.pattern == LoadPattern.SPIKE:
                assert config.spike_multiplier is not None
            elif config.pattern == LoadPattern.STEP:
                assert config.step_size is not None
                assert config.step_duration_seconds is not None
            elif config.pattern == LoadPattern.WAVE:
                assert config.wave_period_seconds is not None