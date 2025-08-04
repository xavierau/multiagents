from typing import Callable, Dict, Any, Optional, Union, Awaitable
from functools import wraps
import inspect
import asyncio

from .base_worker import BaseWorker, WorkerConfig
from .interface import IWorker


class FunctionWorker(BaseWorker):
    """Worker implementation that wraps a function."""

    def __init__(self, config: WorkerConfig, func: Callable):
        super().__init__(config)
        self.func = func
        self.is_async = inspect.iscoroutinefunction(func)

    async def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the wrapped function."""
        if self.is_async:
            result = await self.func(context)
        else:
            # Run sync function in executor to avoid blocking
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(None, self.func, context)

        # Ensure result is a dict
        if not isinstance(result, dict):
            result = {"result": result}

        return result

    def validate_input(self, context: Dict[str, Any]) -> bool:
        """Validate based on function signature."""
        sig = inspect.signature(self.func)
        
        # Check if function expects specific parameters
        params = list(sig.parameters.keys())
        
        # If function takes **kwargs or a single dict parameter, any context is valid
        if any(p.kind == inspect.Parameter.VAR_KEYWORD for p in sig.parameters.values()):
            return True
            
        # If function has exactly one parameter (the context dict), accept any valid dict
        if len(params) == 1:
            return True

        # For functions with multiple parameters, check that context contains required parameters
        required_params = [
            name for name, param in sig.parameters.items()
            if param.default == inspect.Parameter.empty
            and param.kind not in (inspect.Parameter.VAR_POSITIONAL, inspect.Parameter.VAR_KEYWORD)
        ]
        
        return all(param in context for param in required_params)


def worker(
    worker_type: str,
    *,
    timeout: int = 300,
    retry_attempts: int = 3,
    retry_delay: int = 1,
    validate_input: Optional[Callable[[Dict[str, Any]], bool]] = None,
    validate_output: Optional[Callable[[Dict[str, Any]], bool]] = None,
) -> Callable:
    """
    Decorator to register a function as a worker.
    
    Args:
        worker_type: Unique identifier for this worker type
        timeout: Timeout in seconds
        retry_attempts: Number of retry attempts on failure
        retry_delay: Delay between retries in seconds
        validate_input: Optional input validation function
        validate_output: Optional output validation function
        
    Example:
        @worker("process_payment")
        async def process_payment(context: dict) -> dict:
            amount = context["amount"]
            # Process payment...
            return {"status": "success", "transaction_id": "123"}
    """
    def decorator(func: Union[Callable, Awaitable]) -> IWorker:
        # Create worker config
        config = WorkerConfig(
            worker_type=worker_type,
            timeout_seconds=timeout,
            retry_attempts=retry_attempts,
            retry_delay_seconds=retry_delay,
        )

        # Create function worker
        worker_instance = FunctionWorker(config, func)

        # Override validation if provided
        if validate_input:
            worker_instance.validate_input = validate_input
        if validate_output:
            worker_instance.validate_output = validate_output

        # Store original function for access
        worker_instance.original_function = func

        # Register worker if registry is available
        # This would be done by the framework when workers are loaded

        return worker_instance

    return decorator


def dspy_worker(
    worker_type: str,
    *,
    signature: Optional[str] = None,
    timeout: int = 300,
    retry_attempts: int = 3,
    model: Optional[str] = None,
) -> Callable:
    """
    Decorator for creating a DSPy-powered worker.
    
    Args:
        worker_type: Unique identifier for this worker type
        signature: DSPy signature string (e.g., "question -> answer")
        timeout: Timeout in seconds
        retry_attempts: Number of retry attempts
        model: LLM model to use
        
    Example:
        @dspy_worker("summarize_text", signature="text -> summary")
        async def summarize(context: dict) -> dict:
            # The DSPy agent is automatically available
            return {"summary": context["summary"]}  # DSPy handles the generation
    """
    def decorator(func: Callable) -> IWorker:
        from .dspy_wrapper import DSPyAgent, DSPyConfig
        
        # Create DSPy agent with default config (which will load API key from environment)
        dspy_config = DSPyConfig() if model is None else DSPyConfig(model=model)
        dspy_agent = DSPyAgent(dspy_config)
        
        # Create signature if provided
        if signature:
            input_desc, output_desc = signature.split("->")
            sig = dspy_agent.create_signature(input_desc.strip(), output_desc.strip())
        
        # Wrap function to inject DSPy functionality
        @wraps(func)
        async def wrapped(context: Dict[str, Any]) -> Dict[str, Any]:
            # If signature is provided, use DSPy to generate output
            if signature and sig:
                result = dspy_agent.predict(sig, **context)
                # Merge with any additional processing from the original function
                if inspect.iscoroutinefunction(func):
                    additional = await func(context)
                else:
                    additional = func(context)
                result.update(additional)
                return result
            else:
                # Just call the function with DSPy agent available
                context["_dspy_agent"] = dspy_agent
                if inspect.iscoroutinefunction(func):
                    return await func(context)
                else:
                    return func(context)
        
        # Create worker config
        config = WorkerConfig(
            worker_type=worker_type,
            timeout_seconds=timeout,
            retry_attempts=retry_attempts,
        )
        
        # Create and return worker
        return FunctionWorker(config, wrapped)
    
    return decorator