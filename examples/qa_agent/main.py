"""
Q&A Agent System - Main entry point
"""
import asyncio
import sys
from typing import Dict, Any

from multiagents.core.factory import create_simple_framework
from multiagents.event_bus.redis_bus import RedisEventBus

from workers import coordinator_agent, rag_retrieval_agent, validator_agent
from workflow import create_qa_workflow


class QASystem:
    """Simple Q&A system using MultiAgents framework."""
    
    def __init__(self):
        self.workflow = create_qa_workflow()
        self.event_bus = None
        self.worker_manager = None
        self.orchestrator = None
        
    async def setup(self):
        """Initialize the framework components."""
        # Create framework components with monitoring
        self.event_bus, self.worker_manager, self.orchestrator = await create_simple_framework(
            self.workflow
        )
        
        # Register workers
        self.worker_manager.register(coordinator_agent)
        self.worker_manager.register(rag_retrieval_agent)
        self.worker_manager.register(validator_agent)
        
        # Start all components
        await self.event_bus.start()
        await self.worker_manager.start()
        await self.orchestrator.start()
        
        print("✅ Q&A System initialized successfully!")
        
    async def ask_question(self, question: str, clarification_response: str = None) -> Dict[str, Any]:
        """
        Process a user question through the Q&A workflow.
        
        Args:
            question: The user's question
            clarification_response: Optional response to clarification request
            
        Returns:
            The workflow execution result
        """
        # Prepare initial context
        context = {
            "question": question,
            "clarification_needed": clarification_response is None
        }
        
        if clarification_response:
            context["clarification_response"] = clarification_response
            context["clarification_needed"] = False
        
        # Execute workflow
        transaction_id = await self.orchestrator.execute_workflow("qa_workflow", context)
        
        # Wait for completion (with timeout)
        max_attempts = 30
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


async def interactive_qa_session():
    """Run an interactive Q&A session."""
    qa_system = QASystem()
    
    try:
        # Initialize system
        await qa_system.setup()
        
        print("\n🤖 MultiAgents Q&A System")
        print("=" * 50)
        print("Ask questions about the MultiAgents framework!")
        print("Type 'exit' to quit.\n")
        
        while True:
            # Get user question
            question = input("\n❓ Your question: ").strip()
            
            if question.lower() in ['exit', 'quit', 'q']:
                print("\n👋 Goodbye!")
                break
            
            if not question:
                continue
            
            # Process question
            print("\n🔄 Processing your question...")
            result = await qa_system.ask_question(question)
            
            # Check if clarification is needed
            step_results = result.get("step_results", {})
            
            if step_results.get("clarify", {}).get("needs_clarification"):
                # Show clarification message
                clarification_msg = step_results["clarify"]["clarification_message"]
                print(f"\n🤔 {clarification_msg}")
                
                # Get clarification response
                clarification = input("\n📝 Your response: ").strip()
                
                # Re-process with clarification
                print("\n🔄 Processing with clarification...")
                result = await qa_system.ask_question(question, clarification)
            
            # Display final response
            if result["state"] == "completed":
                # Find the final response in step results
                if "validate" in step_results and step_results["validate"].get("validation_passed"):
                    response = step_results["validate"]["response"]
                elif "retrieve_and_generate" in step_results:
                    response = step_results["retrieve_and_generate"].get("response", "No response generated")
                else:
                    response = "Unable to generate response"
                
                print(f"\n📚 Answer:\n{response}")
            else:
                print(f"\n❌ Error: {result.get('error', 'Unknown error')}")
                
    except KeyboardInterrupt:
        print("\n\n👋 Interrupted by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
    finally:
        # Cleanup
        await qa_system.cleanup()


def main():
    """Main entry point."""
    try:
        asyncio.run(interactive_qa_session())
    except Exception as e:
        print(f"Failed to run Q&A system: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()