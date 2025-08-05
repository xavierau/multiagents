"""
DSPy Module Classes for Enhanced Worker Support
==============================================

This module provides DSPy module classes that support tools and different reasoning patterns.
"""

import dspy
from typing import Dict, Any, Optional, Callable, List, Union
import inspect
import asyncio


class WorkerTool:
    """
    Wrapper for tools that can be used in DSPy workers.
    Handles both sync and async functions.
    """
    
    def __init__(self, func: Callable, name: Optional[str] = None):
        self.func = func
        self.name = name or func.__name__
        self.is_async = inspect.iscoroutinefunction(func)
        
        # Extract function signature for DSPy
        self.signature = inspect.signature(func)
        self.docstring = func.__doc__ or f"Tool: {self.name}"
        
        # Create DSPy-compatible tool
        self.dspy_tool = self._create_dspy_tool()
    
    def _create_dspy_tool(self):
        """Create DSPy-compatible tool from function."""
        if self.is_async:
            # For async functions, wrap in sync wrapper for DSPy
            def sync_wrapper(*args, **kwargs):
                try:
                    loop = asyncio.get_event_loop()
                    return loop.run_until_complete(self.func(*args, **kwargs))
                except RuntimeError:
                    # Create new event loop if none exists
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    try:
                        return loop.run_until_complete(self.func(*args, **kwargs))
                    finally:
                        loop.close()
            
            sync_wrapper.__doc__ = self.docstring
            sync_wrapper.__name__ = self.name
            sync_wrapper.__annotations__ = self.func.__annotations__
            return sync_wrapper
        else:
            return self.func
    
    async def acall(self, *args, **kwargs):
        """Async call for tools."""
        if self.is_async:
            return await self.func(*args, **kwargs)
        else:
            return self.func(*args, **kwargs)
    
    def call(self, *args, **kwargs):
        """Sync call for tools."""
        if self.is_async:
            return asyncio.run(self.func(*args, **kwargs))
        else:
            return self.func(*args, **kwargs)


class WorkerModule(dspy.Module):
    """
    Base class for all DSPy worker modules.
    This provides the interface for optimization-ready modules.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__()
        self.config = config or {}
        self._training_examples: List[dspy.Example] = []
        self._optimization_metrics: Dict[str, float] = {}
    
    def add_training_example(self, inputs: Dict[str, Any], expected_output: Dict[str, Any]):
        """Add training examples for future optimization."""
        try:
            example = dspy.Example(**inputs, **expected_output).with_inputs(*inputs.keys())
            self._training_examples.append(example)
        except Exception as e:
            # Log the error but don't fail the worker
            print(f"Warning: Could not add training example: {e}")
    
    def get_training_examples(self) -> List[dspy.Example]:
        """Get collected training examples."""
        return self._training_examples
    
    def update_metrics(self, metrics: Dict[str, float]):
        """Update performance metrics."""
        self._optimization_metrics.update(metrics)


class SimpleSignatureModule(WorkerModule):
    """
    DSPy module for simple signature-based workers (no tools).
    """
    
    def __init__(self, signature: str, reasoning_type: str = "predict", config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.signature = signature
        self.reasoning_type = reasoning_type
        
        # Create DSPy signature
        self.dspy_signature = dspy.Signature(signature)
        
        # Choose reasoning method
        if reasoning_type == "chain_of_thought":
            self.predictor = dspy.ChainOfThought(self.dspy_signature)
        elif reasoning_type == "program_of_thought":
            self.predictor = dspy.ProgramOfThought(self.dspy_signature)
        else:  # default to predict
            self.predictor = dspy.Predict(self.dspy_signature)
    
    def forward(self, **kwargs) -> dspy.Prediction:
        """Execute signature."""
        return self.predictor(**kwargs)


class ToolEnabledWorkerModule(WorkerModule):
    """
    DSPy module that can use tools via ReAct or CodeAct pattern.
    """
    
    def __init__(self, signature: str, tools: List[Union[Callable, WorkerTool]], 
                 reasoning_type: str = "react", max_iters: int = 5, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.signature = signature
        self.tools = self._prepare_tools(tools)
        self.reasoning_type = reasoning_type
        self.max_iters = max_iters
        
        # Create DSPy signature
        self.dspy_signature = dspy.Signature(signature)
        
        # Choose reasoning method with tools
        if reasoning_type == "react":
            self.predictor = dspy.ReAct(self.dspy_signature, tools=self.tools, max_iters=max_iters)
        elif reasoning_type == "codeact":
            self.predictor = dspy.CodeAct(self.dspy_signature, tools=self.tools)
        else:
            # Fallback to ChainOfThought without tools
            self.predictor = dspy.ChainOfThought(self.dspy_signature)
    
    def _prepare_tools(self, tools: List[Union[Callable, WorkerTool]]) -> List[Callable]:
        """Prepare tools for DSPy usage."""
        dspy_tools = []
        for tool in tools:
            if isinstance(tool, WorkerTool):
                dspy_tools.append(tool.dspy_tool)
            else:
                # Wrap raw function in WorkerTool
                worker_tool = WorkerTool(tool)
                dspy_tools.append(worker_tool.dspy_tool)
        return dspy_tools
    
    def forward(self, **kwargs) -> dspy.Prediction:
        """Execute with tools using ReAct or CodeAct."""
        return self.predictor(**kwargs)


def tool(name: Optional[str] = None):
    """
    Decorator to register a function as a worker tool.
    
    Args:
        name: Optional name for the tool
    
    Example:
        @tool("search_database")
        def search_db(query: str) -> List[str]:
            '''Search the database for relevant information.'''
            return ["result1", "result2"]
    """
    def decorator(func: Callable) -> WorkerTool:
        return WorkerTool(func, name)
    return decorator