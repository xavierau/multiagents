from typing import Callable, Dict, Any, Optional, Union, Awaitable, List
from functools import wraps
import inspect
import asyncio
from dataclasses import dataclass

from .base_worker import BaseWorker, WorkerConfig
from .interface import IWorker
from .dspy_modules import WorkerTool, SimpleSignatureModule, ToolEnabledWorkerModule


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
    tools: Optional[List[Union[Callable, WorkerTool]]] = None,
    reasoning: str = "predict",
    timeout: int = 300,
    retry_attempts: int = 3,
    model: Optional[str] = None,
    max_iters: int = 5,
    enable_optimization: bool = False,
) -> Callable:
    """
    Enhanced decorator for creating DSPy-powered workers with tool support.
    
    Args:
        worker_type: Unique identifier for this worker type
        signature: DSPy signature string (e.g., "question -> answer")
        tools: List of tools/functions the worker can use
        reasoning: Type of reasoning (predict, chain_of_thought, program_of_thought, react, codeact)
        timeout: Timeout in seconds
        retry_attempts: Number of retry attempts
        model: LLM model to use
        max_iters: Maximum iterations for ReAct/CodeAct
        enable_optimization: Whether to enable optimization (future)
        
    Examples:
        # Simple signature-based worker (backward compatible)
        @dspy_worker("summarize_text", signature="text -> summary")
        async def summarize(context: dict) -> dict:
            return {"processed": True}
        
        # Tool-enabled worker with ReAct
        @dspy_worker("research_agent", 
                    signature="question -> answer", 
                    tools=[search_web, lookup_db],
                    reasoning="react")
        async def research(context: dict) -> dict:
            return {"research_complete": True}
    """
    def decorator(func: Callable) -> IWorker:
        # Create enhanced worker configuration
        config = DSPyWorkerConfig(
            worker_type=worker_type,
            signature=signature,
            tools=tools or [],
            reasoning=reasoning,
            model=model,
            timeout=timeout,
            retry_attempts=retry_attempts,
            max_iters=max_iters,
            enable_optimization=enable_optimization,
        )
        
        return DSPyModuleWorker(config, func)
    
    return decorator


@dataclass
class DSPyWorkerConfig:
    """Enhanced configuration for DSPy workers with tool support."""
    worker_type: str
    signature: Optional[str] = None
    tools: List[Union[Callable, WorkerTool]] = None
    reasoning: str = "predict"  # predict, chain_of_thought, program_of_thought, react, codeact
    model: Optional[str] = None
    timeout: int = 300
    retry_attempts: int = 3
    max_iters: int = 5  # for ReAct/CodeAct
    # Future optimization settings
    enable_optimization: bool = False
    optimization_method: str = "bootstrap_few_shot"
    collect_training_data: bool = True
    
    def __post_init__(self):
        if self.tools is None:
            self.tools = []


