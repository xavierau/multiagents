# Orchestrator API Reference

The orchestrator is the central component that manages workflow execution and state coordination.

## Classes

### `IOrchestrator`

Main orchestrator interface following Interface Segregation Principle.

#### Methods

##### `execute_workflow(workflow_id: str, initial_context: Dict[str, Any]) -> str`

Start a new workflow instance.

**Parameters:**
- `workflow_id` (str): ID of the workflow definition to execute
- `initial_context` (Dict[str, Any]): Initial data for the workflow

**Returns:**
- `str`: Unique transaction ID for this workflow instance

**Raises:**
- `ValidationError`: Invalid workflow_id or context
- `WorkflowExecutionError`: Failed to start workflow

**Example:**
```python
transaction_id = await orchestrator.execute_workflow(
    "order_processing",
    {
        "order_id": "ORDER-123",
        "customer_id": "CUST-456",
        "items": [{"product": "laptop", "qty": 1}]
    }
)
```

##### `get_status(transaction_id: str) -> Dict[str, Any]`

Get current status of a workflow instance.

**Parameters:**
- `transaction_id` (str): ID of the workflow instance

**Returns:**
- `Dict[str, Any]`: Status information including:
  - `state` (str): Current workflow state
  - `current_step` (str): Current executing step
  - `step_results` (Dict): Results from completed steps
  - `error` (Optional[str]): Error message if failed
  - `created_at` (str): Workflow creation timestamp
  - `updated_at` (str): Last update timestamp

**Raises:**
- `ValueError`: Invalid transaction_id
- `StateStoreError`: Failed to retrieve status

**Example:**
```python
status = await orchestrator.get_status(transaction_id)
print(f"State: {status['state']}")
print(f"Current step: {status['current_step']}")

if status['state'] == 'completed':
    for step, result in status['step_results'].items():
        print(f"{step}: {result}")
```

##### `cancel_workflow(transaction_id: str) -> bool`

Cancel a running workflow.

**Parameters:**
- `transaction_id` (str): ID of the workflow instance to cancel

**Returns:**
- `bool`: True if cancelled successfully

**Raises:**
- `ValueError`: Invalid transaction_id
- `WorkflowExecutionError`: Cannot cancel workflow in current state

**Example:**
```python
cancelled = await orchestrator.cancel_workflow(transaction_id)
if cancelled:
    print("Workflow cancelled successfully")
```

### `Orchestrator`

Concrete implementation of `IOrchestrator` with Redis state store.

#### Constructor

```python
Orchestrator(
    workflow: IWorkflowDefinition,
    event_bus: IEventBus,
    state_store: Optional[IStateStore] = None,
    logger: Optional[ILogger] = None
)
```

**Parameters:**
- `workflow` (IWorkflowDefinition): The workflow definition to execute
- `event_bus` (IEventBus): Event bus for communication
- `state_store` (Optional[IStateStore]): State persistence (defaults to Redis)
- `logger` (Optional[ILogger]): Logger instance

#### Additional Methods

##### `start() -> None`

Start the orchestrator and begin listening for events.

**Example:**
```python
await orchestrator.start()
```

##### `stop() -> None`

Stop the orchestrator and cleanup resources.

**Example:**
```python
await orchestrator.stop()
```

##### `get_workflow_definition() -> IWorkflowDefinition`

Get the associated workflow definition.

**Returns:**
- `IWorkflowDefinition`: The workflow definition

## Workflow Definition

### `IWorkflowDefinition`

Interface for defining workflows.

#### Methods

##### `get_id() -> str`

Get the workflow ID.

**Returns:**
- `str`: Unique workflow identifier

##### `get_steps() -> List[WorkflowStep]`

Get all steps in the workflow.

**Returns:**
- `List[WorkflowStep]`: All workflow steps

##### `get_initial_step() -> Optional[WorkflowStep]`

Get the first step to execute.

**Returns:**
- `Optional[WorkflowStep]`: First step or None if empty workflow

##### `get_next_step(current_step: str, context: SagaContext) -> Optional[WorkflowStep]`

Determine the next step based on current step and context.

