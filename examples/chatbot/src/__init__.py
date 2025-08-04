"""
MultiAgents Chatbot Example - Source Package

This package contains the core implementation of the DSPy-powered
chatbot with Google Gemini integration.
"""

from .chatbot_agent import ChatbotAgent, ChatbotConfig
from .cli_interface import ChatbotCLI
from .conversation_manager import ConversationManager
from .config_loader import load_config, load_personality

__all__ = [
    "ChatbotAgent",
    "ChatbotConfig", 
    "ChatbotCLI",
    "ConversationManager",
    "load_config",
    "load_personality",
]