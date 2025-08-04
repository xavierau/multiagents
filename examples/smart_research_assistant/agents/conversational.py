"""
Conversational Agent - Handles greetings, simple responses, and casual interactions.

This agent specializes in:
1. Responding to greetings and pleasantries
2. Handling simple acknowledgments 
3. Providing help and guidance
4. Directing users to research capabilities when appropriate
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../../'))

from typing import Dict, Any
import asyncio
from datetime import datetime

from multiagents.worker_sdk import dspy_worker
from config.gemini_config import get_coordinator_config


@dspy_worker(
    "conversational_response",
    signature="user_input, context -> response, response_type, suggested_actions",
    timeout=30,
    retry_attempts=2,
    model=get_coordinator_config().model
)
async def conversational_response_worker(context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Conversational Agent that handles greetings and simple interactions.
    
    This agent provides:
    1. Friendly responses to greetings
    2. Help and guidance information
    3. Suggestions for research queries
    4. Graceful handling of unclear inputs
    """
    user_input = context.get("user_question", "").lower().strip()
    existing_context = context.get("context", {})
    
    # Access DSPy agent for intelligent responses
    dspy_agent = context.get("_dspy_agent")
    
    if dspy_agent:
        try:
            # Use LLM for conversational response
            conversation_signature = dspy_agent.create_signature(
                "user_message, context",
                "friendly_response, response_type, suggested_research_topics"
            )
            
            conversation_result = dspy_agent.predict(
                conversation_signature,
                user_message=user_input,
                context=str(existing_context)
            )
            
            response = conversation_result.get("friendly_response", "")
            response_type = conversation_result.get("response_type", "greeting")
            suggested_topics = conversation_result.get("suggested_research_topics", "")
            
        except Exception as e:
            print(f"DSPy conversation failed, using fallback: {e}")
            response, response_type, suggested_topics = _fallback_conversational_response(user_input)
    else:
        response, response_type, suggested_topics = _fallback_conversational_response(user_input)
    
    # Generate suggested actions based on response type
    suggested_actions = _generate_suggested_actions(response_type, user_input)
    
    return {
        "response": response,
        "response_type": response_type,
        "suggested_actions": suggested_actions,
        "suggested_research_topics": suggested_topics.split(",") if suggested_topics else [],
        "conversation_metadata": {
            "response_method": "llm_enhanced" if dspy_agent else "rule_based",
            "user_input_length": len(user_input),
            "response_time": datetime.now().isoformat(),
            "interaction_type": "conversational"
        }
    }