class DSPyModuleWorker(BaseWorker):
    """
    Enhanced worker that supports both signatures and tools via DSPy modules.
    This replaces the old FunctionWorker approach for DSPy workers.
    """
    
    def __init__(self, config: DSPyWorkerConfig, user_func: Callable):
        # Create standard WorkerConfig for base class
        base_config = WorkerConfig(
            worker_type=config.worker_type,
            timeout_seconds=config.timeout,
            retry_attempts=config.retry_attempts,
        )
        super().__init__(base_config)
        
        self.dspy_config = config
        self.user_func = user_func
        
        # Create the appropriate DSPy module
        self.dspy_module = self._create_dspy_module()
        
        # Configure DSPy if model specified
        if config.model:
            self._configure_dspy()
        
        # Performance tracking for future optimization
        self.execution_history: List[Dict[str, Any]] = []
        self.success_count = 0
        self.total_count = 0
    
    def _create_dspy_module(self):
        """Create the appropriate DSPy module based on configuration."""
        if not self.dspy_config.signature:
            # User must provide their own DSPy module logic
            return None
        
        # Choose module type based on tools and reasoning
        if self.dspy_config.tools and self.dspy_config.reasoning in ["react", "codeact"]:
            # Tool-enabled module
            return ToolEnabledWorkerModule(
                signature=self.dspy_config.signature,
                tools=self.dspy_config.tools,
                reasoning_type=self.dspy_config.reasoning,
                max_iters=self.dspy_config.max_iters,
                config=self.dspy_config.__dict__
            )
        else:
            # Simple signature module
            return SimpleSignatureModule(
                signature=self.dspy_config.signature,
                reasoning_type=self.dspy_config.reasoning,
                config=self.dspy_config.__dict__
            )
    
    def _configure_dspy(self):
        """Configure DSPy with the specified model."""
        try:
            import dspy
            lm = dspy.LM(model=self.dspy_config.model)
            dspy.configure(lm=lm)
        except Exception as e:
            print(f"Warning: Could not configure DSPy model {self.dspy_config.model}: {e}")
    
    async def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the DSPy module-based worker with tool support."""
        self.total_count += 1
        
        try:
            result = {}
            
            # Execute DSPy module if available
            if self.dspy_module:
                # Extract inputs for DSPy signature
                dspy_inputs = {k: v for k, v in context.items() if not k.startswith('_')}
                
                # Execute the DSPy module (with tools if configured)
                dspy_result = self.dspy_module(**dspy_inputs)
                
                # Convert DSPy prediction to dict
                for field_name in dir(dspy_result):
                    if not field_name.startswith('_') and hasattr(dspy_result, field_name):
                        value = getattr(dspy_result, field_name)
                        if not callable(value):
                            result[field_name] = value
            else:
                # Fallback: provide DSPy agent like the old implementation
                from .dspy_wrapper import DSPyAgent, DSPyConfig
                dspy_config = DSPyConfig() if self.dspy_config.model is None else DSPyConfig(model=self.dspy_config.model)
                dspy_agent = DSPyAgent(dspy_config)
                context["_dspy_agent"] = dspy_agent
            
            # Execute user function for additional processing
            context.update(result)
            context['_dspy_result'] = result  # Provide access to DSPy result
            
            if inspect.iscoroutinefunction(self.user_func):
                additional = await self.user_func(context)
            else:
                # Run sync function in executor to avoid blocking
                loop = asyncio.get_event_loop()
                additional = await loop.run_in_executor(None, self.user_func, context)
            
            # Merge results
            if isinstance(additional, dict):
                result.update(additional)
            elif additional is not None:
                result["result"] = additional
            
            # Track successful execution
            if self.dspy_config.collect_training_data:
                self._collect_training_example(context, result)
            
            self.success_count += 1
            return result
            
        except Exception as e:
            # Track failed execution
            self.execution_history.append({
                "inputs": context,
                "success": False,
                "error": str(e),
                "timestamp": "now"  # Use actual timestamp in production
            })
            raise
    
    def _collect_training_example(self, inputs: Dict[str, Any], outputs: Dict[str, Any]):
        """Collect training examples for future optimization."""
        # Clean inputs/outputs for DSPy signature fields
        clean_inputs = {k: v for k, v in inputs.items() if not k.startswith('_')}
        
        # Add to DSPy module if available
        if self.dspy_module and hasattr(self.dspy_module, 'add_training_example'):
            self.dspy_module.add_training_example(clean_inputs, outputs)
        
        # Store execution history
        self.execution_history.append({
            "inputs": clean_inputs,
            "outputs": outputs,
            "success": True,
            "timestamp": "now",  # Use actual timestamp in production
            "tools_used": [tool.name if isinstance(tool, WorkerTool) else getattr(tool, '__name__', str(tool)) 
                          for tool in self.dspy_config.tools]
        })
    
    def get_available_tools(self) -> List[str]:
        """Get list of available tool names."""
        tools = []
        for tool in self.dspy_config.tools:
            if isinstance(tool, WorkerTool):
                tools.append(tool.name)
            elif hasattr(tool, '__name__'):
                tools.append(tool.__name__)
            else:
                tools.append(str(tool))
        return tools
    
    def get_optimization_data(self) -> Dict[str, Any]:
        """Get data for future optimization."""
        return {
            "training_examples": self.dspy_module.get_training_examples() if self.dspy_module else [],
            "execution_history": self.execution_history,
            "success_rate": self.success_count / max(self.total_count, 1),
            "total_executions": self.total_count,
            "available_tools": self.get_available_tools(),
        }
    
    def validate_input(self, context: Dict[str, Any]) -> bool:
        """Validate input based on DSPy signature or function signature."""
        if self.dspy_module and hasattr(self.dspy_module, 'dspy_signature'):
            # Validate against DSPy signature input fields
            try:
                input_fields = [field for field in dir(self.dspy_module.dspy_signature) if not field.startswith('_')]
                # For now, just check that we have some input
                return bool(context)
            except:
                return True  # Default to valid if we can't validate
        else:
            # Use parent class validation
            return super().validate_input(context)