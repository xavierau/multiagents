# Load Testing Framework

This directory contains a comprehensive load testing framework for the MultiAgents system, designed to measure performance, identify bottlenecks, and validate scalability under various load conditions.

## Overview

The load testing framework provides:
- **Multiple Load Patterns**: Constant, ramp-up, spike, step, and wave patterns
- **Component Testing**: Individual testing of event bus, workers, and orchestrator
- **Workflow Testing**: End-to-end workflow performance testing
- **Comprehensive Metrics**: Response times, throughput, error rates, system resources
- **Rich Reporting**: Console, JSON, HTML, and CSV reports

## Architecture

```
tests/load/
├── scenarios/              # Load test scenarios
│   ├── workflow_load_test.py       # Workflow-focused load tests
│   └── component_load_test.py      # Component-focused load tests
├── utils/                  # Load testing utilities
│   ├── metrics_collector.py        # Performance metrics collection
│   └── load_generator.py          # Load pattern generation
├── reports/                # Generated test reports (created during tests)
├── load_test_runner.py     # Main CLI runner
└── README.md              # This file
```

## Quick Start

### Prerequisites

1. **Redis Server**: Load tests require Redis
   ```bash
   docker run -d -p 6379:6379 redis:alpine
   ```

2. **Dependencies**: Install required packages
   ```bash
   pip install psutil aiohttp
   ```

### Running Load Tests

#### Using the Load Test Runner (Recommended)
```bash
# Quick smoke test (30 seconds)
python tests/load/load_test_runner.py smoke

# Full workflow load tests
python tests/load/load_test_runner.py workflow

# Component-specific load tests  
python tests/load/load_test_runner.py component

# Complete benchmark suite (30+ minutes)
python tests/load/load_test_runner.py benchmark
```

#### Using the Main Test Runner
```bash
# Run load tests via main test runner
python tests/test_runner.py load
```

#### With Output Reports
```bash
# Generate detailed reports
python tests/load/load_test_runner.py benchmark --output-dir ./load_reports
```

## Load Test Types

### 1. Smoke Tests
**Duration**: 30 seconds  
**Purpose**: Quick validation that system is functional  
**Load**: 5 concurrent requests at 2 RPS

```bash
python tests/load/load_test_runner.py smoke
```

### 2. Workflow Load Tests
**Duration**: 5-30 minutes  
**Purpose**: Test complete workflow execution performance  
**Scenarios**:
- Simple 3-step workflows
- Complex 5-step workflows  
- CPU-intensive workflows
- Memory-intensive workflows
- Failure-handling workflows

### 3. Component Load Tests
**Duration**: 10-20 minutes  
**Purpose**: Test individual component performance  
**Components**:
- Event Bus: Message publishing and consumption
- Worker Manager: Worker execution performance
- Orchestrator: Workflow coordination

### 4. Benchmark Suite
**Duration**: 30+ minutes  
**Purpose**: Comprehensive system performance evaluation  
**Includes**: All workflow and component tests with various load patterns

## Load Patterns

### Constant Load
Steady request rate throughout the test duration.
```python
LoadConfig(
    pattern=LoadPattern.CONSTANT,
    duration_seconds=120,
    max_concurrent_requests=50,
    requests_per_second=25
)
```

### Ramp-Up Load
Gradually increases from 0 to maximum load.
```python
LoadConfig(
    pattern=LoadPattern.RAMP_UP,
    duration_seconds=300,
    max_concurrent_requests=100,
    requests_per_second=50,
    ramp_up_seconds=120
)
```

### Spike Load
Normal load with periodic spikes.
```python
LoadConfig(
    pattern=LoadPattern.SPIKE,
    duration_seconds=300,
    requests_per_second=20,
    spike_multiplier=5  # 5x normal load during spikes
)
```

### Step Load
Load increases in steps over time.
```python
LoadConfig(
    pattern=LoadPattern.STEP,
    duration_seconds=600,
    requests_per_second=10,
    step_size=10,
    step_duration_seconds=60
)
```

