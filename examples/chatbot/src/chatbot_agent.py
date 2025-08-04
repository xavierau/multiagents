"""
DSPy-powered Chatbot Agent using Google Gemini

This module implements a conversational agent using the MultiAgents
framework's DSPy integration with Google Gemini.
"""

import asyncio
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
import structlog
from datetime import datetime

from multiagents.worker_sdk import dspy_worker
from multiagents.worker_sdk.dspy_wrapper import DSPyAgent, DSPyConfig
import dspy


logger = structlog.get_logger()


@dataclass
class ChatbotConfig:
    """Configuration for the chatbot agent."""
    model: str = "gemini/gemini-1.5-flash"
    temperature: float = 0.7
    max_tokens: int = 1000
    personality: str = "default"
    system_prompt: Optional[str] = None
    conversation_window: int = 5  # Number of previous messages to include


class ConversationSignature(dspy.Signature):
    """DSPy signature for conversational responses."""
    conversation_history = dspy.InputField(desc="Previous conversation messages")
    user_message = dspy.InputField(desc="Current user message")
    system_prompt = dspy.InputField(desc="System instructions for the assistant")
    
    response = dspy.OutputField(desc="Assistant's response to the user")
    

class ChatbotAgent:
    """
    DSPy-powered chatbot agent that maintains conversation context
    and generates responses using Google Gemini.
    """
    
    def __init__(self, config: ChatbotConfig):
        self.config = config
        self.dspy_config = DSPyConfig(
            model=config.model,
            temperature=config.temperature,
            max_tokens=config.max_tokens
        )
        self.agent = DSPyAgent(self.dspy_config)
        self.conversation_module = dspy.ChainOfThought(ConversationSignature)
        
        logger.info("Initialized ChatbotAgent", 
                   model=config.model,
                   personality=config.personality)
    
    async def generate_response(self, 
                              message: str, 
                              conversation_history: List[Dict[str, str]],
                              system_prompt: Optional[str] = None) -> str:
        """
        Generate a response to the user's message considering conversation history.
        
        Args:
            message: The user's current message
            conversation_history: List of previous messages
            system_prompt: Optional override for system prompt
            
        Returns:
            The assistant's response
        """
        try:
            # Use provided system prompt or default from config
            prompt = system_prompt or self.config.system_prompt or self._get_default_prompt()
            
            # Format conversation history
            history_text = self._format_conversation_history(conversation_history)
            
            # Generate response using DSPy
            result = self.conversation_module(
                conversation_history=history_text,
                user_message=message,
                system_prompt=prompt
            )
            
            return result.response
            
        except Exception as e:
            logger.error("Error generating response", error=str(e))
            raise
    
    def _format_conversation_history(self, history: List[Dict[str, str]]) -> str:
        """Format conversation history for the prompt."""
        if not history:
            return "No previous conversation."
        
        # Take only the last N messages based on conversation window
        recent_history = history[-self.config.conversation_window:]
        
        formatted = []
        for msg in recent_history:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            formatted.append(f"{role.capitalize()}: {content}")
        
        return "\n".join(formatted)
    
    def _get_default_prompt(self) -> str:
        """Get default system prompt based on personality."""
        default_prompts = {
            "default": "You are a helpful AI assistant. Be conversational, informative, and friendly.",
            "creative": "You are a creative AI companion. Be imaginative, use vivid language, and encourage creative thinking.",
            "technical": "You are a technical AI expert. Provide accurate technical information with examples when appropriate.",
            "casual": "You are a friendly chat buddy. Be casual, use appropriate humor, and keep conversations light and enjoyable."
        }
        
        return default_prompts.get(self.config.personality, default_prompts["default"])
    
    def update_config(self, **kwargs):
        """Update chatbot configuration dynamically."""
        for key, value in kwargs.items():
            if hasattr(self.config, key):
                setattr(self.config, key, value)
                
        # Update DSPy config if model settings changed
        if any(key in kwargs for key in ["model", "temperature", "max_tokens"]):
            self.dspy_config = DSPyConfig(
                model=self.config.model,
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens
            )
            self.agent = DSPyAgent(self.dspy_config)


@dspy_worker("chatbot-worker", model="gemini/gemini-1.5-flash")
async def chatbot_worker(context: Dict[str, Any]) -> Dict[str, Any]:
    """
    MultiAgents worker implementation for the chatbot.
    
    This worker can be used in workflows for automated conversations
    or integrated with the event bus for distributed chat handling.
    """
    # Extract parameters
    message = context.get("message", "")
    conversation_history = context.get("conversation_history", [])
    personality = context.get("personality", "default")
    system_prompt = context.get("system_prompt")
    
    # Create chatbot instance
    config = ChatbotConfig(
        personality=personality,
        system_prompt=system_prompt
    )
    chatbot = ChatbotAgent(config)
    
    # Generate response
    response = await chatbot.generate_response(
        message=message,
        conversation_history=conversation_history,
        system_prompt=system_prompt
    )
    
    # Return structured result
    return {
        "response": response,
        "timestamp": datetime.now().isoformat(),
        "model": config.model,
        "personality": personality,
        "message_length": len(message),
        "response_length": len(response)
    }