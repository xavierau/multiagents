# E-commerce Order Processing Example

This example demonstrates the MultiAgents framework by implementing a complete e-commerce order processing workflow.

## Features Demonstrated

- **Sequential workflow execution** - Orders go through validation, inventory check, payment, and fulfillment
- **Compensation actions** - Automatic rollback on failures (refunds, inventory release)
- **DSPy integration** - AI-powered order confirmation generation
- **Event-driven architecture** - Decoupled workers communicate via events
- **State persistence** - Workflow state survives restarts

## Workflow Steps

1. **Validate Order** - Checks order structure and required fields
2. **Check Inventory** - Verifies product availability (with compensation)
3. **Process Payment** - Charges customer (with refund compensation)
4. **Generate Confirmation** - Uses DSPy to create personalized message
5. **Fulfill Order** - Creates shipping label and tracking
6. **Notify Customer** - Sends final notification

## Running the Example

1. Start Redis:
   ```bash
   redis-server
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Run the example:
   ```bash
   python -m examples.ecommerce_order.main
   ```

## Sample Output

```
🚀 Starting E-commerce Order Processing Example

📡 Starting event bus...

👷 Registering workers...
✓ Registered worker: validate_order
✓ Registered worker: check_inventory
✓ Registered worker: process_payment
...

🔄 Executing workflow...
✓ Workflow started with transaction ID: 550e8400-e29b-41d4-a716-446655440000

📊 Monitoring workflow status...
State: running
Current Step: validate_order
...

✅ Workflow completed with state: completed
```

## Customization

You can modify the workflow by:
- Adding new workers in `workers.py`
- Changing the workflow definition in `workflow.py`
- Implementing conditional branching
- Adding parallel execution steps