def _fallback_conversational_response(user_input: str) -> tuple:
    """Fallback conversational responses when DSPy is not available."""
    
    # Greetings
    greetings = ['hi', 'hello', 'hey']
    if any(greeting in user_input for greeting in greetings):
        response = (
            "Hello! 👋 I'm your Smart Research Assistant. I can help you with:\n"
            "• Market research and analysis\n"
            "• Investment and ROI calculations\n" 
            "• Technology trends and insights\n"
            "• Data analysis and statistics\n\n"
            "What would you like to research today?"
        )
        return response, "greeting", "investment opportunities, market trends, technology analysis"
    
    # Time-based greetings
    if any(time_greeting in user_input for time_greeting in ['good morning', 'good afternoon', 'good evening']):
        response = (
            "Good day! ☀️ Ready to dive into some research? I'm here to help you explore:\n"
            "• Financial markets and investment opportunities\n"
            "• Industry trends and analysis\n"
            "• Data-driven insights\n\n"
            "What topic interests you most?"
        )
        return response, "time_greeting", "stock analysis, renewable energy, AI trends"
    
    # Thank you responses
    if any(thanks in user_input for thanks in ['thank', 'thanks']):
        response = (
            "You're very welcome! 😊 I'm always here to help with your research needs.\n"
            "Feel free to ask me about any topic you'd like to explore!"
        )
        return response, "appreciation", "follow-up research, additional analysis"
    
    # Goodbyes
    if any(goodbye in user_input for goodbye in ['bye', 'goodbye', 'see you']):
        response = (
            "Goodbye! 👋 It was great helping you with your research.\n"
            "Come back anytime you need insights or analysis!"
        )
        return response, "farewell", ""
    
    # Help requests
    if any(help_word in user_input for help_word in ['help', 'what can you do', 'how do you work']):
        response = (
            "I'm your AI Research Assistant! Here's what I can do:\n\n"
            "🔍 **Research Capabilities:**\n"
            "• Market analysis and trends\n"
            "• Investment research and ROI calculations\n"
            "• Technology and industry insights\n"
            "• Data analysis and statistics\n\n"
            "💡 **How to use me:**\n"
            "• Ask specific research questions\n"
            "• Request calculations or analysis\n"
            "• Get market insights and trends\n\n"
            "**Example questions:**\n"
            "• \"What's the ROI of renewable energy stocks?\"\n"
            "• \"Analyze the latest AI investment trends\"\n"
            "• \"Calculate compound interest on $5,000 at 7%\"\n\n"
            "What would you like to research?"
        )
        return response, "help", "renewable energy, AI trends, investment analysis"
    
    # Unclear/short inputs
    if len(user_input) < 4:
        response = (
            "I didn't quite catch that. 🤔 Could you please provide more details?\n\n"
            "I specialize in research and analysis. Try asking me about:\n"
            "• Market trends or stock analysis\n"
            "• Investment opportunities and ROI\n"
            "• Technology developments\n"
            "• Data analysis questions\n\n"
            "What would you like to explore?"
        )
        return response, "clarification_needed", "market research, investment analysis, tech trends"
    
    # Default response for unclear inputs
    response = (
        "I'm not sure I understand what you're looking for. 🤔\n\n"
        "I'm designed to help with research and analysis. You can ask me to:\n"
        "• Research market trends or companies\n"
        "• Analyze investment opportunities\n"
        "• Calculate returns and financial metrics\n"
        "• Explore technology and industry insights\n\n"
        "Could you rephrase your question or tell me what you'd like to research?"
    )
    return response, "unclear_request", "market analysis, investment research, technology trends"


def _generate_suggested_actions(response_type: str, user_input: str) -> list:
    """Generate suggested actions based on the response type."""
    
    if response_type in ["greeting", "time_greeting"]:
        return [
            "Ask about investment opportunities",
            "Research market trends", 
            "Get help with calculations",
            "Explore technology insights"
        ]
    
    elif response_type == "help":
        return [
            "Try: 'What are the latest AI trends?'",
            "Try: 'Calculate ROI on $10,000 investment'",
            "Try: 'Analyze renewable energy stocks'",
            "Ask about specific markets or companies"
        ]
    
    elif response_type in ["clarification_needed", "unclear_request"]:
        return [
            "Be more specific in your question",
            "Ask about a particular industry or market",
            "Request analysis or calculations",
            "Use keywords like 'analyze', 'research', or 'calculate'"
        ]
    
    elif response_type == "appreciation":
        return [
            "Ask a follow-up question",
            "Research a new topic",
            "Get additional analysis",
            "Explore related subjects"
        ]
    
    else:
        return [
            "Ask a research question",
            "Request market analysis",
            "Get investment insights",
            "Explore industry trends"
        ]


if __name__ == "__main__":
    # Test the conversational agent
    async def test_conversational_agent():
        print("🗣️ Testing Conversational Agent")
        print("=" * 40)
        
        test_inputs = [
            "hi",
            "hello there",
            "good morning",
            "thanks",
            "help",
            "what can you do",
            "bye",
            "a",
            "unclear input here"
        ]
        
        for user_input in test_inputs:
            print(f"\nInput: '{user_input}'")
            
            context = {
                "user_question": user_input,
                "context": {}
            }
            
            try:
                result = await conversational_response_worker.execute(context)
                print(f"Response: {result.get('response', 'No response')[:100]}...")
                print(f"Type: {result.get('response_type', 'unknown')}")
                print(f"Suggested actions: {len(result.get('suggested_actions', []))}")
            except Exception as e:
                print(f"Error: {e}")
    
    # Run test
    asyncio.run(test_conversational_agent())