### Wave Load  
Sinusoidal load pattern.
```python
LoadConfig(
    pattern=LoadPattern.WAVE,
    duration_seconds=600,
    requests_per_second=30,
    wave_period_seconds=120
)
```

## Metrics Collected

### Performance Metrics
- **Response Time**: Min, max, average, 50th/95th/99th percentiles
- **Throughput**: Requests per second
- **Success Rate**: Percentage of successful requests
- **Error Rate**: Failure percentage and error breakdown

### System Metrics
- **CPU Usage**: Average and peak CPU utilization
- **Memory Usage**: Peak memory consumption
- **Disk I/O**: Read/write throughput
- **Network I/O**: Network traffic
- **Redis Connections**: Active connection count

### Workflow-Specific Metrics
- **Step Count**: Number of workflow steps executed
- **Transaction Tracking**: End-to-end transaction timing
- **State Persistence**: Workflow state storage performance
- **Compensation Execution**: Rollback operation timing

## Report Formats

### Console Output
Real-time progress and summary displayed in terminal.

### JSON Reports
Machine-readable results for CI/CD integration.
```json
{
  "test_name": "Simple Workflow - Light Load",
  "duration_seconds": 60.5,
  "total_requests": 1205,
  "success_rate": 0.998,
  "requests_per_second": 19.9,
  "response_times": {
    "avg": 0.045,
    "p95": 0.089,
    "p99": 0.156
  }
}
```

### HTML Reports
Interactive web reports with charts and detailed analysis.

### CSV Data
Raw metrics data for custom analysis.
- `request_metrics.csv`: Individual request data
- `system_metrics.csv`: System resource usage over time

## Configuration

### Predefined Configurations
The framework includes predefined configurations:

- `smoke`: Quick validation (30s, 5 concurrent, 2 RPS)
- `light`: Light load (60s, 20 concurrent, 10 RPS)
- `moderate`: Moderate load (120s, 50 concurrent, 25 RPS)
- `heavy`: Heavy load (180s, 100 concurrent, 50 RPS)
- `burst`: Burst testing (1000 concurrent, no rate limit)
- `endurance`: Long-running test (30 minutes, sustained load)

### Custom Configurations
Create custom load configurations:

```python
from tests.load.utils.load_generator import LoadConfig, LoadPattern

custom_config = LoadConfig(
    pattern=LoadPattern.CONSTANT,
    duration_seconds=300,
    max_concurrent_requests=200,
    requests_per_second=100
)
```

## Performance Benchmarks

### Expected Performance (Reference System)
*Results may vary based on hardware and configuration*

| Test Type | RPS | Avg Response | P95 Response | Success Rate |
|-----------|-----|-------------|--------------|--------------|
| Simple Workflow | 50+ | <50ms | <100ms | >99% |
| Complex Workflow | 25+ | <100ms | <200ms | >98% |
| Event Bus Only | 500+ | <10ms | <25ms | >99.9% |
| Worker Execution | 100+ | <20ms | <50ms | >99% |

### Resource Usage
- **Memory**: <500MB peak for moderate loads
- **CPU**: <80% average for sustained loads
- **Redis**: <100 concurrent connections

## Troubleshooting

### Common Issues

**High Error Rates**
- Check Redis connectivity
- Verify worker registration
- Review timeout settings
- Monitor system resources

**Poor Performance**
- Check CPU/memory utilization
- Review Redis performance
- Optimize worker logic
- Tune concurrency limits

**Memory Leaks**
- Monitor peak memory usage
- Check for unclosed connections
- Review worker cleanup
- Analyze GC patterns

### Debug Mode
Run with verbose logging:
```bash
python tests/load/load_test_runner.py benchmark --redis-url redis://localhost:6379/15 --skip-cleanup
```

