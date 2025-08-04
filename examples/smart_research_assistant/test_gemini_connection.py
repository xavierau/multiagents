"""
Test script to verify Gemini connection and configuration.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../'))

from config.gemini_config import get_default_gemini_config
from multiagents.worker_sdk.dspy_wrapper import DSPyAgent


def test_gemini_connection():
    """Test basic Gemini connection."""
    print("🧪 Testing Gemini LLM connection...")
    
    try:
        # Get configuration
        config = get_default_gemini_config()
        print(f"✓ Configuration loaded: {config.model}")
        
        # Create DSPy agent
        dspy_config = config.to_dspy_config()
        agent = DSPyAgent(dspy_config)
        print("✓ DSPy agent created successfully")
        
        # Test basic signature
        signature = agent.create_signature("question", "answer")
        print("✓ DSPy signature created")
        
        # Test simple prediction
        print("\n🤖 Testing simple prediction...")
        result = agent.predict(signature, question="What is 2 + 2?")
        print(f"✓ Prediction successful: {result}")
        
        print("\n✅ Gemini connection test PASSED!")
        return True
        
    except Exception as e:
        print(f"\n❌ Gemini connection test FAILED: {e}")
        print("\nPlease ensure:")
        print("1. GOOGLE_API_KEY environment variable is set")
        print("2. API key has access to Gemini models")
        print("3. Internet connection is available")
        return False


if __name__ == "__main__":
    success = test_gemini_connection()
    sys.exit(0 if success else 1)