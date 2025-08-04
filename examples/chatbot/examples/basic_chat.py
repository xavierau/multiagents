#!/usr/bin/env python3
"""
Basic example of using the chatbot programmatically.

This shows how to integrate the chatbot into your own applications.
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.chatbot_agent import ChatbotAgent, ChatbotConfig
from src.conversation_manager import ConversationManager


async def basic_chat_example():
    """Simple example of using the chatbot."""
    
    # Create chatbot with default configuration
    config = ChatbotConfig(
        model="gemini/gemini-1.5-flash",
        temperature=0.7,
        personality="default"
    )
    
    chatbot = ChatbotAgent(config)
    conversation = ConversationManager()
    
    print("🤖 Basic Chatbot Example")
    print("-" * 40)
    
    # Example conversation
    messages = [
        "Hello! What can you help me with today?",
        "Can you explain what the MultiAgents framework is?",
        "How does DSPy integration work in this context?",
        "Thanks for the explanation!"
    ]
    
    for message in messages:
        print(f"\n👤 User: {message}")
        
        # Add to conversation history
        conversation.add_message("user", message)
        
        # Get conversation history for context
        history = conversation.get_conversation_history()
        
        # Generate response
        response = await chatbot.generate_response(
            message=message,
            conversation_history=history
        )
        
        # Add response to history
        conversation.add_message("assistant", response)
        
        print(f"🤖 Assistant: {response}")
    
    # Show conversation statistics
    print("\n" + "=" * 40)
    print("Conversation Statistics:")
    stats = conversation.get_statistics()
    print(f"  Total messages: {stats['message_count']}")
    print(f"  Average message length: {stats['avg_message_length']:.1f} chars")
    
    # Save conversation
    filepath = conversation.save_conversation("basic_example.json")
    print(f"\n✅ Conversation saved to: {filepath}")


async def streaming_example():
    """Example with simulated streaming responses."""
    
    config = ChatbotConfig(personality="creative")
    chatbot = ChatbotAgent(config)
    
    print("\n\n🎨 Creative Writing Example")
    print("-" * 40)
    
    prompt = "Write a short haiku about artificial intelligence"
    print(f"\n👤 User: {prompt}")
    
    # Generate response
    response = await chatbot.generate_response(
        message=prompt,
        conversation_history=[]
    )
    
    # Simulate streaming
    print("🤖 Assistant: ", end="", flush=True)
    for char in response:
        print(char, end="", flush=True)
        await asyncio.sleep(0.03)  # Typing effect
    print()


async def multi_personality_example():
    """Example showing different personalities."""
    
    personalities = ["technical", "creative", "casual"]
    question = "What is machine learning?"
    
    print("\n\n🎭 Multi-Personality Example")
    print("-" * 40)
    print(f"Question: {question}")
    
    for personality in personalities:
        print(f"\n--- {personality.upper()} Personality ---")
        
        config = ChatbotConfig(personality=personality)
        chatbot = ChatbotAgent(config)
        
        response = await chatbot.generate_response(
            message=question,
            conversation_history=[]
        )
        
        print(f"Response: {response[:200]}...")  # Show first 200 chars


if __name__ == "__main__":
    # Run all examples
    asyncio.run(basic_chat_example())
    asyncio.run(streaming_example())
    asyncio.run(multi_personality_example())