"""
Unit tests for the MultiAgents Chatbot components.
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.chatbot_agent import ChatbotAgent, ChatbotConfig
from src.conversation_manager import ConversationManager
from src.config_loader import load_config, load_personality, PersonalityConfig


class TestChatbotAgent:
    """Test ChatbotAgent functionality."""
    
    @pytest.fixture
    def chatbot_config(self):
        """Create test chatbot configuration."""
        return ChatbotConfig(
            model="gemini/gemini-1.5-flash",
            temperature=0.7,
            max_tokens=100,
            personality="default"
        )
    
    @pytest.fixture
    def chatbot(self, chatbot_config):
        """Create test chatbot instance."""
        with patch('src.chatbot_agent.DSPyAgent'):
            return ChatbotAgent(chatbot_config)
    
    @pytest.mark.asyncio
    async def test_generate_response(self, chatbot):
        """Test response generation."""
        # Mock the DSPy module
        chatbot.conversation_module = AsyncMock()
        chatbot.conversation_module.return_value = Mock(response="Test response")
        
        response = await chatbot.generate_response(
            message="Hello",
            conversation_history=[]
        )
        
        assert response == "Test response"
        chatbot.conversation_module.assert_called_once()
    
    def test_format_conversation_history(self, chatbot):
        """Test conversation history formatting."""
        history = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there!"}
        ]
        
        formatted = chatbot._format_conversation_history(history)
        
        assert "User: Hello" in formatted
        assert "Assistant: Hi there!" in formatted
    
    def test_update_config(self, chatbot):
        """Test configuration updates."""
        chatbot.update_config(temperature=0.9, personality="creative")
        
        assert chatbot.config.temperature == 0.9
        assert chatbot.config.personality == "creative"


class TestConversationManager:
    """Test ConversationManager functionality."""
    
    @pytest.fixture
    def conversation(self, tmp_path):
        """Create test conversation manager."""
        return ConversationManager(history_dir=str(tmp_path))
    
    def test_add_message(self, conversation):
        """Test adding messages to conversation."""
        conversation.add_message("user", "Hello")
        conversation.add_message("assistant", "Hi there!")
        
        assert len(conversation.messages) == 2
        assert conversation.messages[0]["role"] == "user"
        assert conversation.messages[0]["content"] == "Hello"
    
    def test_get_conversation_history(self, conversation):
        """Test retrieving conversation history."""
        conversation.add_message("user", "Message 1")
        conversation.add_message("assistant", "Response 1")
        conversation.add_message("user", "Message 2")
        
        # Get all history
        history = conversation.get_conversation_history()
        assert len(history) == 3
        
        # Get last 2 messages
        recent = conversation.get_conversation_history(last_n=2)
        assert len(recent) == 2
        assert recent[0]["content"] == "Response 1"
    
    def test_save_and_load_conversation(self, conversation, tmp_path):
        """Test saving and loading conversations."""
        # Add some messages
        conversation.add_message("user", "Test message")
        conversation.add_message("assistant", "Test response")
        
        # Save conversation
        filepath = conversation.save_conversation("test_conv.json")
        assert Path(filepath).exists()
        
        # Create new conversation and load
        new_conversation = ConversationManager(history_dir=str(tmp_path))
        new_conversation.load_conversation(filepath)
        
        assert len(new_conversation.messages) == 2
        assert new_conversation.messages[0]["content"] == "Test message"
    
    def test_clear_history(self, conversation):
        """Test clearing conversation history."""
        conversation.add_message("user", "Hello")
        conversation.add_message("assistant", "Hi")
        
        conversation.clear_history()
        
        assert len(conversation.messages) == 0
        assert "cleared_at" in conversation.metadata
    
    def test_get_statistics(self, conversation):
        """Test conversation statistics."""
        conversation.add_message("user", "Hello")
        conversation.add_message("assistant", "Hi there! How can I help?")
        conversation.add_message("user", "What's the weather?")
        
        stats = conversation.get_statistics()
        
        assert stats["message_count"] == 3
        assert stats["user_messages"] == 2
        assert stats["assistant_messages"] == 1
        assert stats["avg_message_length"] > 0


class TestConfigLoader:
    """Test configuration loading functionality."""
    
    def test_load_personality(self):
        """Test loading a personality configuration."""
        # Create a mock personality config
        with patch('src.config_loader.load_yaml_config') as mock_load:
            mock_load.return_value = {
                "personalities": {
                    "test": {
                        "name": "Test Bot",
                        "description": "A test personality",
                        "system_prompt": "You are a test bot",
                        "temperature": 0.5,
                        "traits": ["trait1", "trait2"]
                    }
                }
            }
            
            personality = load_personality("test")
            
            assert personality is not None
            assert personality.name == "Test Bot"
            assert personality.temperature == 0.5
            assert len(personality.traits) == 2
    
    def test_validate_environment(self):
        """Test environment validation."""
        with patch.dict('os.environ', {'GOOGLE_API_KEY': 'test-key'}):
            validation = validate_environment()
            assert validation['GOOGLE_API_KEY'] is True
        
        with patch.dict('os.environ', {}, clear=True):
            validation = validate_environment()
            assert validation.get('GOOGLE_API_KEY') is False


@pytest.mark.asyncio
async def test_chatbot_worker():
    """Test the chatbot worker function."""
    from src.chatbot_agent import chatbot_worker
    
    with patch('src.chatbot_agent.ChatbotAgent') as mock_agent_class:
        mock_agent = Mock()
        mock_agent.generate_response = AsyncMock(return_value="Test response")
        mock_agent_class.return_value = mock_agent
        
        context = {
            "message": "Hello",
            "conversation_history": [],
            "personality": "default"
        }
        
        result = await chatbot_worker(context)
        
        assert result["response"] == "Test response"
        assert "timestamp" in result
        assert result["personality"] == "default"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])