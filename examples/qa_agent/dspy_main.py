"""
DSPy-powered Q&A Agent System - Main entry point with codebase RAG
"""
import asyncio
import sys
import os
from typing import Dict, Any

from multiagents.core.factory import create_simple_framework
from dspy_workers import dspy_coordinator_agent, dspy_rag_retrieval_agent, dspy_validator_agent
from dspy_workflow import create_dspy_qa_workflow


class DSPyQASystem:
    """DSPy-powered Q&A system with codebase RAG."""
    
    def __init__(self):
        self.workflow = create_dspy_qa_workflow()
        self.event_bus = None
        self.worker_manager = None
        self.orchestrator = None
        
    async def setup(self):
        """Initialize the framework components."""
        # Check for Google API key
        if not os.getenv("GOOGLE_API_KEY"):
            print("⚠️  GOOGLE_API_KEY environment variable not set!")
            print("   Please set it to use Gemini with DSPy")
            print("   export GOOGLE_API_KEY='your-api-key'")
            return False
        
        # Create framework components with monitoring
        self.event_bus, self.worker_manager, self.orchestrator = await create_simple_framework(
            self.workflow
        )
        
        # Register DSPy workers
        self.worker_manager.register(dspy_coordinator_agent)
        self.worker_manager.register(dspy_rag_retrieval_agent)
        self.worker_manager.register(dspy_validator_agent)
        
        # Start all components
        await self.event_bus.start()
        await self.worker_manager.start()
        await self.orchestrator.start()
        
        print("✅ DSPy Q&A System initialized successfully!")
        print("🧠 Using Gemini LLM for intelligent responses")
        print("📚 Codebase indexed for real-time search")
        return True
        
    async def ask_question(self, question: str) -> Dict[str, Any]:
        """
        Process a user question through the DSPy Q&A workflow.
        
        Args:
            question: The user's question about the codebase
            
        Returns:
            The workflow execution result
        """
        # Prepare initial context
        context = {
            "question": question,
            "google_api_key": os.getenv("GOOGLE_API_KEY")  # Pass API key to workers
        }
        
        # Execute workflow
        transaction_id = await self.orchestrator.execute_workflow("dspy_qa_workflow", context)
        
        # Wait for completion (with timeout)
        max_attempts = 60  # 30 seconds
        for _ in range(max_attempts):
            status = await self.orchestrator.get_status(transaction_id)
            
            if status["state"] in ["completed", "failed"]:
                return status
                
            await asyncio.sleep(0.5)
        
        return {"error": "Workflow timeout"}
    
    async def cleanup(self):
        """Cleanup framework components."""
        if self.orchestrator:
            await self.orchestrator.stop()
        if self.worker_manager:
            await self.worker_manager.stop()
        if self.event_bus:
            await self.event_bus.stop()


