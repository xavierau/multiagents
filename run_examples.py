#!/usr/bin/env python3
"""
Example runner script that sets up the Python path correctly.
Run this from the project root directory.
"""
import sys
import os
import asyncio
from pathlib import Path

# Fix Python path conflicts when running from within the multiagents directory
if '' in sys.path:
    sys.path.remove('')
if '.' in sys.path:
    sys.path.remove('.')

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def show_menu():
    """Show available examples."""
    print("🚀 MultiAgents Framework Examples")
    print("=" * 50)
    print("🤖 LLM-Powered Examples:")
    print("1. 💬 Smart Research Assistant (Conversational AI)")
    print("2. 🤖 Interactive Chatbot (Multi-personality AI)")
    print("")
    print("🔧 Core Framework Examples:")
    print("3. 📝 Simple Workflow Example")
    print("4. 🛒 E-commerce Order Processing")
    print("5. 📊 Monitoring Demonstration")
    print("6. 🎨 Diagram Generation Demo")
    print("")
    print("7. 🚪 Exit")
    print("=" * 50)

async def run_smart_research_assistant():
    """Run the Smart Research Assistant example."""
    try:
        from examples.smart_research_assistant.cli import main
        print("\n🔍 Starting Smart Research Assistant...")
        print("💡 Try asking: 'What are renewable energy trends?' or just say 'hi!'")
        print("⚠️  Note: Requires GOOGLE_API_KEY and GOOGLE_SEARCH_* environment variables")
        print("📖 See examples/smart_research_assistant/SETUP.md for configuration")
        print()
        await main()
    except ImportError as e:
        print(f"❌ Error importing Smart Research Assistant: {e}")
        print("💡 Make sure you're running from the project root directory")
    except Exception as e:
        print(f"❌ Error running Smart Research Assistant: {e}")

async def run_interactive_chatbot():
    """Run the Interactive Chatbot example."""
    try:
        from examples.chatbot.main import main
        print("\n🤖 Starting Interactive Chatbot...")
        print("💡 Try different personalities and conversation styles")
        print("⚠️  Note: Requires LLM API configuration (see examples/chatbot/README.md)")
        print()
        await main()
    except ImportError as e:
        print(f"❌ Error importing Interactive Chatbot: {e}")
        print("💡 Make sure you're running from the project root directory")
    except Exception as e:
        print(f"❌ Error running Interactive Chatbot: {e}")

async def run_simple_workflow():
    """Run the simple workflow example."""
    try:
        from examples.simple_workflow import main
        await main()
    except ImportError as e:
        print(f"❌ Error importing simple workflow: {e}")
        print("💡 Make sure you're running from the project root directory")
    except Exception as e:
        print(f"❌ Error running simple workflow: {e}")

async def run_ecommerce_example():
    """Run the e-commerce example."""
    try:
        from examples.ecommerce_order.main import main
        await main()
    except ImportError as e:
        print(f"❌ Error importing e-commerce example: {e}")
        print("💡 Make sure you're running from the project root directory")
    except Exception as e:
        print(f"❌ Error running e-commerce example: {e}")

async def run_monitoring_demo():
    """Run the monitoring demonstration."""
    try:
        from examples.monitoring_example import main
        await main()
    except ImportError as e:
        print(f"❌ Error importing monitoring demo: {e}")
        print("💡 Make sure you're running from the project root directory")
    except Exception as e:
        print(f"❌ Error running monitoring demo: {e}")

def run_diagram_demo():
    """Run the diagram generation demo."""
    try:
        from examples.ecommerce_order.diagram_demo import main
        main()
    except ImportError as e:
        print(f"❌ Error importing diagram demo: {e}")
        print("💡 Make sure you're running from the project root directory")  
    except Exception as e:
        print(f"❌ Error running diagram demo: {e}")

async def main():
    """Main menu and example runner."""
    print("🚀 MultiAgents Framework - LLM-Powered Multi-Agent System")
    print("⚠️  Prerequisites:")
    print("   • Redis running on localhost:6379")
    print("   • For LLM examples: API keys configured (see example READMEs)")
    print()
    
    while True:
        show_menu()
        try:
            choice = input("Enter your choice (1-7): ").strip()
            
            if choice == "1":
                print("\n💬 Running Smart Research Assistant...")
                await run_smart_research_assistant()
            elif choice == "2":
                print("\n🤖 Running Interactive Chatbot...")
                await run_interactive_chatbot()
            elif choice == "3":
                print("\n📝 Running Simple Workflow Example...")
                await run_simple_workflow()
            elif choice == "4":
                print("\n🛒 Running E-commerce Order Processing...")
                await run_ecommerce_example()
            elif choice == "5":
                print("\n📊 Running Monitoring Demonstration...")
                await run_monitoring_demo()
            elif choice == "6":
                print("\n🎨 Running Diagram Generation Demo...")
                run_diagram_demo()
            elif choice == "7":
                print("👋 Goodbye!")
                break
            else:
                print("❌ Invalid choice. Please enter 1-7.")
                
            input("\nPress Enter to continue...")
            print("\n")
            
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"❌ Error running example: {e}")
            input("\nPress Enter to continue...")

if __name__ == "__main__":
    asyncio.run(main())