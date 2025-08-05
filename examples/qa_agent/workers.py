"""
Q&A System Workers - Coordinator, RAG, and Validator agents
"""
import json
from typing import Dict, Any, List
from multiagents import worker, dspy_worker

# Simple in-memory document store
DOCUMENT_STORE = {
    "worker_creation": """
    Creating Workers in MultiAgents:
    
    1. Basic Worker with @worker decorator:
    ```python
    @worker("my_worker")
    async def my_worker(context):
        data = context["input_data"]
        result = process_data(data)
        return {"processed": result}
    ```
    
    2. DSPy Worker with @dspy_worker:
    ```python
    @dspy_worker("llm_worker", signature="input -> output")
    async def llm_worker(context):
        return context  # DSPy handles LLM interaction
    ```
    
    3. Worker with compensation:
    ```python
    @worker("main_action")
    async def main_action(context):
        # Do something
        return {"result": "done"}
    
    @worker("compensate_action")
    async def compensate_action(context):
        # Undo the action
        return {"status": "compensated"}
    ```
    """,
    
    "workflow_creation": """
    Creating Workflows in MultiAgents:
    
    Use WorkflowBuilder to create workflows:
    ```python
    from multiagents.orchestrator.workflow import WorkflowBuilder
    
    workflow = (WorkflowBuilder("my_workflow")
        .add_step("step1", "worker1")
        .add_step("step2", "worker2", compensation="undo_worker2")
        .add_conditional_step("step3", "worker3", 
                            condition=lambda ctx: ctx.get("proceed"))
        .build())
    ```
    """,
    
    "event_bus": """
    Event Bus in MultiAgents:
    
    The Event Bus handles all communication between components:
    - Uses Redis Pub/Sub for scalability
    - Supports CommandEvent, ResultEvent, ErrorEvent, CompensationEvent
    - Fully asynchronous operation
    
    Example:
    ```python
    from multiagents.event_bus.redis_bus import RedisEventBus
    event_bus = RedisEventBus()
    await event_bus.start()
    ```
    """,
    
    "project_purpose": """
    MultiAgents Framework Purpose:
    
    The MultiAgents Framework is a hybrid event-driven orchestration framework designed specifically for building intelligent, multi-step, and fault-tolerant applications with LLM integration.
    
    Core Goals:
    1. **LLM-First Design**: Built specifically for AI developers and LLM-powered applications
    2. **Multi-Agent Coordination**: Enable multiple specialized agents to work together seamlessly
    3. **Production Ready**: Provide enterprise-grade reliability, monitoring, and fault tolerance
    4. **Developer Experience**: Simple APIs with decorators for easy agent creation
    
    Key Benefits:
    - Combines orchestration (centralized control) with event-driven architecture
    - Native DSPy integration for intelligent workers
    - Built-in compensation and rollback mechanisms (Saga pattern)
    - Comprehensive monitoring and observability
    - Scalable async communication via Redis
    
    Target Applications:
    - Conversational AI systems
    - Research assistants
    - LLM-driven workflows
    - Tool-using agents
    - Data analysis pipelines
    
    This framework makes it easy to build sophisticated AI applications where multiple intelligent agents work together reliably in production environments.
    """
}


@dspy_worker("coordinator")
async def coordinator_agent(context: Dict[str, Any]) -> Dict[str, Any]:
    """
    LLM-powered coordinator agent that intelligently classifies user questions and manages workflow.
    """
    import os
    import dspy
    
    user_question = context.get("question", "")
    clarification_response = context.get("clarification_response", "")
    
    if not user_question:
        return {
            "error": "No question provided",
            "needs_clarification": True
        }
    
    # Configure DSPy with Gemini
    try:
        api_key = os.getenv("GOOGLE_API_KEY") or context.get("google_api_key")
        if not api_key:
            return {
                "error": "GOOGLE_API_KEY not found in environment variables",
                "needs_clarification": True
            }
        
        from dspy import LM
        lm = LM(model="gemini/gemini-1.5-pro", api_key=api_key)
        dspy.configure(lm=lm)
        
    except Exception as e:
        return {
            "error": f"Failed to configure DSPy with Gemini: {e}",
            "needs_clarification": True
        }
    
    # Define DSPy signature for intelligent question classification
    class QuestionClassifier(dspy.Signature):
        """Analyze user questions about the MultiAgents framework and determine if clarification is needed."""
        
        original_question = dspy.InputField(desc="The user's original question")
        clarification_response = dspy.InputField(desc="User's clarification response (empty if none)")
        
        needs_clarification = dspy.OutputField(desc="Boolean: true if the question is too vague and needs clarification")
        topics = dspy.OutputField(desc="List of relevant topics: worker, workflow, event, dspy, project, general")
        clarification_message = dspy.OutputField(desc="Friendly clarification message if needed")
        question_to_process = dspy.OutputField(desc="The actual question to process (clarification or original)")
    
    # Use the clarification response if provided, otherwise use original question
    question_to_analyze = clarification_response if clarification_response else user_question
    
    try:
        # Use DSPy to intelligently classify the question
        classifier = dspy.Predict(QuestionClassifier)
        result = classifier(
            original_question=user_question,
            clarification_response=clarification_response
        )
        
        # Parse the results
        needs_clarification = result.needs_clarification.lower() == "true"
        
        # Parse topics (handle both string and list formats)
        try:
            import json
            if isinstance(result.topics, str):
                if result.topics.startswith('['):
                    topics = json.loads(result.topics)
                else:
                    topics = [t.strip() for t in result.topics.split(',')]
            else:
                topics = result.topics if isinstance(result.topics, list) else [result.topics]
        except:
            topics = ["general"]  # Fallback
        
        if needs_clarification and not clarification_response:
            # Need clarification
            return {
                "needs_clarification": True,
                "clarification_message": result.clarification_message,
                "detected_topics": topics,
                "original_question": user_question
            }
        else:
            # Proceed to RAG
            return {
                "needs_clarification": False,
                "topics": topics,
                "original_question": user_question,
                "clarification_response": clarification_response,
                "question_to_process": result.question_to_process or question_to_analyze,
                "proceed_to_rag": True,
                "llm_classified": True
            }
            
    except Exception as e:
        # Fallback to simple logic if DSPy fails
        if clarification_response or any(word in question_to_analyze.lower() for word in ["purpose", "project", "multiagents", "framework", "worker", "workflow"]):
            return {
                "needs_clarification": False,
                "topics": ["general"],
                "original_question": user_question,
                "clarification_response": clarification_response,
                "question_to_process": question_to_analyze,
                "proceed_to_rag": True,
                "fallback_used": f"DSPy failed: {e}"
            }
        else:
            return {
                "needs_clarification": True,
                "clarification_message": f"I'd like to help you with '{user_question}'. Could you please provide more details about what aspect of the MultiAgents framework you're interested in?",
                "detected_topics": ["general"],
                "original_question": user_question,
                "fallback_used": f"DSPy failed: {e}"
            }


