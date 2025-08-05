"""
Test the simple Q&A system with the problematic scenario.
"""
import asyncio
from main import QASystem

async def test_clarification_scenario():
    """Test the scenario where user says 'hi' then clarifies with 'what is the purpose of the project'."""
    
    qa_system = QASystem()
    
    try:
        print("🚀 Setting up Q&A system...")
        await qa_system.setup()
        
        print("\n" + "="*60)
        print("TEST: User says 'hi' then clarifies with 'what is the purpose of the project'")
        print("="*60)
        
        # Test 1: Initial ambiguous question
        print("\n🔍 Test 1: User asks 'hi'")
        result1 = await qa_system.ask_question("hi")
        
        print(f"Result state: {result1['state']}")
        step_results = result1.get("step_results", {})
        
        if step_results.get("clarify", {}).get("needs_clarification"):
            clarification_msg = step_results["clarify"]["clarification_message"]
            print(f"✅ System asks for clarification: {clarification_msg[:100]}...")
            
            # Test 2: User provides clarification
            print(f"\n🔍 Test 2: User clarifies with 'what is the purpose of the project'")
            result2 = await qa_system.ask_question("hi", "what is the purpose of the project")
            
            print(f"Result state: {result2['state']}")
            step_results2 = result2.get("step_results", {})
            
            if result2["state"] == "completed":
                # Find the final response
                if "validate" in step_results2 and step_results2["validate"].get("validation_passed"):
                    response = step_results2["validate"]["response"]
                elif "retrieve_and_generate" in step_results2:
                    response = step_results2["retrieve_and_generate"].get("response", "No response generated")
                else:
                    response = "Unable to generate response"
                
                print(f"✅ SUCCESS: Got final response")
                print(f"📚 Response preview: {response[:200]}...")
                
                # Check if response mentions the project purpose
                if "multiagents" in response.lower() and "framework" in response.lower():
                    print("✅ Response is relevant to project purpose")
                else:
                    print("❌ Response may not be relevant to project purpose")
                    
            else:
                print(f"❌ FAILED: {result2.get('error', 'Unknown error')}")
                print("Step results:", step_results2)
                
        else:
            print("❌ System should have asked for clarification but didn't")
            
    except Exception as e:
        print(f"❌ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        await qa_system.cleanup()

if __name__ == "__main__":
    asyncio.run(test_clarification_scenario())