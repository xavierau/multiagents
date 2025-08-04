# E-commerce Order Processing

A comprehensive MultiAgents framework example demonstrating e-commerce order processing with saga pattern, compensation, and monitoring.

## Quick Start

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Start Redis server:
   ```bash
   redis-server
   ```

3. Run the example:
   ```bash
   python main.py
   ```

## What This Example Shows

- **Complex Workflow**: Multi-step order processing with validation, inventory management, payment, and fulfillment
- **Saga Pattern**: Distributed transaction with automatic rollback on failures
- **Compensation Logic**: Sophisticated rollback mechanisms for each step
- **Error Handling**: Robust error recovery and retry mechanisms
- **Monitoring**: Comprehensive observability with event tracing and metrics
- **Real-world Patterns**: Production-ready patterns for e-commerce systems

## Workflow Steps

1. **Order Validation** - Validate order data and business rules
2. **Inventory Check** - Verify product availability and reserve stock
3. **Payment Processing** - Process payment with external gateway
4. **Order Fulfillment** - Create shipping labels and schedule delivery
5. **Notification** - Send confirmation emails and updates

Each step includes compensation logic for automatic rollback on failures.

## Project Structure

- `main.py` - Application entry point with order scenarios
- `workflows/` - Order processing workflow definitions
- `workers/` - E-commerce worker implementations
- `models/` - Data models for orders, payments, etc.
- `config/` - Configuration files for monitoring and services
- `tests/` - Comprehensive test suite

## Monitoring

The example includes comprehensive monitoring:
- Event lifecycle tracking
- Worker performance metrics  
- Error pattern analysis
- Transaction tracing

View logs in `./logs/{PROJECT_NAME}.log`

## Testing Different Scenarios

The example demonstrates various scenarios:
- ✅ Successful order processing
- ❌ Payment failure with automatic rollback
- ❌ Inventory unavailable with compensation
- ❌ Network timeout with retry logic

## Architecture Benefits

This example showcases MultiAgents framework benefits:
- **Scalability**: Each worker can scale independently
- **Fault Tolerance**: Automatic compensation on failures  
- **Observability**: Complete visibility into distributed transactions
- **Maintainability**: Clean separation of concerns
- **Testability**: Each component can be tested in isolation