**Parameters:**
- `current_step` (str): Name of the current step
- `context` (SagaContext): Current saga context with results

**Returns:**
- `Optional[WorkflowStep]`: Next step to execute or None if workflow is complete

### `WorkflowBuilder`

Fluent API for building workflows.

#### Constructor

```python
WorkflowBuilder(workflow_id: str)
```

**Parameters:**
- `workflow_id` (str): Unique identifier for the workflow

#### Methods

##### `add_step(name: str, worker_name: str, compensation: Optional[str] = None) -> WorkflowBuilder`

Add a sequential step to the workflow.

**Parameters:**
- `name` (str): Step name (must be unique within workflow)
- `worker_name` (str): Name of worker to execute
- `compensation` (Optional[str]): Worker to run if compensation needed

**Returns:**
- `WorkflowBuilder`: Self for method chaining

**Example:**
```python
builder.add_step("validate", "validate_order")
       .add_step("process", "process_payment", compensation="refund_payment")
```

##### `add_conditional_step(name: str, worker_name: str, condition: Callable[[SagaContext], bool], compensation: Optional[str] = None) -> WorkflowBuilder`

Add a conditional step that only executes if condition is true.

**Parameters:**
- `name` (str): Step name
- `worker_name` (str): Name of worker to execute
- `condition` (Callable): Function that evaluates context to determine execution
- `compensation` (Optional[str]): Compensation worker name

**Returns:**
- `WorkflowBuilder`: Self for method chaining

**Example:**
```python
builder.add_conditional_step(
    "premium_processing",
    "premium_handler",
    condition=lambda ctx: ctx.get("customer_tier") == "premium"
)
```

##### `add_parallel_steps(steps: List[Dict[str, str]]) -> WorkflowBuilder`

Add steps that can execute in parallel.

**Parameters:**
- `steps` (List[Dict]): List of step definitions with 'name', 'worker_name', optional 'compensation'

**Returns:**
- `WorkflowBuilder`: Self for method chaining

**Example:**
```python
builder.add_parallel_steps([
    {"name": "check_inventory", "worker_name": "inventory_check"},
    {"name": "validate_payment", "worker_name": "payment_validator"}
])
```

##### `build() -> IWorkflowDefinition`

Build the final workflow definition.

**Returns:**
- `IWorkflowDefinition`: Immutable workflow definition

**Example:**
```python
workflow = (WorkflowBuilder("order_processing")
    .add_step("validate", "validate_order")
    .add_step("process", "process_payment", compensation="refund_payment")
    .add_step("fulfill", "fulfill_order")
    .build())
```

## State Store

### `IStateStore`

Interface for persisting workflow state.

#### Methods

##### `save_context(context: SagaContext) -> None`

Save or update a saga context.

##### `load_context(transaction_id: str) -> Optional[SagaContext]`

Load a saga context by transaction ID.

##### `delete_context(transaction_id: str) -> bool`

Delete a saga context.

##### `list_contexts(workflow_id: Optional[str] = None, state: Optional[str] = None) -> List[str]`

List transaction IDs matching criteria.

## Workflow States

Workflows progress through these states:

- **`pending`**: Created but not started
- **`running`**: Currently executing
- **`completed`**: Successfully finished
- **`failed`**: Failed with unrecoverable error
- **`compensated`**: Failed and compensations executed
- **`cancelled`**: Cancelled by user request

## Error Handling

### Automatic Retry

The orchestrator automatically retries failed steps:

```python
# Configure retry behavior (default: 3 retries with exponential backoff)
workflow = (WorkflowBuilder("my_workflow")
    .add_step("risky_step", "might_fail_worker")
    .with_retry_config(max_retries=5, backoff_factor=2.0)
    .build())
```

### Compensation Pattern

When a workflow fails, compensations run in reverse order:

```python
workflow = (WorkflowBuilder("transaction")
    .add_step("reserve", "reserve_inventory", compensation="release_inventory")
    .add_step("charge", "charge_payment", compensation="refund_payment")
    .add_step("ship", "ship_order", compensation="cancel_shipment")
    .build())

# If shipping fails, compensations run: cancel_shipment → refund_payment → release_inventory
```