async def interactive_dspy_qa_session():
    """Run an interactive DSPy Q&A session."""
    qa_system = DSPyQASystem()
    
    try:
        # Initialize system
        if not await qa_system.setup():
            return
        
        print("\n🤖 DSPy-Powered MultiAgents Codebase Q&A")
        print("=" * 55)
        print("Ask questions about the MultiAgents framework codebase!")
        print("Powered by Gemini LLM with intelligent codebase search.")
        print("Type 'exit' to quit.\n")
        
        # Show example questions
        print("💡 Example questions:")
        print("  • How do I create a worker with the @worker decorator?")
        print("  • What's the difference between @worker and @dspy_worker?")
        print("  • How does the orchestrator handle workflow state?")
        print("  • Show me the WorkflowBuilder implementation")
        print("  • How do I set up monitoring in MultiAgents?")
        print()
        
        while True:
            # Get user question
            question = input("❓ Your question: ").strip()
            
            if question.lower() in ['exit', 'quit', 'q']:
                print("\n👋 Goodbye!")
                break
            
            if not question:
                continue
            
            # Process question with DSPy
            print(f"\n🔄 Analyzing question with Gemini...")
            print(f"🔍 Searching codebase...")
            print(f"🧠 Generating intelligent response...")
            
            result = await qa_system.ask_question(question)
            
            # Display results
            if result["state"] == "completed":
                step_results = result.get("step_results", {})
                
                # Check coordinator results
                classify_result = step_results.get("classify", {})
                if classify_result.get("needs_clarification"):
                    print(f"\n🤔 {classify_result.get('clarification_message', 'Need more details')}")
                    continue
                
                # Check if we got a final response
                if "validate" in step_results and step_results["validate"].get("validation_passed"):
                    response = step_results["validate"]["response"]
                    print(f"\n📚 **Answer**:\n{response}")
                    
                    # Show retrieved files if available
                    rag_result = step_results.get("retrieve_and_generate", {})
                    retrieved_files = rag_result.get("retrieved_files", [])
                    if retrieved_files:
                        print(f"\n📁 **Sources**: {', '.join(retrieved_files[:3])}")
                        if len(retrieved_files) > 3:
                            print(f"   ... and {len(retrieved_files) - 3} more files")
                    
                elif "retrieve_and_generate" in step_results:
                    # Show RAG response even if validation failed
                    rag_result = step_results["retrieve_and_generate"]
                    if "response" in rag_result:
                        print(f"\n📝 **Response**:\n{rag_result['response']}")
                    else:
                        print(f"\n❌ Error: {rag_result.get('error', 'No response generated')}")
                else:
                    print(f"\n❌ No response generated")
                    
            else:
                print(f"\n❌ Error: {result.get('error', 'Unknown error')}")
                
    except KeyboardInterrupt:
        print("\n\n👋 Interrupted by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
    finally:
        # Cleanup
        await qa_system.cleanup()


async def test_dspy_qa_system():
    """Test the DSPy Q&A system with predefined questions."""
    
    print("🚀 Testing DSPy Q&A System")
    print("=" * 50)
    
    qa_system = DSPyQASystem()
    
    try:
        if not await qa_system.setup():
            return
        
        test_questions = [
            "How do I create a basic worker?",
            "What is the WorkflowBuilder and how do I use it?",
            "How does the event bus work in MultiAgents?",
            "Show me the orchestrator implementation",
            "How do I set up monitoring?"
        ]
        
        for i, question in enumerate(test_questions, 1):
            print(f"\n🧪 Test {i}: {question}")
            
            try:
                result = await qa_system.ask_question(question)
                
                if result["state"] == "completed":
                    step_results = result.get("step_results", {})
                    
                    if "validate" in step_results and step_results["validate"].get("validation_passed"):
                        response = step_results["validate"]["response"]
                        print(f"✅ Generated response: {len(response)} characters")
                    else:
                        print("⚠️ Response generated but validation failed")
                else:
                    print(f"❌ Failed: {result.get('error', 'Unknown error')}")
                    
            except Exception as e:
                print(f"❌ Test failed: {e}")
            
            print("-" * 50)
        
    finally:
        await qa_system.cleanup()
    
    print("🏁 Testing completed!")


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="DSPy-powered Q&A system for MultiAgents codebase")
    parser.add_argument("--test", action="store_true", help="Run automated tests")
    parser.add_argument("--question", type=str, help="Ask a single question")
    
    args = parser.parse_args()
    
    try:
        if args.test:
            asyncio.run(test_dspy_qa_system())
        elif args.question:
            async def single_question():
                qa_system = DSPyQASystem()
                if await qa_system.setup():
                    result = await qa_system.ask_question(args.question)
                    if result["state"] == "completed":
                        step_results = result.get("step_results", {})
                        if "validate" in step_results:
                            print(step_results["validate"].get("response", "No response"))
                        else:
                            print("No final response generated")
                    else:
                        print(f"Error: {result.get('error', 'Unknown error')}")
                await qa_system.cleanup()
            
            asyncio.run(single_question())
        else:
            asyncio.run(interactive_dspy_qa_session())
    except Exception as e:
        print(f"Failed to run DSPy Q&A system: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()