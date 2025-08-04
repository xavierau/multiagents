import dspy
from typing import Dict, Any, Optional, List, Callable, Type
from dataclasses import dataclass
from pydantic import BaseModel, Field
import structlog
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

logger = structlog.get_logger()


@dataclass
class DSPyConfig:
    """Configuration for DSPy integration."""
    model: str = "gemini/gemini-1.5-flash"
    api_key: Optional[str] = None
    temperature: float = 0.7
    max_tokens: int = 1000
    retry_attempts: int = 3


class DSPySignature(BaseModel):
    """Base class for defining DSPy signatures with Pydantic."""
    class Config:
        extra = "forbid"


class DSPyAgent:
    """
    Wrapper for DSPy to abstract LLM interactions.
    Provides clean interface for workers to use LLM capabilities.
    """

    def __init__(self, config: Optional[DSPyConfig] = None):
        self.config = config or DSPyConfig()
        self._initialize_dspy()
        self._signatures: Dict[str, Type[dspy.Signature]] = {}
        self._modules: Dict[str, dspy.Module] = {}

    def _initialize_dspy(self) -> None:
        """Initialize DSPy with configuration."""
        # Get API key from config or environment
        api_key = self.config.api_key
        if not api_key:
            if self.config.model.startswith("gpt") or self.config.model.startswith("openai"):
                api_key = os.getenv("OPENAI_API_KEY")
            elif self.config.model.startswith("gemini") or self.config.model.startswith("google"):
                api_key = os.getenv("GOOGLE_API_KEY")
        
        # Debug logging
        logger.info("Initializing DSPy", 
                   model=self.config.model, 
                   has_api_key=bool(api_key),
                   api_key_source="config" if self.config.api_key else "environment")
        
        if self.config.model.startswith("gpt") or self.config.model.startswith("openai"):
            lm = dspy.LM(
                model=self.config.model,
                api_key=api_key,
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens,
            )
        elif self.config.model.startswith("gemini") or self.config.model.startswith("google"):
            lm = dspy.LM(
                model=self.config.model,
                api_key=api_key,
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens,
            )
        else:
            # Default fallback
            lm = dspy.LM(
                model=self.config.model,
                api_key=api_key,
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens,
            )
        
        logger.info("Configuring DSPy with LM", 
                   lm_model=getattr(lm, 'model', 'unknown'),
                   lm_type=type(lm).__name__)
        
        dspy.configure(lm=lm)

    def create_signature(self, input_desc: str, output_desc: str, 
                        name: Optional[str] = None) -> Type[dspy.Signature]:
        """
        Create a DSPy signature for structured outputs.
        
        Args:
            input_desc: Description of input fields
            output_desc: Description of output fields
            name: Optional name to cache the signature
            
        Returns:
            DSPy signature class
        """
        signature = dspy.Signature(f"{input_desc} -> {output_desc}")
        
        if name:
            self._signatures[name] = signature
            
        return signature

    def create_chain(self, *modules: dspy.Module, name: Optional[str] = None) -> dspy.Module:
        """
        Create a chain of DSPy modules.
        
        Args:
            modules: DSPy modules to chain
            name: Optional name to cache the chain
            
        Returns:
            Chained DSPy module
        """
        if len(modules) == 1:
            chain = modules[0]
        else:
            chain = dspy.ChainOfThought(*modules)
        
        if name:
            self._modules[name] = chain
            
        return chain

    def predict(self, signature: Type[dspy.Signature], **kwargs) -> Dict[str, Any]:
        """
        Make a prediction using a signature.
        
        Args:
            signature: DSPy signature to use
            **kwargs: Input fields for the signature
            
        Returns:
            Dictionary of output fields
        """
        predictor = dspy.Predict(signature)
        result = predictor(**kwargs)
        
        # Convert to dict for easier handling
        output_dict = {}
        for field in signature.output_fields:
            if hasattr(result, field):
                output_dict[field] = getattr(result, field)
                
        return output_dict

    def chain_of_thought(self, question: str, signature: Optional[Type[dspy.Signature]] = None) -> str:
        """
        Use chain of thought reasoning.
        
        Args:
            question: Question to reason about
            signature: Optional signature to use
            
        Returns:
            Reasoned answer
        """
        if signature is None:
            signature = self.create_signature("question", "answer")
            
        cot = dspy.ChainOfThought(signature)
        result = cot(question=question)
        
        return result.answer if hasattr(result, 'answer') else str(result)

    def react_agent(self, task: str, tools: List[Callable], max_steps: int = 5) -> Dict[str, Any]:
        """
        Create a ReAct-style agent with tools.
        
        Args:
            task: Task description
            tools: List of callable tools
            max_steps: Maximum reasoning steps
            
        Returns:
            Result with reasoning trace and final answer
        """
        # This is a simplified version - full implementation would integrate with DSPy's ReAct
        thoughts = []
        
        for step in range(max_steps):
            # Generate thought
            thought_sig = self.create_signature("task, previous_thoughts", "thought, action, tool")
            thought_result = self.predict(
                thought_sig,
                task=task,
                previous_thoughts="\n".join(thoughts)
            )
            
            thoughts.append(f"Thought: {thought_result.get('thought', '')}")
            
            # Check if task is complete
            if "final answer" in thought_result.get('thought', '').lower():
                break
                
            # Execute tool if specified
            if thought_result.get('tool') and thought_result.get('action'):
                # Match tool and execute
                # This would need proper tool matching logic
                pass
        
        return {
            "reasoning_trace": thoughts,
            "final_answer": thoughts[-1] if thoughts else "No answer generated"
        }

    def optimize_chain(self, examples: List[Dict[str, Any]], 
                      metric: Callable[[Any, Any], float],
                      modules: List[dspy.Module]) -> dspy.Module:
        """
        Use DSPy's optimization capabilities to improve a chain.
        
        Args:
            examples: Training examples
            metric: Evaluation metric function
            modules: Modules to optimize
            
        Returns:
            Optimized module chain
        """
        # Create dataset
        trainset = []
        for example in examples:
            # Convert to DSPy example format
            dspy_example = dspy.Example(**example)
            trainset.append(dspy_example)
        
        # Set up optimizer
        optimizer = dspy.BootstrapFewShotWithRandomSearch(
            metric=metric,
            max_bootstrapped_demos=4,
            max_labeled_demos=16,
        )
        
        # Create program to optimize
        if len(modules) == 1:
            program = modules[0]
        else:
            program = dspy.ChainOfThought(*modules)
        
        # Optimize
        optimized_program = optimizer.compile(program, trainset=trainset)
        
        return optimized_program

    def create_structured_output(self, output_model: Type[BaseModel], 
                               prompt: str, **kwargs) -> BaseModel:
        """
        Generate structured output using a Pydantic model.
        
        Args:
            output_model: Pydantic model for output structure
            prompt: Prompt template
            **kwargs: Values to fill in the prompt
            
        Returns:
            Instance of the output model
        """
        # Create signature from Pydantic model
        output_fields = ", ".join(output_model.__fields__.keys())
        signature = self.create_signature(
            "input_text",
            output_fields
        )
        
        # Format prompt
        formatted_prompt = prompt.format(**kwargs)
        
        # Predict
        result = self.predict(signature, input_text=formatted_prompt)
        
        # Convert to Pydantic model
        return output_model(**result)

    def batch_process(self, items: List[Dict[str, Any]], 
                     signature: Type[dspy.Signature],
                     parallel: bool = False) -> List[Dict[str, Any]]:
        """
        Process multiple items with the same signature.
        
        Args:
            items: List of input dictionaries
            signature: DSPy signature to use
            parallel: Whether to process in parallel (requires async)
            
        Returns:
            List of output dictionaries
        """
        results = []
        
        for item in items:
            try:
                result = self.predict(signature, **item)
                results.append(result)
            except Exception as e:
                logger.error(f"Error processing item: {e}", item=item)
                results.append({"error": str(e)})
        
        return results