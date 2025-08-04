# Integration Tests

This directory contains integration tests that verify the complete MultiAgents framework functionality by testing real interactions between components.

## Overview

Integration tests differ from unit tests by:
- Using real Redis connections (test database)
- Testing complete workflows end-to-end
- Verifying inter-component communication
- Testing failure scenarios and compensations
- Validating monitoring and observability features

## Test Structure

```
tests/integration/
├── workflows/              # Workflow-specific integration tests
│   ├── test_basic_workflow.py          # Simple workflow execution
│   ├── test_compensation_workflow.py   # Failure and rollback scenarios  
│   └── test_event_flow.py              # Event bus and communication tests
├── fixtures/               # Reusable test data and workflows
│   ├── workflows.py        # Pre-built workflow definitions
│   └── test_data.py        # Sample data generators
├── utils/                  # Test utilities and workers
│   └── test_workers.py     # Mock workers for testing
├── test_end_to_end.py      # Complete system tests
├── conftest.py            # Integration test fixtures
└── README.md              # This file
```

## Prerequisites

### Redis Server
Integration tests require a running Redis server:

```bash
# Using Docker (recommended)
docker run -d -p 6379:6379 redis:alpine

# Or install locally
brew install redis  # macOS
apt-get install redis-server  # Ubuntu
```

### Dependencies
Ensure all test dependencies are installed:
```bash
pip install -r requirements.txt
```

## Running Integration Tests

### Using Test Runner
```bash
# Run all integration tests
python tests/test_runner.py integration

# Run end-to-end tests only
python tests/test_runner.py e2e

# Run with verbose output
python tests/test_runner.py integration --verbose
```

### Using Pytest Directly
```bash
# All integration tests
pytest tests/integration/ -m integration

# Specific test file
pytest tests/integration/workflows/test_basic_workflow.py

# End-to-end tests only
pytest tests/integration/test_end_to_end.py -m e2e

# With coverage
pytest tests/integration/ -m integration --cov=multiagents
```

### Test Markers
- `@pytest.mark.integration` - All integration tests
- `@pytest.mark.e2e` - End-to-end system tests
- `@pytest.mark.redis` - Tests requiring Redis
- `@pytest.mark.slow` - Long-running tests

## Test Categories

### 1. Basic Workflow Tests (`test_basic_workflow.py`)
- Simple sequential workflow execution
- Data flow between workflow steps
- State persistence and recovery
- Timeout handling

### 2. Compensation Tests (`test_compensation_workflow.py`) 
- Saga rollback on failures
- Partial compensations
- Compensation failure handling
- Retry logic for compensations

### 3. Event Flow Tests (`test_event_flow.py`)
- Event publication and consumption
- Event monitoring integration
- Concurrent event processing
- Error event propagation

### 4. End-to-End Tests (`test_end_to_end.py`)
- Complete order processing workflows
- Multiple concurrent workflows
- System restart and state persistence
- Monitoring and observability verification

## Test Workers

The `utils/test_workers.py` file contains mock workers that simulate real business logic:

- **validate_order_worker** - Order validation
- **check_inventory_worker** - Inventory checking with reservation
- **process_payment_worker** - Payment processing simulation
- **handle_shipping_worker** - Shipping arrangement
- **failing_worker** - Always fails (for testing error handling)
- **timeout_worker** - Times out (for testing timeout handling)
- **intermittent_worker** - Fails intermittently (for testing retries)

## Fixtures and Test Data

### Workflow Fixtures (`fixtures/workflows.py`)
Pre-built workflows for testing:
```python
from tests.integration.fixtures.workflows import get_workflow

# Get a simple linear workflow
workflow = get_workflow("simple")

# Get an e-commerce workflow with compensations
workflow = get_workflow("ecommerce")
```

### Test Data (`fixtures/test_data.py`)
Realistic test data generators:
```python
from tests.integration.fixtures.test_data import get_test_scenario

# Get a simple order
order = get_test_scenario("simple_order")

# Get a high-value order  
order = get_test_scenario("high_value_order")
```

