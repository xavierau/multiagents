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
    print("=" * 40)
    print("1. Simple Workflow Example")
    print("2. E-commerce Order Processing")
    print("3. Monitoring Demonstration")
    print("4. Diagram Generation Demo")
    print("5. Exit")
    print("=" * 40)

async def run_simple_workflow():
    """Run the simple workflow example."""
    # Add parent directory to path to import multiagents package
    parent_dir = project_root.parent
    if str(parent_dir) not in sys.path:
        sys.path.insert(0, str(parent_dir))
    from multiagents.examples.simple_workflow import main
    await main()

async def run_ecommerce_example():
    """Run the e-commerce example."""
    # Add parent directory to path to import multiagents package
    parent_dir = project_root.parent
    if str(parent_dir) not in sys.path:
        sys.path.insert(0, str(parent_dir))
    from multiagents.examples.ecommerce_order.main import main
    await main()

async def run_monitoring_demo():
    """Run the monitoring demonstration."""
    # Add parent directory to path to import multiagents package
    parent_dir = project_root.parent
    if str(parent_dir) not in sys.path:
        sys.path.insert(0, str(parent_dir))
    from multiagents.examples.monitoring_example import main
    await main()

def run_diagram_demo():
    """Run the diagram generation demo."""
    # Add parent directory to path to import multiagents package
    parent_dir = project_root.parent
    if str(parent_dir) not in sys.path:
        sys.path.insert(0, str(parent_dir))
    from multiagents.examples.ecommerce_order.diagram_demo import main
    main()

async def main():
    """Main menu and example runner."""
    print("⚠️  Make sure Redis is running on localhost:6379\n")
    
    while True:
        show_menu()
        try:
            choice = input("Enter your choice (1-5): ").strip()
            
            if choice == "1":
                print("\n🔄 Running Simple Workflow Example...")
                await run_simple_workflow()
            elif choice == "2":
                print("\n🛒 Running E-commerce Order Processing...")
                await run_ecommerce_example()
            elif choice == "3":
                print("\n📊 Running Monitoring Demonstration...")
                await run_monitoring_demo()
            elif choice == "4":
                print("\n🎨 Running Diagram Generation Demo...")
                run_diagram_demo()
            elif choice == "5":
                print("👋 Goodbye!")
                break
            else:
                print("❌ Invalid choice. Please enter 1-5.")
                
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