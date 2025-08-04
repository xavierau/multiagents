# Tutorial: Building Your First Workflow

Learn to build a complete workflow from scratch using the MultiAgents Framework.

## Learning Objectives

By the end of this tutorial, you will:
- Create workers using decorators
- Build sequential workflows  
- Handle worker inputs and outputs
- Monitor workflow execution
- Understand event flow and state management

## Prerequisites

- Completed [Getting Started Guide](../guides/getting-started.md)
- Redis server running
- Basic understanding of Python async/await

## What We're Building

A **Customer Registration Workflow** that:
1. Validates customer data
2. Checks for duplicate accounts
3. Creates the customer record
4. Sends welcome email
5. Updates analytics

```
Input: Customer Data → Validate → Check Duplicates → Create Record → Send Email → Update Analytics → Complete
```

## Step 1: Set Up the Project

Create a new file called `customer_registration.py`:

```python
import asyncio
import re
from datetime import datetime
from typing import Dict, Any

# Import MultiAgents framework
from multiagents import worker
from multiagents.core.factory import create_simple_framework
from multiagents.orchestrator.workflow import WorkflowBuilder
```

## Step 2: Create the Validation Worker

Workers are stateless functions that perform specific tasks. Let's start with data validation:

```python
@worker("validate_customer")
async def validate_customer_worker(context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate customer registration data.
    
    Input context:
        - customer_data: dict with name, email, phone, address
    
    Output:
        - validated_data: cleaned and validated customer data
        - validation_status: "passed" or "failed"
        - validation_errors: list of any validation errors
    """
    customer_data = context.get("customer_data", {})
    errors = []
    validated_data = {}
    
    # Validate required fields
    required_fields = ["name", "email", "phone"]
    for field in required_fields:
        if not customer_data.get(field):
            errors.append(f"Missing required field: {field}")
        else:
            validated_data[field] = customer_data[field].strip()
    
    # Validate email format
    email = customer_data.get("email", "")
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if email and not re.match(email_pattern, email):
        errors.append("Invalid email format")
    
    # Validate phone format (simple check)
    phone = customer_data.get("phone", "")
    if phone and len(re.sub(r'[^\d]', '', phone)) < 10:
        errors.append("Phone number must have at least 10 digits")
    
    # Clean phone number
    if phone:
        validated_data["phone"] = re.sub(r'[^\d]', '', phone)
    
    # Add optional fields if provided
    optional_fields = ["address", "company", "notes"]
    for field in optional_fields:
        if customer_data.get(field):
            validated_data[field] = customer_data[field].strip()
    
    # Add metadata
    validated_data["validated_at"] = datetime.utcnow().isoformat()
    
    return {
        "validated_data": validated_data,
        "validation_status": "passed" if not errors else "failed",
        "validation_errors": errors,
        "field_count": len(validated_data)
    }
```

## Step 3: Create the Duplicate Check Worker

Next, let's check for existing customers:

```python
# Simulate a customer database
EXISTING_CUSTOMERS = [
    {"email": "john.doe@example.com", "phone": "5551234567"},
    {"email": "jane.smith@company.com", "phone": "5559876543"},
]

@worker("check_duplicates")
async def check_duplicates_worker(context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Check if customer already exists in the system.
    
    Input context:
        - validated_data: customer data from validation step
    
    Output:
        - duplicate_status: "none", "email", "phone", or "both"
        - existing_customer: details of existing customer if found
        - is_duplicate: boolean indicating if customer already exists
    """
    validated_data = context["validated_data"]
    email = validated_data.get("email", "").lower()
    phone = validated_data.get("phone", "")
    
    existing_customer = None
    duplicate_types = []
    
    # Check against existing customers
    for customer in EXISTING_CUSTOMERS:
        if customer["email"].lower() == email:
            duplicate_types.append("email")
            existing_customer = customer
        elif customer["phone"] == phone:
            duplicate_types.append("phone") 
            existing_customer = customer
    
    # Determine duplicate status
    if not duplicate_types:
        duplicate_status = "none"
    elif "email" in duplicate_types and "phone" in duplicate_types:
        duplicate_status = "both"
    elif "email" in duplicate_types:
        duplicate_status = "email"
    else:
        duplicate_status = "phone"
    
    return {
        "duplicate_status": duplicate_status,
        "existing_customer": existing_customer,
        "is_duplicate": duplicate_status != "none",
        "duplicate_types": duplicate_types,
        "checked_at": datetime.utcnow().isoformat()
    }
```