## Writing Integration Tests

### Basic Structure
```python
import pytest
from multiagents.core.saga_context import SagaState

@pytest.mark.integration
@pytest.mark.asyncio
class TestMyIntegration:
    async def test_my_workflow(
        self,
        integration_orchestrator,
        integration_worker_manager
    ):
        # Register workers
        await integration_worker_manager.register_worker(my_worker)
        
        # Create and register workflow
        workflow = create_my_workflow()
        await integration_orchestrator.register_workflow(workflow)
        
        # Execute workflow
        transaction_id = await integration_orchestrator.execute_workflow(
            "my-workflow",
            {"test": "data"}
        )
        
        # Wait for completion
        await asyncio.sleep(2)
        
        # Verify results
        state = await integration_orchestrator.get_workflow_state(transaction_id)
        assert state.state == SagaState.COMPLETED
```

### Using Fixtures
```python
async def test_with_fixtures(
    self,
    integration_orchestrator,
    integration_worker_manager,
    sample_workflow_definition,
    order_data
):
    # Use pre-built workflow and data
    workflow = sample_workflow_definition()
    
    # Test with realistic data
    result = await run_workflow(workflow, order_data)
```

## Common Patterns

### Testing Failures
```python
# Register a failing worker
from tests.integration.utils.test_workers import failing_worker
await integration_worker_manager.register_worker(failing_worker)

# Add failing step to workflow
builder.add_step("fail", "failing_worker")

# Verify failure handling
state = await integration_orchestrator.get_workflow_state(transaction_id)
assert state.state == SagaState.FAILED
```

### Testing Compensations
```python
# Add compensation steps
builder.add_step(
    "process_payment",
    "payment_processor",
    compensation="refund_payment"
)

# After failure, verify compensation ran
assert state.data["refund_successful"] is True
```

### Concurrent Testing
```python
# Launch multiple workflows
tasks = []
for i in range(5):
    task = integration_orchestrator.execute_workflow(
        "concurrent-test",
        {"id": i}
    )
    tasks.append(task)

transaction_ids = await asyncio.gather(*tasks)
```

## Debugging Integration Tests

### Enable Debug Logging
```bash
pytest tests/integration/ -m integration -s --log-cli-level=DEBUG
```

### Check Redis Data
```bash
redis-cli -n 15  # Test database
KEYS *           # See all keys
GET saga:state:transaction-id  # Check workflow state
```

### Monitor Events
Integration tests include event monitoring. Check logs for:
- Event dispatch and pickup
- Processing start and completion
- Error tracking and compensation triggers

## Performance Considerations

Integration tests are slower than unit tests because they:
- Use real Redis connections
- Execute complete workflows
- Include realistic processing delays
- Test timeout scenarios

Expect integration tests to take 30 seconds to several minutes depending on the test suite.

## Troubleshooting

### Redis Connection Issues
```bash
# Check Redis is running
redis-cli ping

# Check port availability
netstat -an | grep 6379
```

### Test Database Cleanup
Tests use Redis database 15 to avoid conflicts. If tests fail unexpectedly:
```bash
redis-cli -n 15 FLUSHDB
```

### Worker Registration Issues
Ensure workers are registered before executing workflows:
```python
# Wrong - workers not registered
transaction_id = await orchestrator.execute_workflow("my-workflow", data)

# Correct - register first
await worker_manager.register_worker(my_worker)
transaction_id = await orchestrator.execute_workflow("my-workflow", data)
```

## CI/CD Integration

Integration tests are designed for CI/CD environments:

```yaml
# GitHub Actions example
- name: Start Redis
  run: docker run -d -p 6379:6379 redis:alpine

- name: Run Integration Tests
  run: pytest tests/integration/ -m integration --junitxml=integration-results.xml
```

The tests automatically clean up Redis state and handle test isolation.