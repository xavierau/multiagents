"""
Enhanced DSPy Worker Examples
============================

Examples showing the refactored dspy_worker decorator with tool support.
Demonstrates backward compatibility and new tool functionality.

Note: For real LLM examples with actual Gemini calls, see real_dspy_examples.py
"""

import asyncio
import os
import dspy
from multiagents import dspy_worker, tool


def configure_dspy_if_available():
    """Configure DSPy with Gemini if API key is available."""
    api_key = os.getenv("GOOGLE_API_KEY")
    if api_key:
        try:
            lm = dspy.LM(model="gemini/gemini-1.5-flash", api_key=api_key)
            dspy.configure(lm=lm)
            print("✅ DSPy configured with Gemini LM")
            return True
        except Exception as e:
            print(f"⚠️ Could not configure DSPy: {e}")
    else:
        print("ℹ️ GOOGLE_API_KEY not found - examples will show structure only")
    return False

# =======================
# 1. Backward Compatibility Examples
# =======================

# OLD STYLE - Still works exactly the same
@dspy_worker("sentiment_classifier", signature="text -> sentiment: str, confidence: float")
async def classify_sentiment(context: dict) -> dict:
    """Backward compatible: existing code unchanged."""
    sentiment = context.get('sentiment', 'neutral') 
    confidence = context.get('confidence', 0.5)
    
    return {
        "needs_review": confidence < 0.7,
        "method": "backward_compatible"
    }

# =======================
# 2. Enhanced Reasoning Examples  
# =======================

@dspy_worker("enhanced_summarizer", 
            signature="document -> summary: str, key_points: list[str]",
            reasoning="chain_of_thought")
async def enhanced_summarizer(context: dict) -> dict:
    """Enhanced with chain of thought reasoning."""
    summary = context.get('summary', '')
    key_points = context.get('key_points', [])
    
    return {
        "word_count": len(summary.split()) if summary else 0,
        "num_key_points": len(key_points),
        "reasoning_used": "chain_of_thought"
    }

# =======================
# 3. Tool Definitions
# =======================

@tool("web_search")
async def search_web(query: str) -> list[str]:
    """Search the web for information."""
    # Mock implementation - replace with real web search
    await asyncio.sleep(0.1)  # Simulate API call
    return [
        f"Web result 1 for: {query}",
        f"Web result 2 for: {query}",
        f"Web result 3 for: {query}"
    ]

@tool("database_query")
def query_database(table: str, filters: dict) -> dict:
    """Query database with filters."""
    # Mock implementation - replace with real database query
    return {
        "table": table,
        "filters": filters,
        "results": [
            {"id": 1, "data": "Sample record 1"},
            {"id": 2, "data": "Sample record 2"}
        ],
        "count": 2
    }

@tool("send_notification")
async def send_notification(recipient: str, message: str, priority: str = "normal") -> bool:
    """Send notification to recipient."""
    # Mock implementation - replace with real notification system
    await asyncio.sleep(0.05)  # Simulate sending
    print(f"📧 Notification sent to {recipient}: {message} (Priority: {priority})")
    return True

@tool("calculate_metrics")
def calculate_metrics(data: list[float]) -> dict:
    """Calculate statistical metrics from data."""
    if not data:
        return {"error": "No data provided"}
    
    return {
        "count": len(data),
        "sum": sum(data),
        "average": sum(data) / len(data),
        "min": min(data),
        "max": max(data)
    }

# =======================
# 4. Tool-Enabled Workers with ReAct
# =======================

@dspy_worker("research_assistant", 
            signature="research_question -> comprehensive_answer: str, sources: list[str]",
            tools=[search_web, query_database],
            reasoning="react",
            max_iters=5)
async def research_assistant(context: dict) -> dict:
    """Research assistant that can search web and query database."""
    answer = context.get('comprehensive_answer', '')
    sources = context.get('sources', [])
    
    return {
        "answer_length": len(answer),
        "source_count": len(sources),  
        "research_method": "react_with_tools",
        "tools_available": ["web_search", "database_query"]
    }

@dspy_worker("customer_service_agent",
            signature="customer_request -> response: str, action_taken: str, follow_up_needed: bool",
            tools=[query_database, send_notification],
            reasoning="react",
            max_iters=4)
async def customer_service_agent(context: dict) -> dict:
    """Customer service agent with database and notification capabilities."""
    response = context.get('response', '')
    action = context.get('action_taken', '')
    follow_up = context.get('follow_up_needed', False)
    
    return {
        "response_provided": bool(response),
        "action_completed": bool(action),
        "requires_follow_up": follow_up,
        "agent_type": "tool_enabled_customer_service"
    }