## Step 4: Create the Customer Record Worker

Now let's create the customer record:

```python
@worker("create_customer")
async def create_customer_worker(context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create a new customer record in the system.
    
    Input context:
        - validated_data: customer data from validation
        - is_duplicate: whether customer is duplicate (should be False)
    
    Output:
        - customer_id: unique ID for the new customer
        - customer_record: complete customer record
        - creation_status: "success" or "failed"
    """
    validated_data = context["validated_data"]
    is_duplicate = context.get("is_duplicate", False)
    
    # Don't create if duplicate found
    if is_duplicate:
        return {
            "creation_status": "failed",
            "error": "Cannot create duplicate customer",
            "customer_id": None
        }
    
    # Generate customer ID
    customer_id = f"CUST-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
    
    # Create complete customer record
    customer_record = {
        "id": customer_id,
        "created_at": datetime.utcnow().isoformat(),
        "status": "active",
        "source": "registration_workflow",
        **validated_data  # Include all validated data
    }
    
    # Simulate database save
    await asyncio.sleep(0.1)  # Simulate DB write time
    
    # Add to our "database"
    EXISTING_CUSTOMERS.append({
        "email": customer_record["email"],
        "phone": customer_record["phone"]
    })
    
    return {
        "customer_id": customer_id,
        "customer_record": customer_record,
        "creation_status": "success",
        "record_size": len(str(customer_record))
    }
```

## Step 5: Create the Email Worker

Send a welcome email to the new customer:

```python
@worker("send_welcome_email")
async def send_welcome_email_worker(context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Send welcome email to newly registered customer.
    
    Input context:
        - customer_record: complete customer record
        - customer_id: customer's unique ID
    
    Output:
        - email_status: "sent" or "failed"
        - email_id: unique ID for the sent email
        - recipient: email address
    """
    customer_record = context["customer_record"]
    customer_id = context["customer_id"]
    
    recipient_email = customer_record["email"]
    customer_name = customer_record["name"]
    
    # Simulate email composition
    email_content = f"""
    Welcome to our platform, {customer_name}!
    
    Your customer ID is: {customer_id}
    
    Thank you for registering with us. We're excited to have you on board!
    
    Best regards,
    The Team
    """
    
    # Simulate email sending
    await asyncio.sleep(0.2)  # Simulate email service delay
    
    # Generate email ID
    email_id = f"EMAIL-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
    
    # Simulate potential email failures (5% chance)
    import random
    if random.random() < 0.05:
        return {
            "email_status": "failed",
            "error": "Email service temporarily unavailable",
            "recipient": recipient_email,
            "retry_recommended": True
        }
    
    return {
        "email_status": "sent",
        "email_id": email_id,
        "recipient": recipient_email,
        "sent_at": datetime.utcnow().isoformat(),
        "content_length": len(email_content)
    }
```

## Step 6: Create the Analytics Worker

Finally, update our analytics:

```python
@worker("update_analytics")
async def update_analytics_worker(context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Update analytics with new customer registration.
    
    Input context:
        - customer_record: complete customer record
        - email_status: whether email was sent successfully
    
    Output:
        - analytics_updated: boolean indicating success
        - metrics_recorded: list of recorded metrics
    """
    customer_record = context["customer_record"]
    email_status = context.get("email_status", "unknown")
    
    # Record various metrics
    metrics_recorded = []
    
    # Customer registration metric
    metrics_recorded.append({
        "metric": "customer_registration",
        "value": 1,
        "timestamp": datetime.utcnow().isoformat(),
        "customer_id": customer_record["id"]
    })
    
    # Email delivery metric
    if email_status == "sent":
        metrics_recorded.append({
            "metric": "welcome_email_sent", 
            "value": 1,
            "timestamp": datetime.utcnow().isoformat()
        })
    elif email_status == "failed":
        metrics_recorded.append({
            "metric": "welcome_email_failed",
            "value": 1,
            "timestamp": datetime.utcnow().isoformat()
        })
    
    # Customer source tracking
    metrics_recorded.append({
        "metric": "registration_source",
        "source": "workflow",
        "timestamp": datetime.utcnow().isoformat()
    })
    
    # Simulate analytics update
    await asyncio.sleep(0.05)
    
    return {
        "analytics_updated": True,
        "metrics_recorded": metrics_recorded,
        "metrics_count": len(metrics_recorded),
        "updated_at": datetime.utcnow().isoformat()
    }
```

