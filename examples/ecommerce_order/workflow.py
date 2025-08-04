"""
E-commerce order processing workflow definition.
"""
from multiagents.orchestrator import WorkflowBuilder, WorkflowDefinition


def create_ecommerce_workflow() -> WorkflowDefinition:
    """
    Create the e-commerce order processing workflow.
    
    This workflow demonstrates:
    - Sequential processing steps
    - Conditional branching
    - Compensation actions
    - DSPy integration for intelligent processing
    """
    
    workflow = (WorkflowBuilder("ecommerce_order_processing")
        # Step 1: Validate the order
        .add_step(
            name="validate_order",
            worker_type="validate_order",
            timeout=30
        )
        
        # Step 2: Check inventory availability
        .add_step(
            name="check_inventory",
            worker_type="check_inventory",
            compensation="release_inventory",  # Compensation if later steps fail
            timeout=30
        )
        
        # Step 3: Process payment
        .add_step(
            name="process_payment",
            worker_type="process_payment",
            compensation="refund_payment",  # Compensation if later steps fail
            timeout=60
        )
        
        # Step 4: Generate confirmation (using DSPy)
        .add_step(
            name="generate_confirmation",
            worker_type="generate_order_confirmation",
            timeout=30
        )
        
        # Step 5: Create fulfillment
        .add_step(
            name="fulfill_order",
            worker_type="fulfill_order",
            timeout=30
        )
        
        # Step 6: Notify customer
        .add_step(
            name="notify_customer",
            worker_type="notify_customer",
            timeout=30
        )
        
        .build()
    )
    
    return workflow


def create_advanced_ecommerce_workflow() -> WorkflowDefinition:
    """
    Create an advanced e-commerce workflow with conditional logic.
    
    This demonstrates more complex workflow patterns:
    - Conditional branching based on payment results
    - Parallel execution paths
    - Complex compensation logic
    """
    
    workflow = WorkflowDefinition("advanced_ecommerce_order")
    
    # Define all steps
    from multiagents.orchestrator.workflow import WorkflowStep
    
    # Validation step
    validate_step = WorkflowStep(
        name="validate_order",
        worker_type="validate_order",
        timeout_seconds=30
    )
    workflow.add_step(validate_step)
    
    # Inventory check with compensation
    inventory_step = WorkflowStep(
        name="check_inventory",
        worker_type="check_inventory",
        compensation="release_inventory",
        timeout_seconds=30
    )
    workflow.add_step(inventory_step)
    
    # Payment processing with conditional branching
    payment_step = WorkflowStep(
        name="process_payment",
        worker_type="process_payment",
        compensation="refund_payment",
        timeout_seconds=60,
        next_steps={
            "payment_success": "generate_confirmation",
            "not_payment_success": "payment_retry"
        }
    )
    workflow.add_step(payment_step)
    
    # Payment retry step
    payment_retry_step = WorkflowStep(
        name="payment_retry",
        worker_type="process_payment",
        compensation="refund_payment",
        timeout_seconds=60,
        retry_policy={"max_attempts": 2, "delay_seconds": 5},
        next_steps={
            "payment_success": "generate_confirmation",
            "not_payment_success": "payment_failed_notification"
        }
    )
    workflow.add_step(payment_retry_step)
    
    # Payment failure notification
    payment_failed_step = WorkflowStep(
        name="payment_failed_notification",
        worker_type="notify_customer",
        timeout_seconds=30
    )
    workflow.add_step(payment_failed_step)
    
    # Order confirmation generation
    confirmation_step = WorkflowStep(
        name="generate_confirmation",
        worker_type="generate_order_confirmation",
        timeout_seconds=30
    )
    workflow.add_step(confirmation_step)
    
    # Fulfillment
    fulfillment_step = WorkflowStep(
        name="fulfill_order",
        worker_type="fulfill_order",
        timeout_seconds=30
    )
    workflow.add_step(fulfillment_step)
    
    # Customer notification
    notify_step = WorkflowStep(
        name="notify_customer",
        worker_type="notify_customer",
        timeout_seconds=30
    )
    workflow.add_step(notify_step)
    
    return workflow