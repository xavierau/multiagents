"""
Reusable workflow fixtures for integration tests.
"""
from multiagents.orchestrator import WorkflowBuilder
from multiagents.orchestrator.workflow import WorkflowDefinition


def create_simple_linear_workflow() -> WorkflowDefinition:
    """Create a simple 3-step linear workflow."""
    builder = WorkflowBuilder("simple-linear")
    builder.add_step("step1", "worker1", timeout=30)
    builder.add_step("step2", "worker2", timeout=30)  
    builder.add_step("step3", "worker3", timeout=30)
    return builder.build()


def create_compensation_workflow() -> WorkflowDefinition:
    """Create a workflow with compensation steps."""
    builder = WorkflowBuilder("compensation-workflow")
    
    builder.add_step(
        "reserve_inventory",
        "inventory_worker",
        compensation="restore_inventory",
        timeout=30
    )
    
    builder.add_step(
        "charge_payment", 
        "payment_worker",
        compensation="refund_payment",
        timeout=60
    )
    
    builder.add_step(
        "send_notification",
        "notification_worker",
        timeout=30
    )
    
    return builder.build()


def create_complex_ecommerce_workflow() -> WorkflowDefinition:
    """Create a complex e-commerce order processing workflow."""
    builder = WorkflowBuilder("ecommerce-order")
    
    # Validation phase
    builder.add_step(
        "validate_order",
        "order_validator",
        timeout=30
    )
    
    builder.add_step(
        "validate_customer", 
        "customer_validator",
        timeout=30
    )
    
    # Inventory and pricing
    builder.add_step(
        "check_inventory",
        "inventory_checker",
        compensation="restore_inventory",
        timeout=45
    )
    
    builder.add_step(
        "calculate_pricing",
        "pricing_calculator", 
        timeout=30
    )
    
    # Payment processing
    builder.add_step(
        "process_payment",
        "payment_processor",
        compensation="refund_payment", 
        timeout=90
    )
    
    # Fulfillment
    builder.add_step(
        "create_shipment",
        "shipping_handler",
        compensation="cancel_shipment",
        timeout=60
    )
    
    builder.add_step(
        "send_confirmation",
        "notification_sender",
        timeout=30
    )
    
    return builder.build()


def create_conditional_workflow() -> WorkflowDefinition:
    """Create a workflow with conditional branching."""
    builder = WorkflowBuilder("conditional-workflow")
    
    # Initial step
    builder.add_step("analyze", "analyzer_worker")
    
    # Conditional steps would be handled by the analyzer returning
    # different results that affect subsequent steps
    builder.add_step("high_value_process", "premium_worker")
    builder.add_step("standard_process", "standard_worker")
    
    return builder.build()


def create_parallel_workflow() -> WorkflowDefinition:
    """Create a workflow designed for parallel execution (future feature)."""
    builder = WorkflowBuilder("parallel-workflow")
    
    # Initial step
    builder.add_step("prepare", "preparation_worker")
    
    # These could run in parallel (when feature is implemented)
    builder.add_step("process_a", "worker_a")
    builder.add_step("process_b", "worker_b") 
    builder.add_step("process_c", "worker_c")
    
    # Final aggregation step
    builder.add_step("aggregate", "aggregation_worker")
    
    return builder.build()


def create_retry_workflow() -> WorkflowDefinition:
    """Create a workflow testing retry behavior."""
    builder = WorkflowBuilder("retry-workflow")
    
    builder.add_step(
        "unreliable_step",
        "intermittent_worker",
        timeout=30,
        retry_policy={
            "max_retries": 3,
            "backoff_seconds": 1
        }
    )
    
    builder.add_step("final_step", "reliable_worker")
    
    return builder.build()


def create_timeout_workflow() -> WorkflowDefinition:
    """Create a workflow to test timeout handling."""
    builder = WorkflowBuilder("timeout-workflow")
    
    builder.add_step("quick_step", "fast_worker", timeout=5)
    builder.add_step("slow_step", "slow_worker", timeout=2)  # Will timeout
    builder.add_step("cleanup_step", "cleanup_worker")
    
    return builder.build()


def create_large_workflow() -> WorkflowDefinition:
    """Create a workflow with many steps for load testing."""
    builder = WorkflowBuilder("large-workflow")
    
    # Create 20 sequential steps
    for i in range(20):
        builder.add_step(
            f"step_{i:02d}",
            f"worker_{i:02d}",
            timeout=30
        )
    
    return builder.build()


# Workflow registry for easy access
WORKFLOW_REGISTRY = {
    "simple": create_simple_linear_workflow,
    "compensation": create_compensation_workflow, 
    "ecommerce": create_complex_ecommerce_workflow,
    "conditional": create_conditional_workflow,
    "parallel": create_parallel_workflow,
    "retry": create_retry_workflow,
    "timeout": create_timeout_workflow,
    "large": create_large_workflow,
}


def get_workflow(name: str) -> WorkflowDefinition:
    """Get a workflow by name from the registry."""
    if name not in WORKFLOW_REGISTRY:
        raise ValueError(f"Unknown workflow: {name}. Available: {list(WORKFLOW_REGISTRY.keys())}")
    
    return WORKFLOW_REGISTRY[name]()