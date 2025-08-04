# MultiAgents Framework

A hybrid event-driven orchestration framework for building scalable, fault-tolerant distributed systems using a combination of orchestration and choreography patterns.

## Features

- **Hybrid Architecture**: Combines centralized orchestration with decoupled event-driven communication
- **DSPy Integration**: Built-in support for LLM-powered workers using DSPy
- **Comprehensive Monitoring**: Complete observability with event tracking, worker performance monitoring, and structured logging
- **Saga Pattern**: Built-in support for distributed transactions with compensation actions
- **Developer-Friendly**: Simple decorator-based API for creating workers
- **Scalable**: Horizontally scalable components with Redis backend

## Quick Start

### Prerequisites

1. **Python 3.8+**
2. **Redis Server** (for event bus and state storage)

Start Redis:
```bash
# macOS with Homebrew
brew services start redis

# Ubuntu/Debian
sudo systemctl start redis

# Docker
docker run -d -p 6379:6379 redis:alpine
```

### Installation

1. Clone and navigate to the project:
```bash
git clone <repository-url>
cd multiagents
```

2. Create virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

### Running Examples

**Option 1: Use the example runner (recommended)**
```bash
python run_examples.py
```

**Option 2: Run examples directly**
```bash
# Simple workflow
python -c "
import sys
sys.path.insert(0, '.')
import asyncio
from examples.simple_workflow import main
asyncio.run(main())
"

# E-commerce example with monitoring
python -c "
import sys
sys.path.insert(0, '.')
import asyncio
from examples.ecommerce_order.main import main
asyncio.run(main())
"

# Comprehensive monitoring demo
python -c "
import sys
sys.path.insert(0, '.')
import asyncio
from examples.monitoring_example import main
asyncio.run(main())
"
```

## Framework Overview

### Core Components

1. **Orchestrator**: Manages workflow state and coordinates activities
2. **Workers**: Stateless task executors created with simple decorators
3. **Event Bus**: Decoupled communication layer (Redis Pub/Sub)
4. **Monitoring**: Comprehensive observability and debugging

### Basic Usage

```python
from multiagents import (
    Orchestrator, WorkflowBuilder, WorkerManager, worker
)
from multiagents.event_bus.redis_bus import RedisEventBus

# Define workers
@worker("process_data")
async def process_data_worker(context):
    data = context["input_data"]
    # Process the data
    return {"processed": data, "timestamp": "2024-01-01T00:00:00Z"}

# Create workflow
workflow = (WorkflowBuilder("data_processing")
    .add_step("process", "process_data")
    .build())

# Set up framework
event_bus = RedisEventBus()
worker_manager = WorkerManager(event_bus)
orchestrator = Orchestrator(workflow, event_bus)

# Register worker and start
worker_manager.register(process_data_worker)
await event_bus.start()
await worker_manager.start()
await orchestrator.start()

# Execute workflow
transaction_id = await orchestrator.execute_workflow(
    "data_processing",
    {"input_data": "example data"}
)
```

### Monitoring & Observability

The framework includes comprehensive monitoring:

```python
from multiagents.monitoring import MonitoringConfig, EventMonitor, WorkerMonitor

# Setup monitoring
config = MonitoringConfig()
logger = config.create_logger()
event_monitor = EventMonitor(logger=logger)
worker_monitor = WorkerMonitor(logger=logger)

# Integrate with framework
event_bus = RedisEventBus(event_monitor=event_monitor, logger=logger)
worker_manager = WorkerManager(event_bus, worker_monitor=worker_monitor, logger=logger)
```

**Monitoring Features:**
- **Event Lifecycle Tracking**: Complete event journey from dispatch to completion
- **Worker Performance**: Success rates, processing times, health monitoring
- **Structured Logging**: JSON logs with automatic rotation
- **Error Tracking**: Detailed error context and failure patterns
- **Real-time Metrics**: Performance dashboards and alerting

**Configuration (monitoring.yaml):**
```yaml
logging:
  default_logger: "file"
  level: "INFO"
  file_path: "./logs/multiagents.log"

event_monitoring:
  enabled: true
  trace_retention_hours: 24

worker_monitoring:
  enabled: true
  health_check_interval_seconds: 30
```

## Examples

### 1. Simple Workflow
Basic workflow demonstrating core framework features.

### 2. E-commerce Order Processing
Complete order processing pipeline with:
- Order validation
- Inventory checking with compensation
- Payment processing with refund compensation
- DSPy-powered order confirmation generation
- Fulfillment and customer notification

### 3. Monitoring Demonstration
Comprehensive monitoring example showing:
- Event lifecycle tracking
- Worker performance monitoring
- Error handling and recovery
- System metrics collection

## Development

### Project Structure
```
multiagents/
├── orchestrator/          # Workflow orchestration
├── worker_sdk/           # Worker development SDK
├── event_bus/            # Event bus implementations
├── monitoring/           # Observability system
├── core/                 # Core utilities
└── examples/             # Example implementations
```

### Key Design Principles
- **SOLID Principles**: Clean, maintainable architecture
- **Event-Driven**: Fully decoupled communication
- **Fault Tolerance**: Built-in compensation and rollback
- **Observability**: Comprehensive monitoring and debugging
- **Developer Experience**: Simple, intuitive APIs

### Common Commands
```bash
# Install dependencies
pip install -r requirements.txt

# Run examples
python run_examples.py

# Run tests (when available)
pytest

# Format code
black .
ruff check --fix .

# Type checking
mypy multiagents/
```

## Architecture

The framework follows a hybrid orchestration/choreography pattern:

- **Orchestration**: Centralized workflow management with state machine
- **Choreography**: Decoupled event-driven communication between components
- **Saga Pattern**: Distributed transaction management with compensations
- **Event Sourcing**: Complete audit trail of all activities

This approach provides the benefits of both patterns:
- **Centralized Logic**: Easy to understand and debug workflows
- **Decoupled Components**: Scalable and resilient architecture
- **Fault Tolerance**: Automatic compensation and recovery
- **Observability**: Complete visibility into system behavior

## Contributing

1. Follow SOLID principles and clean code practices
2. Add comprehensive monitoring to all components
3. Include tests for new functionality
4. Update documentation and examples

## License

[License information to be added]