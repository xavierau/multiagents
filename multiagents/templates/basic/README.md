# Basic MultiAgents Project

A simple MultiAgents framework project demonstrating core concepts.

## Quick Start

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Configure Redis connection in `config/settings.yaml`

3. Run the example:
   ```bash
   python main.py
   ```

## Project Structure

- `main.py` - Application entry point
- `workflows/` - Workflow definitions
- `workers/` - Worker implementations
- `config/` - Configuration files
- `tests/` - Test suite

## What This Example Shows

- Basic workflow creation with WorkflowBuilder
- Simple worker implementation with @worker decorator
- Event-driven communication via Redis
- Error handling and compensation
- Basic monitoring and logging

## Next Steps

- Customize workers in `workers/` directory
- Add more complex workflows in `workflows/`
- Configure monitoring in `config/monitoring.yaml`
- Run tests with `pytest tests/`