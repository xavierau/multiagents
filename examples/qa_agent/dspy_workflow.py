"""
DSPy-powered Q&A System Workflow Definition
"""
from multiagents.orchestrator.workflow import WorkflowBuilder


def create_dspy_qa_workflow():
    """
    Create the DSPy-powered Q&A workflow with:
    1. DSPy coordinator with Gemini for question classification
    2. DSPy RAG agent that searches the actual codebase
    3. DSPy validator that ensures accuracy
    """
    workflow = (WorkflowBuilder("dspy_qa_workflow")
        # Step 1: DSPy-powered coordinator with Gemini
        .add_step("classify", "dspy_coordinator")
        
        # Step 2: DSPy-powered RAG with codebase search
        .add_step("retrieve_and_generate", "dspy_rag_agent")
        
        # Step 3: DSPy-powered validation
        .add_step("validate", "dspy_validator")
        
        .build()
    )
    
    return workflow