@worker("rag_agent")
async def rag_retrieval_agent(context: Dict[str, Any]) -> Dict[str, Any]:
    """
    RAG agent that retrieves relevant documentation and constructs a response.
    """
    # Check if clarification is still needed (skip RAG if so)
    if context.get("needs_clarification", True):
        return {
            "skipped": True,
            "reason": "Clarification still needed"
        }
    
    topics = context.get("topics", [])
    question = context.get("question_to_process") or context.get("original_question", context.get("question", ""))
    
    if not topics:
        return {
            "error": "No topics identified for retrieval",
            "needs_regeneration": True
        }
    
    # Retrieve relevant documents
    retrieved_docs = []
    doc_keys = []
    
    # Map topics to document keys
    topic_to_docs = {
        "worker": ["worker_creation"],
        "workflow": ["workflow_creation"],
        "event": ["event_bus"],
        "dspy": ["worker_creation"],  # DSPy info is in worker_creation
        "project": ["project_purpose"],
        "general": ["project_purpose"]  # For general questions, show project overview
    }
    
    for topic in topics:
        if topic in topic_to_docs:
            for doc_key in topic_to_docs[topic]:
                if doc_key not in doc_keys:
                    doc_keys.append(doc_key)
                    retrieved_docs.append(DOCUMENT_STORE.get(doc_key, ""))
    
    if not retrieved_docs:
        return {
            "error": "No relevant documentation found",
            "needs_regeneration": True
        }
    
    # Construct response (simple template-based for this example)
    response = f"Based on your question about '{question}', here's the relevant information:\n\n"
    
    for i, doc in enumerate(retrieved_docs):
        if doc:
            response += f"{doc}\n"
            if i < len(retrieved_docs) - 1:
                response += "\n---\n\n"
    
    return {
        "response": response,
        "retrieved_docs": doc_keys,
        "needs_validation": True
    }


@worker("validator")
async def validator_agent(context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validator agent that checks the response against documentation and ensures quality.
    """
    # Check if RAG was skipped (clarification needed)
    if context.get("skipped", False):
        return {
            "skipped": True,
            "reason": "RAG was skipped due to clarification needed"
        }
    
    response = context.get("response", "")
    retrieved_docs = context.get("retrieved_docs", [])
    original_question = context.get("original_question", context.get("question", ""))
    question_to_validate = context.get("question_to_process") or original_question
    regeneration_count = context.get("regeneration_count", 0)
    
    # Simple validation checks
    validation_errors = []
    
    # Check 1: Response exists and has content
    if not response or len(response) < 50:
        validation_errors.append("Response is too short or empty")
    
    # Check 2: Response contains code examples if asking about implementation
    implementation_keywords = ["create", "how to", "implement", "build", "make"]
    needs_code = any(keyword in question_to_validate.lower() for keyword in implementation_keywords)
    
    if needs_code and "```" not in response:
        validation_errors.append("Response should include code examples")
    
    # Check 3: Response is relevant to the question (use the actual question being answered)
    question_words = set(question_to_validate.lower().split())
    response_words = set(response.lower().split())
    overlap = len(question_words.intersection(response_words))
    
    # For very short questions like "hi", skip relevance check
    if len(question_words) > 2 and overlap < 2:
        validation_errors.append("Response may not be relevant to the question")
    
    # Check 4: Maximum regeneration attempts
    if regeneration_count >= 2:
        # Accept the response after 2 attempts even if not perfect
        return {
            "validation_passed": True,
            "response": response,
            "warning": "Maximum regeneration attempts reached, accepting current response"
        }
    
    if validation_errors:
        # Request regeneration with suggestions
        suggestions = "Please regenerate the response with the following improvements:\n"
        for error in validation_errors:
            suggestions += f"- {error}\n"
        
        return {
            "validation_passed": False,
            "validation_errors": validation_errors,
            "regeneration_suggestions": suggestions,
            "regeneration_count": regeneration_count + 1,
            "needs_regeneration": True
        }
    
    # Validation passed
    return {
        "validation_passed": True,
        "response": response,
        "final_response": True
    }