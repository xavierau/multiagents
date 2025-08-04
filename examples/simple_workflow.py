"""
Simple workflow example demonstrating the basic framework usage.
"""
import asyncio
from multiagents import (
    Orchestrator, WorkflowBuilder, WorkerManager,
    worker, dspy_worker
)
from multiagents.event_bus.redis_bus import RedisEventBus


# Define workers using decorators
@worker("greet_user")
async def greet_user_worker(context):
    """Simple greeting worker."""
    name = context.get("name", "World")
    return {"greeting": f"Hello, {name}!"}


@worker("add_numbers") 
async def add_numbers_worker(context):
    """Add two numbers."""
    a = context.get("a", 0)
    b = context.get("b", 0)
    return {"sum": a + b}


@dspy_worker("generate_message", signature="greeting, sum -> message")
async def generate_message_worker(context):
    """Use DSPy to generate a personalized message."""
    # DSPy will automatically generate the message based on greeting and sum
    return {"generated_at": "2024-01-01T00:00:00Z"}


async def main():
    """Run a simple workflow example."""
    print("🚀 Simple Workflow Example")
    
    # Setup components
    event_bus = RedisEventBus()
    worker_manager = WorkerManager(event_bus)
    
    # Create workflow
    workflow = (WorkflowBuilder("simple_workflow")
        .add_step("greet", "greet_user")
        .add_step("calculate", "add_numbers")
        .add_step("generate", "generate_message")
        .build())
    
    orchestrator = Orchestrator(workflow, event_bus)
    
    try:
        # Start components
        await event_bus.start()
        
        # Register workers
        worker_manager.register(greet_user_worker)
        worker_manager.register(add_numbers_worker)
        worker_manager.register(generate_message_worker)
        
        await worker_manager.start()
        await orchestrator.start()
        
        # Execute workflow
        input_data = {
            "name": "Alice",
            "a": 10,
            "b": 20
        }
        
        transaction_id = await orchestrator.execute_workflow(
            workflow.get_id(),
            input_data
        )
        
        print(f"Started workflow: {transaction_id}")
        
        # Monitor progress
        while True:
            status = await orchestrator.get_status(transaction_id)
            print(f"Status: {status['state']} - Step: {status['current_step']}")
            
            if status['state'] in ['completed', 'failed']:
                print("Final results:", status['step_results'])
                break
                
            await asyncio.sleep(1)
    
    finally:
        await worker_manager.stop()
        await orchestrator.stop()
        await event_bus.stop()


if __name__ == "__main__":
    asyncio.run(main())