### Redis Monitoring
Monitor Redis during tests:
```bash
redis-cli -n 14 monitor
redis-cli -n 14 info memory
redis-cli -n 14 client list
```

## CI/CD Integration

### GitHub Actions Example
```yaml
name: Load Tests
on: [push, pull_request]

jobs:
  load-test:
    runs-on: ubuntu-latest
    services:
      redis:
        image: redis:alpine
        ports:
          - 6379:6379
    
    steps:
    - uses: actions/checkout@v2
    - name: Setup Python
      uses: actions/setup-python@v2
      with:
        python-version: 3.9
    
    - name: Install dependencies
      run: pip install -r requirements.txt
    
    - name: Run smoke tests
      run: python tests/load/load_test_runner.py smoke
    
    - name: Run load tests
      run: python tests/load/load_test_runner.py workflow --output-dir ./reports
    
    - name: Upload reports
      uses: actions/upload-artifact@v2
      with:
        name: load-test-reports
        path: ./reports
```

### Performance Regression Detection
Set performance thresholds:
```python
# In CI script
results = run_load_tests()
assert results.requests_per_second >= 45  # Minimum RPS
assert results.error_rate <= 0.02         # Max 2% error rate
assert results.p95_response_time <= 0.15  # Max 150ms P95
```

## Advanced Usage

### Custom Workers
Create specialized workers for specific load scenarios:

```python
@worker("custom_load_worker", timeout=60)
async def custom_worker(context: Dict[str, Any]) -> Dict[str, Any]:
    # Custom business logic
    processing_time = context.get("processing_time", 0.05)
    await asyncio.sleep(processing_time)
    
    return {
        "processed": True,
        "custom_metric": random.uniform(0, 100)
    }
```

### Custom Workflows
Define workflows for specific testing scenarios:

```python
def create_custom_workflow():
    builder = WorkflowBuilder("custom-load-test")
    builder.add_step("step1", "custom_load_worker")
    builder.add_step("step2", "another_worker")
    return builder.build()
```

### Metrics Analysis
Access raw metrics for custom analysis:

```python
from tests.load.utils.metrics_collector import PerformanceCollector

collector = PerformanceCollector()
# ... run tests ...
summary = collector.get_summary("My Test")

# Export detailed data
collector.export_detailed_metrics(Path("./my_analysis"))
```

## Extending the Framework

### Adding New Load Patterns
Implement custom load patterns in `LoadGenerator`:

```python
async def _custom_pattern_load(self, task_factory, progress_callback, start_time):
    # Custom load generation logic
    pass
```

### Custom Metrics
Extend metrics collection:

```python
class CustomMetrics(PerformanceCollector):
    def record_custom_metric(self, metric_name: str, value: float):
        # Custom metric recording
        pass
```

### Additional Report Formats
Add new report generators:

```python
class CustomReporter:
    @staticmethod
    def generate_pdf_report(summary, output_path):
        # Generate PDF report
        pass
```

## Best Practices

1. **Start Small**: Begin with smoke tests before running full load tests
2. **Monitor Resources**: Watch CPU, memory, and Redis performance
3. **Use Realistic Data**: Test with data similar to production
4. **Test Failure Scenarios**: Include error injection and recovery testing
5. **Baseline Performance**: Establish performance baselines for regression testing
6. **Clean Environment**: Use dedicated Redis databases and clean state
7. **Document Results**: Keep historical performance data for trend analysis

## Performance Tuning Tips

1. **Redis Optimization**:
   - Use Redis pipeline for bulk operations
   - Monitor Redis memory usage
   - Configure appropriate timeout values

2. **Worker Optimization**:
   - Minimize processing time in workers
   - Use async/await properly
   - Avoid blocking operations

3. **System Configuration**:
   - Tune OS-level parameters (file descriptors, etc.)
   - Monitor garbage collection
   - Use appropriate Python version and settings

4. **Load Test Design**:
   - Use appropriate concurrency levels
   - Design realistic load patterns
   - Test both normal and edge cases