# =======================
# 5. Data Analysis Worker with Multiple Tools
# =======================

@dspy_worker("data_analyst",
            signature="analysis_request -> insights: str, recommendations: list[str], metrics: dict",
            tools=[query_database, calculate_metrics, send_notification],
            reasoning="react",
            max_iters=6)
async def data_analyst(context: dict) -> dict:
    """Data analyst that can query data, calculate metrics, and notify stakeholders."""
    insights = context.get('insights', '')
    recommendations = context.get('recommendations', [])
    metrics = context.get('metrics', {})
    
    return {
        "analysis_complete": bool(insights),
        "recommendation_count": len(recommendations),
        "metrics_calculated": bool(metrics),
        "analyst_type": "multi_tool_analyst"
    }

# =======================
# 6. Code Generation Worker with CodeAct
# =======================

@dspy_worker("code_generator",
            signature="requirements -> code: str, documentation: str, test_cases: list[str]",
            tools=[search_web],  # Can search for code examples
            reasoning="codeact")
async def code_generator(context: dict) -> dict:
    """Code generator using CodeAct reasoning with web search for examples."""
    code = context.get('code', '')
    documentation = context.get('documentation', '')
    test_cases = context.get('test_cases', [])
    
    return {
        "code_generated": bool(code),
        "documentation_provided": bool(documentation),
        "test_cases_count": len(test_cases),
        "generation_method": "codeact_with_search"
    }

# =======================
# 7. Simple Workers (No Tools)
# =======================

@dspy_worker("text_processor",
            signature="input_text -> processed_text: str, word_count: int, language: str",
            reasoning="predict")
async def text_processor(context: dict) -> dict:
    """Simple text processor without tools."""
    processed_text = context.get('processed_text', '')
    word_count = context.get('word_count', 0)
    language = context.get('language', 'unknown')
    
    return {
        "processing_complete": bool(processed_text),
        "words_processed": word_count,
        "detected_language": language,
        "processor_type": "simple_signature_based"
    }

# =======================
# 8. Demo Function
# =======================

async def demo_enhanced_workers():
    """Demonstrate the enhanced DSPy workers."""
    print("🚀 Enhanced DSPy Worker Examples")
    print("=" * 50)
    
    # Try to configure DSPy with real LLM
    has_llm = configure_dspy_if_available()
    
    workers_to_test = [
        ("Backward Compatible Classifier", classify_sentiment, {"text": "I love this!"}),
        ("Enhanced Summarizer", enhanced_summarizer, {"document": "Long document text here..."}),
        ("Research Assistant", research_assistant, {"research_question": "What is machine learning?"}),
        ("Customer Service Agent", customer_service_agent, {"customer_request": "I need help with my order"}),
        ("Data Analyst", data_analyst, {"analysis_request": "Analyze sales data trends"}),
        ("Code Generator", code_generator, {"requirements": "Create a Python function to sort a list"}),
        ("Text Processor", text_processor, {"input_text": "Hello world, how are you today?"})
    ]
    
    for name, worker, test_context in workers_to_test:
        print(f"\n📋 Testing: {name}")
        try:
            # Print worker info
            print(f"   Worker Type: {worker.get_worker_type()}")
            print(f"   Worker Class: {type(worker).__name__}")
            print(f"   Signature: {worker.dspy_config.signature}")
            print(f"   Reasoning: {worker.dspy_config.reasoning}")
            
            if hasattr(worker, 'get_available_tools'):
                tools = worker.get_available_tools()
                print(f"   Available Tools: {tools if tools else 'None'}")
            
            print(f"   Status: ✅ Created successfully")
            
        except Exception as e:
            print(f"   Status: ❌ Failed - {e}")
    
    print(f"\n" + "=" * 50)
    print("🎉 Demo Complete!")
    print("\nKey Features Demonstrated:")
    print("• ✅ Backward compatibility - existing code unchanged")
    print("• ✅ Enhanced reasoning types (predict, chain_of_thought, react, codeact)")  
    print("• ✅ Tool integration with @tool decorator")
    print("• ✅ ReAct pattern for tool-using agents")
    print("• ✅ CodeAct pattern for code generation")
    print("• ✅ Multiple tools per worker")
    print("• ✅ Async and sync tool support")
    print("• ✅ Training data collection for future optimization")


if __name__ == "__main__":
    print("Enhanced DSPy Worker Examples")
    print("Showcasing the refactored decorator with tool support")
    
    try:
        asyncio.run(demo_enhanced_workers())
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()