## Step 7: Define the Workflow

Now let's connect all our workers in a sequential workflow:

```python
def create_customer_registration_workflow():
    """Create the customer registration workflow."""
    return (WorkflowBuilder("customer_registration")
        .add_step("validate", "validate_customer")
        .add_step("check_duplicates", "check_duplicates") 
        .add_step("create_customer", "create_customer")
        .add_step("send_email", "send_welcome_email")
        .add_step("update_analytics", "update_analytics")
        .build())
```

## Step 8: Create the Main Execution Function

```python
async def main():
    """Execute the customer registration workflow."""
    print("🚀 Customer Registration Workflow Tutorial")
    print("=" * 50)
    
    # Create workflow
    workflow = create_customer_registration_workflow()
    
    # Set up framework
    event_bus, worker_manager, orchestrator = await create_simple_framework(workflow)
    
    try:
        # Start framework components
        print("📡 Starting framework...")
        await event_bus.start()
        
        # Register all workers
        print("👷 Registering workers...")
        worker_manager.register(validate_customer_worker)
        worker_manager.register(check_duplicates_worker)
        worker_manager.register(create_customer_worker)
        worker_manager.register(send_welcome_email_worker)
        worker_manager.register(update_analytics_worker)
        
        await worker_manager.start()
        await orchestrator.start()
        
        print(f"✓ Registered {len(worker_manager.list_workers())} workers")
        
        # Test data - new customer
        new_customer_data = {
            "customer_data": {
                "name": "Alice Johnson",
                "email": "alice.johnson@example.com",
                "phone": "(555) 123-9999",
                "address": "123 Main St, Anytown, USA",
                "company": "Tech Startup Inc"
            }
        }
        
        # Execute workflow
        print("\n📦 Processing new customer registration...")
        transaction_id = await orchestrator.execute_workflow(
            "customer_registration",
            new_customer_data
        )
        
        print(f"✓ Workflow started with ID: {transaction_id}")
        
        # Monitor progress
        print("\n📊 Monitoring workflow progress...")
        completed_states = {"completed", "failed", "compensated", "cancelled"}
        
        while True:
            status = await orchestrator.get_status(transaction_id)
            
            print(f"State: {status['state']} | Current Step: {status['current_step']}")
            
            if status['state'] in completed_states:
                print(f"\n✅ Workflow {status['state'].upper()}")
                
                if status['step_results']:
                    print("\n📋 Step Results:")
                    for step_name, result in status['step_results'].items():
                        print(f"\n{step_name}:")
                        # Show key result fields
                        if isinstance(result, dict):
                            for key, value in result.items():
                                if not key.startswith('_'):  # Skip internal fields
                                    print(f"  {key}: {value}")
                
                # Show final customer info if successful
                if status['state'] == 'completed' and 'create_customer' in status['step_results']:
                    customer_info = status['step_results']['create_customer']
                    print(f"\n🎉 Customer successfully registered!")
                    print(f"Customer ID: {customer_info['customer_id']}")
                    print(f"Email: {customer_info['customer_record']['email']}")
                
                break
            
            await asyncio.sleep(1)
        
        # Test with duplicate customer
        print("\n" + "="*50)
        print("🔄 Testing duplicate customer detection...")
        
        duplicate_customer_data = {
            "customer_data": {
                "name": "John Doe",
                "email": "john.doe@example.com",  # This email already exists
                "phone": "(555) 999-8888"
            }
        }
        
        duplicate_transaction_id = await orchestrator.execute_workflow(
            "customer_registration",
            duplicate_customer_data
        )
        
        # Monitor duplicate test
        while True:
            status = await orchestrator.get_status(duplicate_transaction_id)
            
            if status['state'] in completed_states:
                print(f"Duplicate test result: {status['state']}")
                
                if 'check_duplicates' in status.get('step_results', {}):
                    duplicate_result = status['step_results']['check_duplicates']
                    print(f"Duplicate detected: {duplicate_result['is_duplicate']}")
                    print(f"Duplicate type: {duplicate_result['duplicate_status']}")
                
                break
            
            await asyncio.sleep(0.5)
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        # Cleanup
        print("\n🧹 Shutting down...")
        await worker_manager.stop()
        await orchestrator.stop()
        await event_bus.stop()
        print("✓ Shutdown complete")

if __name__ == "__main__":
    # Make sure Redis is running
    print("⚠️  Ensure Redis is running: redis-server")
    asyncio.run(main())
```

