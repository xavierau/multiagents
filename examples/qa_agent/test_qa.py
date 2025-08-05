"""
Test script for Q&A Agent System
"""
import asyncio
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from multiagents.core.factory import create_simple_framework
from workers import coordinator_agent, rag_retrieval_agent, validator_agent
from workflow import create_qa_workflow


async def test_qa_system():
    """Test the Q&A system with predefined questions."""
    
    print("🚀 Testing Q&A Agent System")
    print("=" * 50)
    
    # Initialize system
    workflow = create_qa_workflow()
    event_bus, worker_manager, orchestrator = await create_simple_framework(workflow)
    
    # Register workers
    worker_manager.register(coordinator_agent)
    worker_manager.register(rag_retrieval_agent)
    worker_manager.register(validator_agent)
    
    # Start framework
    await event_bus.start()
    await worker_manager.start()
    await orchestrator.start()
    
    print("✅ Q&A System initialized!\n")
    
    # Test cases
    test_cases = [
        {
            "name": "Clear Worker Question",
            "question": "How do I create a basic worker?",
            "clarification": "1"  # Basic worker
        },
        {
            "name": "DSPy Worker Question", 
            "question": "How do I create an AI worker with DSPy?",
            "clarification": "1"  # Still worker creation
        },
        {
            "name": "Workflow Question",
            "question": "How do I build a workflow?",
            "clarification": "2"  # Workflow creation
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"🧪 Test {i}: {test_case['name']}")
        print(f"❓ Question: {test_case['question']}")
        
        try:
            # Step 1: Initial question (should need clarification)
            result1 = await run_workflow(orchestrator, test_case["question"])
            
            if result1["state"] == "completed":
                step_results = result1.get("step_results", {})
                
                # Check if coordinator asked for clarification
                if step_results.get("clarify", {}).get("needs_clarification"):
                    print("🤔 System asked for clarification (as expected)")
                    
                    # Step 2: Re-run with clarification
                    context_with_clarification = {
                        "question": test_case["question"],
                        "clarification_needed": False,
                        "topics": ["worker"] if test_case["clarification"] == "1" else ["workflow"],
                        "original_question": test_case["question"]
                    }
                    
                    result2 = await run_workflow(orchestrator, "", context_with_clarification)
                    
                    if result2["state"] == "completed":
                        final_results = result2.get("step_results", {})
                        
                        # Check if we got a valid response
                        if "validate" in final_results and final_results["validate"].get("validation_passed"):
                            response = final_results["validate"]["response"]
                            print(f"✅ Generated response:\n{response[:200]}...\n")
                        elif "retrieve_and_generate" in final_results:
                            response = final_results["retrieve_and_generate"].get("response", "No response")
                            print(f"📝 RAG response:\n{response[:200]}...\n")
                        else:
                            print("⚠️ No final response generated\n")
                    else:
                        print(f"❌ Second workflow failed: {result2.get('error', 'Unknown error')}\n")
                else:
                    print("⚠️ No clarification requested (unexpected)\n")
            else:
                print(f"❌ Initial workflow failed: {result1.get('error', 'Unknown error')}\n")
                
        except Exception as e:
            print(f"❌ Test failed with exception: {e}\n")
        
        print("-" * 50)
    
    # Cleanup
    await orchestrator.stop()
    await worker_manager.stop()
    await event_bus.stop()
    
    print("🏁 Testing completed!")


async def run_workflow(orchestrator, question, custom_context=None):
    """Run a workflow and wait for completion."""
    context = custom_context or {"question": question, "clarification_needed": True}
    
    transaction_id = await orchestrator.execute_workflow("qa_workflow", context)
    
    # Wait for completion
    for _ in range(30):  # 15 second timeout
        status = await orchestrator.get_status(transaction_id)
        if status["state"] in ["completed", "failed"]:
            return status
        await asyncio.sleep(0.5)
    
    return {"error": "Workflow timeout"}


if __name__ == "__main__":
    try:
        asyncio.run(test_qa_system())
    except KeyboardInterrupt:
        print("\n👋 Test interrupted by user")
    except Exception as e:
        print(f"❌ Test failed: {e}")