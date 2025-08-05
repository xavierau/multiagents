# MultiAgents Framework Quick Reference

**🚀 LLM-Powered Multi-Agent Orchestration Framework**

This is your one-stop reference for the MultiAgents Framework. Keep this handy while developing!

## 📦 Installation & Setup

```bash
# Install from PyPI
pip install multiagents-framework

# Verify installation  
multiagents --version

# Start Redis (required)
docker run -d -p 6379:6379 redis:alpine
```

## 🔧 Core Components

### 1. Workers (Task Executors)

```python
from multiagents import worker, dspy_worker

# Basic worker
@worker("my_worker")
async def my_worker(context):
    return {"result": "processed", "status": "success"}

# LLM-powered worker with DSPy
@dspy_worker("ai_worker", signature="input_text -> response")
async def ai_worker(context):
    # DSPy handles LLM interaction automatically
    return context
```

### 2. Workflows (Orchestration)

```python
from multiagents.orchestrator.workflow import WorkflowBuilder

# Build workflow
workflow = (WorkflowBuilder("my_workflow")
    .add_step("step1", "worker1")
    .add_step("step2", "worker2", compensation="undo_worker2")
    .add_conditional_step("step3", "worker3", 
                         condition=lambda ctx: ctx.get("proceed", False))
    .build())
```

### 3. Framework Setup

```python
from multiagents.core.factory import create_simple_framework

# Quick setup with monitoring
event_bus, worker_manager, orchestrator = await create_simple_framework(workflow)

# Register workers
worker_manager.register(my_worker)
worker_manager.register(ai_worker)

# Start framework
await event_bus.start()
await worker_manager.start()
await orchestrator.start()

# Execute workflow
tx_id = await orchestrator.execute_workflow("my_workflow", {"input": "data"})
```

## 🎯 Common Patterns

### LLM Agent Pattern
```python
@dspy_worker("agent_researcher")
async def research_agent(context):
    query = context["query"]
    # DSPy automatically handles:
    # - LLM prompting
    # - Response parsing
    # - Error handling
    return context

@dspy_worker("agent_summarizer", signature="research_data -> summary")
async def summary_agent(context):
    return context

# Chain agents in workflow
workflow = (WorkflowBuilder("research_pipeline")
    .add_step("research", "agent_researcher")
    .add_step("summarize", "agent_summarizer")
    .build())
```

### Error Handling & Compensation
```python
@worker("charge_payment")
async def charge_payment(context):
    # Main operation
    return {"charge_id": "CHG-123", "amount": 99.99}

@worker("refund_payment") 
async def refund_payment(context):
    # Compensation operation
    charge_id = context["charge_id"]
    return {"refund_id": "REF-123", "status": "refunded"}

# Use in workflow
workflow = (WorkflowBuilder("payment_flow")
    .add_step("charge", "charge_payment", compensation="refund_payment")
    .build())
```

### Monitoring & Observability
```python
from multiagents.monitoring import MonitoringConfig

# Setup monitoring
config = MonitoringConfig.from_file("monitoring.yaml")
logger = config.create_logger()

# Get workflow status
status = await orchestrator.get_status(transaction_id)
print(f"State: {status['state']}")
print(f"Results: {status['step_results']}")
```

## 📋 Worker Context Structure

Workers receive a context dictionary with:

```python
{
    # Original workflow input
    "original_input": {...},
    
    # Previous step results (flattened to top level)
    "key_from_step1": "value1",
    "key_from_step2": "value2",
    
    # Metadata
    "transaction_id": "tx-uuid",
    "workflow_id": "workflow_name",
    "step_name": "current_step"
}
```

## 🔍 Debugging & Troubleshooting

### Check Framework Status
```python
# Worker health
health = await worker_manager.get_health_status()
print(f"Active workers: {health['active_workers']}")

# Workflow status
status = await orchestrator.get_status(transaction_id)
if status['state'] == 'failed':
    print(f"Error: {status['error']}")
```

### Common Issues

1. **"Worker not found"**: Ensure worker is registered before starting
2. **"Redis connection failed"**: Check Redis is running on localhost:6379
3. **"Timeout"**: Increase worker timeout in configuration
4. **"Context missing keys"**: Validate previous steps return expected data

## 🌟 Production Checklist

- [ ] Redis configured with persistence
- [ ] Monitoring setup with structured logging
- [ ] Worker timeouts configured appropriately  
- [ ] Error handling and compensations implemented
- [ ] Health checks enabled
- [ ] Performance metrics tracked

## 📚 Documentation Links

- **Full API Reference**: [docs/api/](api/)
- **Complete Tutorials**: [docs/tutorials/](tutorials/) 
- **Example Applications**: [examples/](../examples/)
- **LLM Integration Guide**: [docs/guides/dspy-integration.md](guides/dspy-integration.md)
- **Architecture Overview**: [docs/guides/architecture.md](guides/architecture.md)

## 🚀 Example Applications

Ready-to-run examples in `/examples/`:

1. **Smart Research Assistant** - LLM research with web search
2. **Interactive Chatbot** - Multi-personality conversational AI
3. **E-commerce Workflow** - Order processing with compensations
4. **Monitoring Demo** - Production observability features

```bash
# Run examples interactively
python run_examples.py

# Or specific example
cd examples/smart_research_assistant
python cli.py
```

---

**Built with ❤️ for the LLM agent community**  
*Making multi-agent AI systems accessible, reliable, and production-ready.*