## Step 9: Run and Test

Save your file and run it:

```bash
python customer_registration.py
```

You should see output like:

```
🚀 Customer Registration Workflow Tutorial
==================================================
📡 Starting framework...
👷 Registering workers...
✓ Registered 5 workers

📦 Processing new customer registration...
✓ Workflow started with ID: TX-20240103-145632-abc123

📊 Monitoring workflow progress...
State: running | Current Step: validate
State: running | Current Step: check_duplicates
State: running | Current Step: create_customer
State: running | Current Step: send_email
State: running | Current Step: update_analytics
State: completed | Current Step: None

✅ Workflow COMPLETED

📋 Step Results:

validate:
  validation_status: passed
  field_count: 5

check_duplicates:
  duplicate_status: none
  is_duplicate: False

create_customer:
  customer_id: CUST-20240103145635
  creation_status: success

send_email:
  email_status: sent
  recipient: alice.johnson@example.com

update_analytics:
  analytics_updated: True
  metrics_count: 3

🎉 Customer successfully registered!
Customer ID: CUST-20240103145635
Email: alice.johnson@example.com
```

## Step 10: Understanding What Happened

Let's trace through what occurred:

1. **Framework Setup**: Event bus, worker manager, and orchestrator were created and started
2. **Worker Registration**: All 5 workers were registered with the worker manager
3. **Workflow Execution**: The orchestrator created a new workflow instance
4. **Sequential Processing**: Each step executed in order:
   - `validate` → data validation passed
   - `check_duplicates` → no duplicates found
   - `create_customer` → new customer record created
   - `send_email` → welcome email sent
   - `update_analytics` → metrics recorded
5. **Completion**: Workflow reached "completed" state

## Verification

### Check the Results

1. **Validation Step**: Ensured all required fields were present and properly formatted
2. **Duplicate Check**: Verified the customer doesn't already exist  
3. **Customer Creation**: Generated a unique customer ID and record
4. **Email Notification**: Simulated sending a welcome email
5. **Analytics Update**: Recorded registration metrics

### Test Error Scenarios

Try modifying the input data to test error handling:

```python
# Test missing required field
invalid_data = {
    "customer_data": {
        "name": "Test User",
        # Missing email and phone
    }
}

# Test invalid email format
invalid_email_data = {
    "customer_data": {
        "name": "Test User",
        "email": "invalid-email",
        "phone": "555-123-4567"
    }
}
```

## Common Issues

### Redis Connection Error
```
ConnectionError: Error 61 connecting to localhost:6379
```
**Solution**: Start Redis server
```bash
redis-server
```

### Worker Not Found Error
```
ValueError: Worker 'validate_customer' not found
```
**Solution**: Ensure workers are registered before starting the worker manager

### Workflow Fails at Validation
If validation fails, check:
- Input data format
- Required fields are present
- Email/phone format validation

## What You Learned

✅ **Worker Creation**: How to create stateless workers with the `@worker` decorator  
✅ **Data Flow**: How context data flows between workflow steps  
✅ **Workflow Building**: How to define sequential workflows with `WorkflowBuilder`  
✅ **Error Handling**: How validation errors are handled and propagated  
✅ **Monitoring**: How to track workflow progress and view results  
✅ **Framework Lifecycle**: How to start, execute, and stop framework components  

## Next Steps

Now that you understand basic workflows, continue with:

1. **[Error Handling Tutorial](error-handling.md)** - Add compensations and retry logic
2. **[Monitoring Setup Tutorial](monitoring-setup.md)** - Implement comprehensive observability
3. **[DSPy Workers Tutorial](dspy-workers.md)** - Create LLM-powered workers

## Complete Code

The complete working code is available in this tutorial. Copy all the code blocks into a single file to run the full example.

This foundational knowledge prepares you for building more complex, production-ready workflows!