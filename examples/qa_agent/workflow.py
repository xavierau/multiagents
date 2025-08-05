"""
Q&A System Workflow Definition
"""
from multiagents.orchestrator.workflow import WorkflowBuilder, WorkflowStep
from multiagents.core.saga_context import SagaContext


def create_qa_workflow():
    """
    Create the Q&A workflow with coordinator, RAG, and validator agents.
    
    Flow:
    1. Coordinator clarifies the question
    2. RAG agent retrieves docs and generates response  
    3. Validator checks the response
    """
    # Simple sequential workflow for this example
    # In a production system, you'd implement proper conditional logic
    workflow = (WorkflowBuilder("qa_workflow")
        # Step 1: Coordinator clarifies user intent
        .add_step("clarify", "coordinator")
        
        # Step 2: RAG retrieval and generation
        .add_step("retrieve_and_generate", "rag_agent")
        
        # Step 3: Validate response
        .add_step("validate", "validator")
        
        .build()
    )
    
    return workflow