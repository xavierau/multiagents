# MultiAgents Framework Tests

This directory contains the test suite for the MultiAgents framework.

## Test Structure

```
tests/
├── unit/                    # Unit tests for individual components
│   ├── core/               # Core functionality tests
│   ├── event_bus/          # Event system tests
│   ├── orchestrator/       # Workflow orchestration tests
│   ├── worker_sdk/         # Worker SDK tests
│   └── monitoring/         # Monitoring system tests
├── integration/            # Integration tests (Phase 2)
├── conftest.py            # Shared pytest fixtures
├── pytest.ini             # Pytest configuration
└── test_runner.py         # Convenient test runner script
```

## Running Tests

### Quick Start

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=multiagents

# Run only unit tests
pytest tests/unit/

# Run tests for a specific module
pytest tests/unit/event_bus/
```

### Using the Test Runner

The test runner provides convenient commands:

```bash
# Run all tests with coverage
python tests/test_runner.py all

# Run only unit tests
python tests/test_runner.py unit

# Run integration tests  
python tests/test_runner.py integration

# Run end-to-end tests
python tests/test_runner.py e2e

# Run load/performance tests
python tests/test_runner.py load

# Run with detailed coverage report
python tests/test_runner.py coverage

# Run fast tests only (exclude slow/integration)
python tests/test_runner.py fast
```

### Test Markers

Tests are marked for selective execution:

- `@pytest.mark.unit` - Unit tests
- `@pytest.mark.integration` - Integration tests
- `@pytest.mark.slow` - Slow tests
- `@pytest.mark.redis` - Tests requiring Redis
- `@pytest.mark.dspy` - Tests requiring DSPy/LLM

Run tests by marker:
```bash
pytest -m "unit"           # Only unit tests
pytest -m "not slow"       # Exclude slow tests
pytest -m "redis"          # Only Redis tests
```

### Coverage Reports

After running tests with coverage:

- **Terminal**: Coverage summary shown in terminal
- **HTML**: Open `htmlcov/index.html` in browser
- **XML**: `coverage.xml` for CI integration

## Writing Tests

### Unit Test Example

```python
import pytest
from multiagents.event_bus import CommandEvent, EventMetadata

class TestCommandEvent:
    def test_command_event_creation(self):
        metadata = EventMetadata(
            transaction_id="trans-123",
            correlation_id="corr-456",
            source="test"
        )
        event = CommandEvent(
            metadata=metadata,
            worker_type="payment_worker",
            payload={"amount": 100}
        )
        
        assert event.worker_type == "payment_worker"
        assert event.payload["amount"] == 100
```

### Async Test Example

```python
import pytest

class TestAsyncComponent:
    @pytest.mark.asyncio
    async def test_async_operation(self):
        result = await some_async_function()
        assert result == expected_value
```

### Using Fixtures

Common fixtures are available in `conftest.py`:

```python
@pytest.mark.asyncio
async def test_with_fixtures(mock_logger, mock_event_bus):
    # mock_logger and mock_event_bus are automatically injected
    component = MyComponent(logger=mock_logger, event_bus=mock_event_bus)
    await component.process()
    
    mock_logger.info.assert_called()
    mock_event_bus.publish.assert_called()
```

## Test Guidelines

1. **Isolation**: Each test should be independent
2. **Clarity**: Test names should describe what they test
3. **Coverage**: Aim for >80% code coverage
4. **Mocking**: Mock external dependencies (Redis, network, etc.)
5. **Async**: Use `@pytest.mark.asyncio` for async tests

## Current Test Status

- ✅ Unit Tests: Core components (events, saga, workflow)  
- ✅ Integration Tests: End-to-end workflow execution, compensations, event flow
- ✅ Load Tests: Performance benchmarking, scalability testing, resource monitoring

## Troubleshooting

### Import Errors
Ensure you're in the project root and the package is installed:
```bash
pip install -e .
```

### Redis Connection Errors
Unit tests mock Redis. For integration tests, ensure Redis is running:
```bash
docker run -d -p 6379:6379 redis:alpine
```

Integration tests use Redis database 15 to avoid conflicts with your main data.

### Async Test Issues
Ensure `pytest-asyncio` is installed:
```bash
pip install pytest-asyncio
```