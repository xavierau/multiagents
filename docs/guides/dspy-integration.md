# DSPy Integration Guide

Comprehensive guide to integrating Large Language Models with the MultiAgents Framework using DSPy.

## Table of Contents

- [DSPy Overview](#dspy-overview)
- [Setup and Configuration](#setup-and-configuration)
- [Creating DSPy Workers](#creating-dspy-workers)
- [Advanced Patterns](#advanced-patterns)
- [Optimization](#optimization)
- [Production Considerations](#production-considerations)
- [Best Practices](#best-practices)

## DSPy Overview

DSPy (Declarative Self-improving Python) is a framework for programming with foundation models. It provides:

- **Structured Prompting**: Define input/output schemas
- **Automatic Optimization**: Improve prompts through examples
- **Modular Composition**: Chain multiple LLM calls
- **Multiple LLM Support**: Works with various LLM providers

### DSPy in MultiAgents Framework

```
┌─────────────────────────────────────────────────────────────────────┐
│                    DSPY INTEGRATION ARCHITECTURE                    │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐ │
│  │   @dspy_worker  │    │  DSPy Signature │    │   LLM Provider  │ │
│  │    Decorator    │    │   Definition    │    │                 │ │
│  │                 │    │                 │    │ • OpenAI        │ │
│  │ • Input prep    │───►│ • Input fields  │───►│ • Anthropic     │ │
│  │ • Context       │    │ • Output fields │    │ • Local models  │ │
│  │ • Post-process  │    │ • Constraints   │    │ • Azure OpenAI  │ │
│  └─────────────────┘    └─────────────────┘    └─────────────────┘ │
│           │                       │                       │         │
│           └───────────────────────┼───────────────────────┘         │
│                                   │                                 │
│                    ┌─────────────────┐                              │
│                    │ FRAMEWORK CORE  │                              │
│                    │                 │                              │
│                    │ • Event routing │                              │
│                    │ • Error handling│                              │
│                    │ • Monitoring    │                              │
│                    │ • State mgmt    │                              │
│                    └─────────────────┘                              │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

## Setup and Configuration

### Installation

```bash
pip install dspy-ai openai anthropic
```

### Basic Configuration

```python
import dspy
import os

# OpenAI Configuration
openai_lm = dspy.OpenAI(
    model="gpt-3.5-turbo",
    api_key=os.getenv("OPENAI_API_KEY"),
    max_tokens=500,
    temperature=0.7
)

# Anthropic Configuration  
anthropic_lm = dspy.Anthropic(
    model="claude-3-sonnet-20240229",
    api_key=os.getenv("ANTHROPIC_API_KEY"),
    max_tokens=500
)

# Azure OpenAI Configuration
azure_lm = dspy.AzureOpenAI(
    api_base=os.getenv("AZURE_OPENAI_ENDPOINT"),
    api_key=os.getenv("AZURE_OPENAI_KEY"),
    api_version="2023-12-01-preview",
    model="gpt-35-turbo"
)

# Local Model Configuration (using Ollama)
local_lm = dspy.OllamaLocal(
    model="llama2",
    base_url="http://localhost:11434"
)

# Configure DSPy
dspy.settings.configure(lm=openai_lm)
```

### Environment-Specific Configuration

```python
def configure_dspy_for_environment():
    """Configure DSPy based on environment."""
    
    env = os.getenv("ENVIRONMENT", "development")
    
    if env == "production":
        # Production: Use reliable, fast models
        lm = dspy.OpenAI(
            model="gpt-3.5-turbo",
            api_key=os.getenv("OPENAI_API_KEY"),
            max_tokens=300,
            temperature=0.3,  # Lower temperature for consistency
            request_timeout=30
        )
    
    elif env == "staging":
        # Staging: Balance cost and performance
        lm = dspy.OpenAI(
            model="gpt-3.5-turbo",
            api_key=os.getenv("OPENAI_API_KEY"),
            max_tokens=400,
            temperature=0.5
        )
    
    else:  # development
        # Development: Use cheaper or local models
        if os.getenv("USE_LOCAL_MODEL", "false").lower() == "true":
            lm = dspy.OllamaLocal(model="llama2")
        else:
            lm = dspy.OpenAI(
                model="gpt-3.5-turbo",
                api_key=os.getenv("OPENAI_API_KEY"),
                max_tokens=200,
                temperature=0.8
            )
    
    dspy.settings.configure(lm=lm)
    return lm
```

## Creating DSPy Workers

### Basic DSPy Worker

```python
from multiagents import dspy_worker

@dspy_worker("analyze_sentiment")
async def analyze_sentiment_worker(context):
    """Basic sentiment analysis using DSPy."""
    
    text = context.get("text", "")
    
    if not text:
        return {
            "sentiment": "neutral",
            "confidence": 0.0,
            "error": "No text provided"
        }
    
    # DSPy will process this context automatically
    return {
        "text": text,
        "analysis_type": "sentiment",
        "timestamp": datetime.utcnow().isoformat()
    }
```

### DSPy Worker with Custom Signature

```python
class SentimentAnalysisSignature(dspy.Signature):
    """Analyze sentiment of given text."""
    
    text = dspy.InputField(desc="Text to analyze for sentiment")
    context_type = dspy.InputField(desc="Type of text (email, review, social_media, etc.)")
    
    sentiment = dspy.OutputField(desc="Sentiment: positive, negative, or neutral")
    confidence = dspy.OutputField(desc="Confidence score between 0 and 1")
    emotions = dspy.OutputField(desc="List of detected emotions (joy, anger, fear, etc.)")
    key_phrases = dspy.OutputField(desc="Important phrases that influenced the sentiment")

@dspy_worker("detailed_sentiment_analysis", signature=SentimentAnalysisSignature)
async def detailed_sentiment_worker(context):
    """Detailed sentiment analysis with structured output."""
    
    text = context.get("text", "")
    context_type = context.get("context_type", "general")
    
    return {
        "text": text,
        "context_type": context_type,
        "analysis_timestamp": datetime.utcnow().isoformat()
    }

@detailed_sentiment_worker.post_process
async def validate_sentiment_output(dspy_result, original_context):
    """Validate and enhance DSPy output."""
    
    # Validate sentiment
    sentiment = dspy_result.get("sentiment", "neutral").lower()
    if sentiment not in ["positive", "negative", "neutral"]:
        sentiment = "neutral"
    
    # Validate confidence
    try:
        confidence = float(dspy_result.get("confidence", 0.5))
        confidence = max(0.0, min(1.0, confidence))
    except (ValueError, TypeError):
        confidence = 0.5
    
    # Parse emotions if string
    emotions = dspy_result.get("emotions", [])
    if isinstance(emotions, str):
        emotions = [e.strip() for e in emotions.split(",") if e.strip()]
    
    # Parse key phrases if string
    key_phrases = dspy_result.get("key_phrases", [])
    if isinstance(key_phrases, str):
        key_phrases = [p.strip() for p in key_phrases.split(",") if p.strip()]
    
    return {
        **dspy_result,
        "sentiment": sentiment,
        "confidence": confidence,
        "emotions": emotions[:5],  # Limit to 5 emotions
        "key_phrases": key_phrases[:10],  # Limit to 10 phrases
        "requires_human_review": confidence < 0.7,
        "processing_metadata": {
            "model_used": "gpt-3.5-turbo",
            "processed_at": datetime.utcnow().isoformat(),
            "text_length": len(original_context.get("text", ""))
        }
    }
```

### Content Generation Worker

```python
class ContentGenerationSignature(dspy.Signature):
    """Generate content based on requirements."""
    
    content_type = dspy.InputField(desc="Type of content to generate (email, blog_post, summary, etc.)")
    target_audience = dspy.InputField(desc="Target audience for the content")
    key_points = dspy.InputField(desc="Key points to include in the content")
    tone = dspy.InputField(desc="Desired tone (formal, casual, friendly, professional)")
    length = dspy.InputField(desc="Desired length (short, medium, long)")
    
    title = dspy.OutputField(desc="Compelling title for the content")
    content = dspy.OutputField(desc="Main content body")
    call_to_action = dspy.OutputField(desc="Call to action if appropriate")
    tags = dspy.OutputField(desc="Relevant tags or keywords")

@dspy_worker("generate_content", signature=ContentGenerationSignature)
async def content_generation_worker(context):
    """Generate content using DSPy."""
    
    content_type = context.get("content_type", "general")
    target_audience = context.get("target_audience", "general audience")
    key_points = context.get("key_points", [])
    tone = context.get("tone", "professional")
    length = context.get("length", "medium")
    
    # Convert key points to string if it's a list
    if isinstance(key_points, list):
        key_points = ", ".join(key_points)
    
    return {
        "content_type": content_type,
        "target_audience": target_audience,
        "key_points": key_points,
        "tone": tone,
        "length": length
    }

@content_generation_worker.post_process
async def enhance_generated_content(dspy_result, original_context):
    """Enhance and validate generated content."""
    
    content = dspy_result.get("content", "")
    title = dspy_result.get("title", "")
    
    # Parse tags if string
    tags = dspy_result.get("tags", [])
    if isinstance(tags, str):
        tags = [tag.strip() for tag in tags.replace("#", "").split(",") if tag.strip()]
    
    # Calculate content metrics
    word_count = len(content.split())
    char_count = len(content)
    
    # Determine if length matches requirement
    length_requirement = original_context.get("length", "medium")
    length_match = "unknown"
    
    if length_requirement == "short" and word_count <= 150:
        length_match = "match"
    elif length_requirement == "medium" and 150 < word_count <= 500:
        length_match = "match"
    elif length_requirement == "long" and word_count > 500:
        length_match = "match"
    else:
        length_match = "mismatch"
    
    return {
        **dspy_result,
        "tags": tags,
        "content_metrics": {
            "word_count": word_count,
            "character_count": char_count,
            "estimated_read_time": max(1, word_count // 200),  # ~200 WPM
            "length_requirement_met": length_match == "match"
        },
        "quality_indicators": {
            "has_title": bool(title),
            "has_call_to_action": bool(dspy_result.get("call_to_action", "")),
            "has_tags": len(tags) > 0,
            "appropriate_length": length_match == "match"
        },
        "generated_at": datetime.utcnow().isoformat()
    }
```

## Advanced Patterns

### Chain of Thought Worker

```python
class ChainOfThoughtSignature(dspy.Signature):
    """Solve complex problems using chain of thought reasoning."""
    
    problem = dspy.InputField(desc="Problem to solve")
    context = dspy.InputField(desc="Additional context or constraints")
    
    reasoning_steps = dspy.OutputField(desc="Step-by-step reasoning process")
    solution = dspy.OutputField(desc="Final solution or answer")
    confidence = dspy.OutputField(desc="Confidence in the solution (0-1)")
    assumptions = dspy.OutputField(desc="Key assumptions made")

@dspy_worker("complex_reasoning", signature=ChainOfThoughtSignature)
async def complex_reasoning_worker(context):
    """Solve complex problems with step-by-step reasoning."""
    
    problem = context.get("problem", "")
    additional_context = context.get("additional_context", "")
    
    return {
        "problem": problem,
        "context": additional_context,
        "reasoning_type": "chain_of_thought"
    }

@complex_reasoning_worker.post_process
async def structure_reasoning_output(dspy_result, original_context):
    """Structure the reasoning output."""
    
    # Parse reasoning steps
    reasoning_steps = dspy_result.get("reasoning_steps", "")
    if isinstance(reasoning_steps, str):
        steps = [step.strip() for step in reasoning_steps.split("\n") if step.strip()]
    else:
        steps = reasoning_steps if isinstance(reasoning_steps, list) else []
    
    # Parse assumptions
    assumptions = dspy_result.get("assumptions", "")
    if isinstance(assumptions, str):
        assumptions_list = [a.strip() for a in assumptions.split(",") if a.strip()]
    else:
        assumptions_list = assumptions if isinstance(assumptions, list) else []
    
    # Validate confidence
    try:
        confidence = float(dspy_result.get("confidence", 0.5))
        confidence = max(0.0, min(1.0, confidence))
    except (ValueError, TypeError):
        confidence = 0.5
    
    return {
        **dspy_result,
        "reasoning_steps": steps,
        "assumptions": assumptions_list,
        "confidence": confidence,
        "reasoning_quality": {
            "step_count": len(steps),
            "has_clear_solution": bool(dspy_result.get("solution", "")),
            "confidence_level": "high" if confidence > 0.8 else "medium" if confidence > 0.5 else "low"
        }
    }
```

### Multi-Step Processing Worker

```python
@dspy_worker("document_processor")
async def document_processor_worker(context):
    """Process documents through multiple DSPy steps."""
    
    document_text = context.get("document_text", "")
    processing_steps = context.get("processing_steps", ["summarize", "extract_entities", "classify"])
    
    if not document_text:
        return {"error": "No document text provided"}
    
    results = {}
    
    # Step 1: Summarization
    if "summarize" in processing_steps:
        summary_signature = create_summary_signature()
        summary_module = dspy.Predict(summary_signature)
        summary_result = summary_module(document=document_text)
        results["summary"] = summary_result
    
    # Step 2: Entity Extraction  
    if "extract_entities" in processing_steps:
        entity_signature = create_entity_signature()
        entity_module = dspy.Predict(entity_signature)
        entity_result = entity_module(document=document_text)
        results["entities"] = entity_result
    
    # Step 3: Classification
    if "classify" in processing_steps:
        classification_signature = create_classification_signature()
        classification_module = dspy.Predict(classification_signature)
        classification_result = classification_module(document=document_text)
        results["classification"] = classification_result
    
    return {
        "processing_results": results,
        "steps_completed": processing_steps,
        "document_length": len(document_text),
        "processed_at": datetime.utcnow().isoformat()
    }

def create_summary_signature():
    """Create signature for document summarization."""
    class SummarizeSignature(dspy.Signature):
        document = dspy.InputField(desc="Document to summarize")
        summary = dspy.OutputField(desc="Concise summary of the document")
        key_points = dspy.OutputField(desc="Main points from the document")
    return SummarizeSignature

def create_entity_signature():
    """Create signature for entity extraction."""
    class EntitySignature(dspy.Signature):
        document = dspy.InputField(desc="Document to extract entities from")
        people = dspy.OutputField(desc="People mentioned in the document")
        organizations = dspy.OutputField(desc="Organizations mentioned")
        locations = dspy.OutputField(desc="Locations mentioned")
        dates = dspy.OutputField(desc="Important dates mentioned")
    return EntitySignature

def create_classification_signature():
    """Create signature for document classification."""
    class ClassificationSignature(dspy.Signature):
        document = dspy.InputField(desc="Document to classify")
        category = dspy.OutputField(desc="Primary category of the document")
        subcategory = dspy.OutputField(desc="Subcategory if applicable")
        confidence = dspy.OutputField(desc="Confidence score for classification")
    return ClassificationSignature
```

## Optimization

### DSPy Optimizer Integration

```python
import dspy
from dspy.teleprompt import BootstrapFewShot, LabeledFewShot

class OptimizedDSPyWorker:
    """DSPy worker with automatic prompt optimization."""
    
    def __init__(self, signature, training_data=None):
        self.signature = signature
        self.predictor = dspy.Predict(signature)
        self.optimized_predictor = None
        self.training_data = training_data or []
    
    async def optimize(self, examples=None):
        """Optimize the DSPy predictor using examples."""
        
        if not examples and not self.training_data:
            print("No training examples available for optimization")
            return
        
        training_examples = examples or self.training_data
        
        # Convert examples to DSPy format
        dspy_examples = []
        for example in training_examples:
            dspy_example = dspy.Example(**example)
            dspy_examples.append(dspy_example)
        
        # Use BootstrapFewShot optimizer
        optimizer = BootstrapFewShot(metric=self._quality_metric)
        
        # Optimize the predictor
        self.optimized_predictor = optimizer.compile(
            self.predictor,
            trainset=dspy_examples
        )
        
        print(f"Optimized predictor with {len(dspy_examples)} examples")
    
    def _quality_metric(self, example, prediction, trace=None):
        """Define quality metric for optimization."""
        # Implement your specific quality metric
        # This is a simple example
        if hasattr(example, 'expected_output'):
            return example.expected_output in str(prediction)
        return True
    
    async def predict(self, **inputs):
        """Make prediction using optimized predictor if available."""
        predictor = self.optimized_predictor or self.predictor
        return predictor(**inputs)

# Usage example
async def create_optimized_sentiment_worker():
    """Create an optimized sentiment analysis worker."""
    
    # Training examples
    training_examples = [
        {
            "text": "I love this product! It's amazing!",
            "sentiment": "positive",
            "confidence": "0.9"
        },
        {
            "text": "This is terrible, I hate it.",
            "sentiment": "negative", 
            "confidence": "0.8"
        },
        {
            "text": "It's okay, nothing special.",
            "sentiment": "neutral",
            "confidence": "0.6"
        }
    ]
    
    # Create optimized worker
    worker = OptimizedDSPyWorker(
        signature=SentimentAnalysisSignature,
        training_data=training_examples
    )
    
    # Optimize with training data
    await worker.optimize()
    
    return worker
```

### Performance Caching

```python
import hashlib
import json
from typing import Optional, Dict, Any

class DSPyCacheManager:
    """Cache manager for DSPy predictions."""
    
    def __init__(self, cache_ttl_seconds=3600):
        self.cache = {}
        self.cache_ttl = cache_ttl_seconds
    
    def _generate_cache_key(self, inputs: Dict[str, Any]) -> str:
        """Generate cache key from inputs."""
        # Sort keys for consistent hashing
        sorted_inputs = json.dumps(inputs, sort_keys=True)
        return hashlib.md5(sorted_inputs.encode()).hexdigest()
    
    def get_cached_prediction(self, inputs: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Get cached prediction if available and not expired."""
        cache_key = self._generate_cache_key(inputs)
        cached_item = self.cache.get(cache_key)
        
        if cached_item:
            timestamp, prediction = cached_item
            if (datetime.utcnow() - timestamp).total_seconds() < self.cache_ttl:
                return prediction
            else:
                # Remove expired item
                del self.cache[cache_key]
        
        return None
    
    def cache_prediction(self, inputs: Dict[str, Any], prediction: Dict[str, Any]):
        """Cache a prediction."""
        cache_key = self._generate_cache_key(inputs)
        self.cache[cache_key] = (datetime.utcnow(), prediction)
    
    def clear_cache(self):
        """Clear all cached predictions."""
        self.cache.clear()

# Enhanced DSPy worker with caching
cache_manager = DSPyCacheManager(cache_ttl_seconds=1800)  # 30 minutes

@dspy_worker("cached_sentiment_analysis")
async def cached_sentiment_worker(context):
    """Sentiment analysis worker with caching."""
    
    text = context.get("text", "")
    
    if not text:
        return {"error": "No text provided"}
    
    # Check cache first
    cache_inputs = {"text": text, "type": "sentiment_analysis"}
    cached_result = cache_manager.get_cached_prediction(cache_inputs)
    
    if cached_result:
        cached_result["cache_hit"] = True
        return cached_result
    
    # Proceed with DSPy processing
    result = {
        "text": text,
        "analysis_type": "sentiment_with_cache",
        "cache_hit": False
    }
    
    return result

@cached_sentiment_worker.post_process
async def cache_sentiment_result(dspy_result, original_context):
    """Cache the DSPy result for future use."""
    
    # Only cache successful results
    if not dspy_result.get("error") and not dspy_result.get("cache_hit"):
        cache_inputs = {
            "text": original_context.get("text", ""),
            "type": "sentiment_analysis"
        }
        cache_manager.cache_prediction(cache_inputs, dspy_result)
    
    return dspy_result
```

## Production Considerations

### Error Handling and Resilience

```python
import asyncio
from functools import wraps

def dspy_retry(max_retries=3, backoff_factor=2.0):
    """Decorator to add retry logic to DSPy workers."""
    
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_retries):
                try:
                    return await func(*args, **kwargs)
                
                except Exception as e:
                    last_exception = e
                    
                    if attempt < max_retries - 1:
                        wait_time = backoff_factor ** attempt
                        print(f"DSPy worker attempt {attempt + 1} failed: {e}")
                        print(f"Retrying in {wait_time} seconds...")
                        await asyncio.sleep(wait_time)
                    else:
                        print(f"DSPy worker failed after {max_retries} attempts")
            
            # If all retries failed, return error response
            return {
                "error": f"DSPy worker failed after {max_retries} attempts: {last_exception}",
                "retry_count": max_retries,
                "last_error": str(last_exception)
            }
        
        return wrapper
    return decorator

@dspy_retry(max_retries=3)
@dspy_worker("resilient_text_processor")
async def resilient_text_processor(context):
    """Text processor with built-in retry logic."""
    
    text = context.get("text", "")
    
    if not text:
        raise ValueError("No text provided")
    
    return {
        "text": text,
        "processing_type": "resilient_processing"
    }
```

### Cost Monitoring

```python
class DSPyCostTracker:
    """Track DSPy usage costs and tokens."""
    
    def __init__(self):
        self.usage_stats = {
            "total_tokens": 0,
            "total_requests": 0,
            "estimated_cost": 0.0,
            "requests_by_model": {},
            "tokens_by_model": {}
        }
        
        # Cost per 1K tokens (example rates)
        self.cost_per_1k_tokens = {
            "gpt-3.5-turbo": 0.002,
            "gpt-4": 0.03,
            "claude-3-sonnet": 0.015
        }
    
    def track_usage(self, model: str, input_tokens: int, output_tokens: int):
        """Track token usage and estimate costs."""
        
        total_tokens = input_tokens + output_tokens
        estimated_cost = (total_tokens / 1000) * self.cost_per_1k_tokens.get(model, 0.002)
        
        # Update stats
        self.usage_stats["total_tokens"] += total_tokens
        self.usage_stats["total_requests"] += 1
        self.usage_stats["estimated_cost"] += estimated_cost
        
        # Update per-model stats
        if model not in self.usage_stats["requests_by_model"]:
            self.usage_stats["requests_by_model"][model] = 0
            self.usage_stats["tokens_by_model"][model] = 0
        
        self.usage_stats["requests_by_model"][model] += 1
        self.usage_stats["tokens_by_model"][model] += total_tokens
    
    def get_usage_report(self) -> Dict[str, Any]:
        """Get detailed usage report."""
        return {
            **self.usage_stats,
            "average_tokens_per_request": (
                self.usage_stats["total_tokens"] / self.usage_stats["total_requests"]
                if self.usage_stats["total_requests"] > 0 else 0
            ),
            "cost_per_request": (
                self.usage_stats["estimated_cost"] / self.usage_stats["total_requests"]
                if self.usage_stats["total_requests"] > 0 else 0
            )
        }

# Global cost tracker
cost_tracker = DSPyCostTracker()

@dspy_worker("cost_tracked_processor")
async def cost_tracked_processor(context):
    """DSPy worker with cost tracking."""
    
    text = context.get("text", "")
    
    # Estimate input tokens (rough approximation)
    input_tokens = len(text.split()) * 1.3  # ~1.3 tokens per word
    
    result = {
        "text": text,
        "estimated_input_tokens": input_tokens
    }
    
    return result

@cost_tracked_processor.post_process
async def track_processing_cost(dspy_result, original_context):
    """Track the cost of DSPy processing."""
    
    # Estimate output tokens
    output_text = str(dspy_result)
    output_tokens = len(output_text.split()) * 1.3
    
    input_tokens = dspy_result.get("estimated_input_tokens", 0)
    
    # Track usage
    cost_tracker.track_usage("gpt-3.5-turbo", int(input_tokens), int(output_tokens))
    
    # Add cost info to result
    dspy_result["token_usage"] = {
        "input_tokens": int(input_tokens),
        "output_tokens": int(output_tokens),
        "total_tokens": int(input_tokens + output_tokens)
    }
    
    return dspy_result
```

## Best Practices

### 1. Input Validation and Sanitization

```python
def validate_dspy_input(context: Dict[str, Any], required_fields: List[str]) -> Dict[str, Any]:
    """Validate and sanitize input for DSPy workers."""
    
    errors = []
    sanitized_context = {}
    
    # Check required fields
    for field in required_fields:
        if field not in context:
            errors.append(f"Missing required field: {field}")
        else:
            sanitized_context[field] = context[field]
    
    # Sanitize text fields
    for key, value in context.items():
        if isinstance(value, str):
            # Remove potential prompt injection patterns
            sanitized_value = value.replace("```", "").replace("</s>", "").replace("<|endoftext|>", "")
            
            # Limit length to prevent excessive token usage
            if len(sanitized_value) > 10000:  # 10k character limit
                sanitized_value = sanitized_value[:10000] + "..."
            
            sanitized_context[key] = sanitized_value
        else:
            sanitized_context[key] = value
    
    if errors:
        raise ValueError(f"Input validation failed: {'; '.join(errors)}")
    
    return sanitized_context
```

### 2. Output Validation

```python
def validate_dspy_output(output: Dict[str, Any], expected_fields: List[str]) -> Dict[str, Any]:
    """Validate DSPy output structure and content."""
    
    validated_output = {}
    
    for field in expected_fields:
        if field not in output:
            # Provide default value or mark as missing
            if field in ["confidence", "score"]:
                validated_output[field] = 0.5
            elif field in ["sentiment", "category", "classification"]:
                validated_output[field] = "unknown"
            else:
                validated_output[field] = ""
        else:
            validated_output[field] = output[field]
    
    # Add validation metadata
    validated_output["validation"] = {
        "all_fields_present": all(field in output for field in expected_fields),
        "missing_fields": [field for field in expected_fields if field not in output],
        "validated_at": datetime.utcnow().isoformat()
    }
    
    return validated_output
```

### 3. Testing DSPy Workers

```python
import pytest

class TestDSPyWorkers:
    """Test suite for DSPy workers."""
    
    @pytest.mark.asyncio
    async def test_sentiment_analysis_positive(self):
        """Test sentiment analysis with positive text."""
        
        context = {
            "text": "I absolutely love this product! It's fantastic!",
            "context_type": "review"
        }
        
        result = await detailed_sentiment_worker(context)
        
        # Validate output structure
        assert "sentiment" in result
        assert "confidence" in result
        assert result["sentiment"] in ["positive", "negative", "neutral"]
        assert 0 <= result["confidence"] <= 1
    
    @pytest.mark.asyncio
    async def test_sentiment_analysis_empty_input(self):
        """Test sentiment analysis with empty input."""
        
        context = {"text": ""}
        
        result = await detailed_sentiment_worker(context)
        
        # Should handle empty input gracefully
        assert "error" in result or result["sentiment"] == "neutral"
    
    @pytest.mark.asyncio
    async def test_content_generation_structure(self):
        """Test content generation output structure."""
        
        context = {
            "content_type": "email",
            "target_audience": "customers",
            "key_points": ["product update", "new features"],
            "tone": "friendly",
            "length": "medium"
        }
        
        result = await content_generation_worker(context)
        
        # Validate required fields
        assert "title" in result
        assert "content" in result
        assert "content_metrics" in result
        assert result["content_metrics"]["word_count"] > 0
```

### 4. Monitoring DSPy Performance

```python
class DSPyPerformanceMonitor:
    """Monitor DSPy worker performance and quality."""
    
    def __init__(self):
        self.metrics = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "average_response_time": 0.0,
            "average_tokens_per_request": 0.0,
            "quality_scores": []
        }
    
    def record_request(self, success: bool, response_time: float, 
                      tokens_used: int, quality_score: Optional[float] = None):
        """Record metrics for a DSPy request."""
        
        self.metrics["total_requests"] += 1
        
        if success:
            self.metrics["successful_requests"] += 1
        else:
            self.metrics["failed_requests"] += 1
        
        # Update moving averages
        total = self.metrics["total_requests"]
        self.metrics["average_response_time"] = (
            (self.metrics["average_response_time"] * (total - 1) + response_time) / total
        )
        self.metrics["average_tokens_per_request"] = (
            (self.metrics["average_tokens_per_request"] * (total - 1) + tokens_used) / total
        )
        
        if quality_score is not None:
            self.metrics["quality_scores"].append(quality_score)
            # Keep only last 100 scores
            if len(self.metrics["quality_scores"]) > 100:
                self.metrics["quality_scores"].pop(0)
    
    def get_performance_report(self) -> Dict[str, Any]:
        """Get performance report."""
        
        success_rate = (
            self.metrics["successful_requests"] / self.metrics["total_requests"]
            if self.metrics["total_requests"] > 0 else 0
        )
        
        average_quality = (
            sum(self.metrics["quality_scores"]) / len(self.metrics["quality_scores"])
            if self.metrics["quality_scores"] else 0
        )
        
        return {
            **self.metrics,
            "success_rate": success_rate,
            "failure_rate": 1 - success_rate,
            "average_quality_score": average_quality
        }
```

This comprehensive guide provides everything needed to successfully integrate DSPy with the MultiAgents Framework for production-ready LLM-powered workflows!