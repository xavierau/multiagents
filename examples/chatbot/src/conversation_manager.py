"""
Conversation Manager for maintaining chat history and context.

This module handles conversation state, history management,
and persistence for the chatbot.
"""

import json
import os
from datetime import datetime
from typing import List, Dict, Any, Optional
from pathlib import Path
import structlog


logger = structlog.get_logger()


class ConversationManager:
    """
    Manages conversation history, context, and persistence.
    """
    
    def __init__(self, history_dir: str = "./conversations", max_history: int = 100):
        self.history_dir = Path(history_dir)
        self.history_dir.mkdir(parents=True, exist_ok=True)
        self.max_history = max_history
        self.conversation_id = self._generate_conversation_id()
        self.messages: List[Dict[str, Any]] = []
        self.metadata: Dict[str, Any] = {
            "id": self.conversation_id,
            "started_at": datetime.now().isoformat(),
            "personality": "default",
            "model": "gemini/gemini-1.5-flash"
        }
        
        logger.info("Initialized ConversationManager", 
                   conversation_id=self.conversation_id,
                   history_dir=str(self.history_dir))
    
    def add_message(self, role: str, content: str, metadata: Optional[Dict] = None):
        """
        Add a message to the conversation history.
        
        Args:
            role: Either "user" or "assistant"
            content: The message content
            metadata: Optional metadata for the message
        """
        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat(),
            "metadata": metadata or {}
        }
        
        self.messages.append(message)
        
        # Trim history if it exceeds max length
        if len(self.messages) > self.max_history:
            self.messages = self.messages[-self.max_history:]
        
        logger.debug("Added message to conversation", 
                    role=role, 
                    message_length=len(content))
    
    def get_conversation_history(self, last_n: Optional[int] = None) -> List[Dict[str, str]]:
        """
        Get conversation history for context.
        
        Args:
            last_n: Number of recent messages to return (None for all)
            
        Returns:
            List of messages with role and content
        """
        messages = self.messages if last_n is None else self.messages[-last_n:]
        
        # Return simplified format for the chatbot
        return [
            {"role": msg["role"], "content": msg["content"]} 
            for msg in messages
        ]
    
    def get_full_conversation(self) -> Dict[str, Any]:
        """Get complete conversation with metadata."""
        return {
            "metadata": self.metadata,
            "messages": self.messages,
            "message_count": len(self.messages),
            "duration": self._calculate_duration()
        }
    
    def save_conversation(self, filename: Optional[str] = None) -> str:
        """
        Save conversation to a JSON file.
        
        Args:
            filename: Optional custom filename
            
        Returns:
            Path to saved file
        """
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"conversation_{timestamp}.json"
        
        filepath = self.history_dir / filename
        
        conversation_data = self.get_full_conversation()
        conversation_data["saved_at"] = datetime.now().isoformat()
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(conversation_data, f, indent=2, ensure_ascii=False)
        
        logger.info("Saved conversation", filepath=str(filepath))
        return str(filepath)
    
    def load_conversation(self, filepath: str):
        """
        Load a conversation from a JSON file.
        
        Args:
            filepath: Path to the conversation file
        """
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        self.messages = data.get("messages", [])
        self.metadata = data.get("metadata", {})
        self.conversation_id = self.metadata.get("id", self._generate_conversation_id())
        
        logger.info("Loaded conversation", 
                   conversation_id=self.conversation_id,
                   message_count=len(self.messages))
    
    def clear_history(self):
        """Clear conversation history but keep metadata."""
        self.messages.clear()
        self.metadata["cleared_at"] = datetime.now().isoformat()
        logger.info("Cleared conversation history")
    
    def update_metadata(self, **kwargs):
        """Update conversation metadata."""
        self.metadata.update(kwargs)
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get conversation statistics."""
        if not self.messages:
            return {
                "message_count": 0,
                "user_messages": 0,
                "assistant_messages": 0,
                "avg_message_length": 0,
                "duration_seconds": 0
            }
        
        user_messages = [m for m in self.messages if m["role"] == "user"]
        assistant_messages = [m for m in self.messages if m["role"] == "assistant"]
        
        all_lengths = [len(m["content"]) for m in self.messages]
        
        return {
            "message_count": len(self.messages),
            "user_messages": len(user_messages),
            "assistant_messages": len(assistant_messages),
            "avg_message_length": sum(all_lengths) / len(all_lengths),
            "avg_user_length": sum(len(m["content"]) for m in user_messages) / max(len(user_messages), 1),
            "avg_assistant_length": sum(len(m["content"]) for m in assistant_messages) / max(len(assistant_messages), 1),
            "duration_seconds": self._calculate_duration()
        }
    
    def export_as_text(self, include_metadata: bool = True) -> str:
        """Export conversation as readable text."""
        lines = []
        
        if include_metadata:
            lines.append(f"=== Conversation {self.conversation_id} ===")
            lines.append(f"Started: {self.metadata.get('started_at', 'Unknown')}")
            lines.append(f"Personality: {self.metadata.get('personality', 'default')}")
            lines.append(f"Model: {self.metadata.get('model', 'Unknown')}")
            lines.append("=" * 40)
            lines.append("")
        
        for msg in self.messages:
            timestamp = msg.get("timestamp", "")
            role = msg["role"].upper()
            content = msg["content"]
            
            lines.append(f"[{timestamp}] {role}:")
            lines.append(content)
            lines.append("")
        
        return "\n".join(lines)
    
    def _generate_conversation_id(self) -> str:
        """Generate a unique conversation ID."""
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        return f"conv_{timestamp}"
    
    def _calculate_duration(self) -> float:
        """Calculate conversation duration in seconds."""
        if not self.messages:
            return 0.0
        
        try:
            start_time = datetime.fromisoformat(self.metadata.get("started_at", ""))
            last_message_time = datetime.fromisoformat(self.messages[-1]["timestamp"])
            return (last_message_time - start_time).total_seconds()
        except (ValueError, KeyError):
            return 0.0