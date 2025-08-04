"""
Interactive CLI for Smart Research Assistant.

This provides a user-friendly command-line interface for interacting with
the multi-agent research system.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../'))

import asyncio
from typing import Dict, Any, Optional
from datetime import datetime
import argparse

from simple_workflow import SimpleResearchWorkflow, run_research_query


class ResearchAssistantCLI:
    """Interactive CLI for the Smart Research Assistant."""
    
    def __init__(self):
        self.workflow = SimpleResearchWorkflow()
        self.session_history: Dict[str, Dict[str, Any]] = {}
        self.current_user = "cli_user"
        
    def print_banner(self):
        """Print the application banner."""
        print("""
╔═══════════════════════════════════════════════════════════════════════════════╗
║                        🧠 Smart Research Assistant 🧠                        ║
║                                                                               ║
║  Multi-Agent AI Research System powered by DSPy and Gemini LLM               ║
║  Features: Research • Analysis • Calculations • Interactive Clarification    ║
╚═══════════════════════════════════════════════════════════════════════════════╝
""")
        
    def print_help(self):
        """Print available commands."""
        print("""
📋 Available Commands:
──────────────────────────────────────────────────────────────────────────────
  research <question>     - Ask a research question
  history                 - Show session history  
  clear                   - Clear screen
  help                    - Show this help message
  quit/exit              - Exit the application
  
💡 Example Questions:
──────────────────────────────────────────────────────────────────────────────  
  • What's the ROI of investing $10,000 in renewable energy stocks for 5 years?
  • Analyze the growth trends in solar energy investments
  • Calculate compound interest on $5,000 at 7% for 3 years
  • Compare Tesla vs NIO stock performance
  • What are the best ESG investment opportunities in 2024?
""")
    
    def format_response_for_cli(self, response: Dict[str, Any]) -> str:
        """Format the agent response for CLI display."""
        if not response or "response" not in response:
            return "❌ No response received"
        
        agent_response = response["response"]
        
        # Check if this is a conversational response
        if response.get("is_conversational", False):
            return self.format_conversational_response(response)
        
        formatted_response = agent_response.get("formatted_response", "")
        executive_summary = agent_response.get("executive_summary", "")
        
        # Build CLI-friendly output
        output = []
        
        # Executive Summary
        if executive_summary:
            output.append("📋 Executive Summary:")
            output.append("─" * 50)
            output.append(executive_summary)
            output.append("")
        
        # Full Response (truncated for CLI)
        if formatted_response:
            output.append("📄 Detailed Analysis:")
            output.append("─" * 50)
            
            # Split response into sections
            lines = formatted_response.split('\n')
            current_section = []
            
            for line in lines:
                if line.startswith('##'):
                    # New section
                    if current_section:
                        output.extend(current_section[:15])  # Limit lines per section
                        if len(current_section) > 15:
                            output.append(f"   ... ({len(current_section) - 15} more lines)")
                        output.append("")
                        current_section = []
                    
                    # Section header
                    section_title = line.replace('##', '').strip()
                    output.append(f"▶ {section_title}")
                    output.append("")
                else:
                    current_section.append(line)
            
            # Add last section
            if current_section:
                output.extend(current_section[:15])
                if len(current_section) > 15:
                    output.append(f"   ... ({len(current_section) - 15} more lines)")
        
        # Metadata
        metadata = response.get("metadata", {})
        if metadata and metadata.get("interaction_type") != "conversational":
            output.append("")
            output.append("📊 Processing Details:")
            output.append("─" * 30)
            output.append(f"  • Processing Steps: {metadata.get('processing_steps', 'Unknown')}")
            output.append(f"  • Had Clarification: {'✓' if metadata.get('had_clarification') else '✗'}")
            output.append(f"  • Had Analysis: {'✓' if metadata.get('had_analysis') else '✗'}")
            output.append(f"  • Completed: {metadata.get('completed_at', 'Unknown')}")
            output.append(f"  • Session ID: {response.get('session_id', 'Unknown')}")
        
        return '\n'.join(output)
    
    def format_conversational_response(self, response: Dict[str, Any]) -> str:
        """Format conversational responses for CLI display."""
        agent_response = response["response"]
        formatted_response = agent_response.get("formatted_response", "")
        suggested_actions = agent_response.get("suggested_actions", [])
        suggested_topics = agent_response.get("suggested_research_topics", [])
        
        output = []
        
        # Main conversational response
        if formatted_response:
            output.append(formatted_response)
            
        # Suggested actions
        if suggested_actions:
            output.append("")
            output.append("💡 What you can do next:")
            output.append("─" * 30)
            for i, action in enumerate(suggested_actions[:4], 1):
                output.append(f"  {i}. {action}")
        
        # Suggested research topics
        if suggested_topics:
            output.append("")
            output.append("🔍 Try researching:")
            output.append("─" * 20)
            for i, topic in enumerate(suggested_topics[:3], 1):
                output.append(f"  • {topic}")
        
        return '\n'.join(output)
    
    def print_session_history(self):
        """Print session history."""
        if not self.session_history:
            print("📚 No research sessions yet. Ask a question to get started!")
            return
        
        print("\n📚 Research Session History:")
        print("═" * 70)
        
        for i, (session_id, session_data) in enumerate(self.session_history.items(), 1):
            question = session_data.get("question", "Unknown question")
            timestamp = session_data.get("timestamp", "Unknown time")
            
            # Truncate long questions
            if len(question) > 50:
                question = question[:47] + "..."
            
            print(f"{i:2d}. [{timestamp}] {question}")
            print(f"    Session: {session_id}")
        
        print("\n💡 Use 'research <question>' to start a new research session")
    
    async def process_research_command(self, question: str) -> bool:
        """Process a research command."""
        if not question.strip():
            print("❌ Please provide a research question.")
            print("   Example: research What's the ROI of renewable energy investments?")
            return False
        
        print(f"\n🔍 Researching: {question}")
        print("═" * (15 + len(question)))
        print("⏳ Processing your request... (this may take 30-60 seconds)")
        
        try:
            # Run the research workflow
            result = await run_research_query(question, self.current_user)
            
            if "error" in result:
                print(f"\n❌ Research failed: {result['error']}")
                return False
            
            # Store in history
            session_id = result.get("session_id", "unknown")
            self.session_history[session_id] = {
                "question": question,
                "result": result,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            
            # Format and display result
            formatted_output = self.format_response_for_cli(result)
            print(f"\n✅ Research Complete!")
            print("═" * 70)
            print(formatted_output)
            
            return True
            
        except Exception as e:
            print(f"\n❌ Unexpected error: {e}")
            return False
    
    def process_command(self, command: str) -> bool:
        """Process a user command. Returns False if should exit."""
        command = command.strip()
        
        if not command:
            return True
        
        # Parse command
        parts = command.split(' ', 1)
        cmd = parts[0].lower()
        args = parts[1] if len(parts) > 1 else ""
        
        if cmd in ['quit', 'exit', 'q']:
            print("\n👋 Thank you for using Smart Research Assistant!")
            return False
        
        elif cmd in ['help', 'h', '?']:
            self.print_help()
        
        elif cmd == 'clear':
            os.system('clear' if os.name == 'posix' else 'cls')
            self.print_banner()
        
        elif cmd == 'history':
            self.print_session_history()
        
        elif cmd == 'research':
            # Run async research command
            asyncio.create_task(self.handle_research_async(args))
        
        else:
            # Treat the entire input as a research question
            asyncio.create_task(self.handle_research_async(command))
        
        return True
    
    async def handle_research_async(self, question: str):
        """Handle research command asynchronously."""
        await self.process_research_command(question)
    
    def run_interactive(self):
        """Run the interactive CLI."""
        self.print_banner()
        print("🚀 Welcome! Type 'help' for commands or just ask a research question.")
        print("💡 Pro tip: You can ask questions directly without typing 'research' first.")
        
        try:
            while True:
                try:
                    # Get user input
                    user_input = input("\n🧠 Research Assistant > ").strip()
                    
                    if not user_input:
                        continue
                    
                    # Process command
                    if not self.process_command(user_input):
                        break
                    
                except KeyboardInterrupt:
                    print("\n\n👋 Goodbye! Thanks for using Smart Research Assistant!")
                    break
                except EOFError:
                    print("\n\n👋 Goodbye! Thanks for using Smart Research Assistant!")
                    break
        except Exception as e:
            print(f"\n❌ CLI Error: {e}")


async def run_single_query(question: str, verbose: bool = False) -> None:
    """Run a single research query (non-interactive mode)."""
    print("🧠 Smart Research Assistant - Single Query Mode")
    print("=" * 60)
    
    if verbose:
        print(f"📝 Question: {question}")
        print("⏳ Processing...")
    
    try:
        result = await run_research_query(question, "single_query_user")
        
        if "error" in result:
            print(f"❌ Error: {result['error']}")
            return
        
        # Extract and display response
        response = result.get("response", {})
        executive_summary = response.get("executive_summary", "")
        formatted_response = response.get("formatted_response", "")
        
        if executive_summary:
            print(f"\n📋 Summary: {executive_summary}")
        
        if formatted_response and verbose:
            print(f"\n📄 Full Response:\n{formatted_response}")
        
        # Show metadata
        metadata = result.get("metadata", {})
        if verbose and metadata:
            print(f"\n📊 Metadata:")
            print(f"  Steps: {metadata.get('processing_steps', 0)}")
            print(f"  Had Analysis: {metadata.get('had_analysis', False)}")
            print(f"  Session: {result.get('session_id', 'Unknown')}")
    
    except Exception as e:
        print(f"❌ Error: {e}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Smart Research Assistant - Multi-Agent AI Research System",
        formatter_class=argparse.RawTextHelpFormatter
    )
    
    parser.add_argument(
        '--query', '-q',
        type=str,
        help='Run a single research query (non-interactive mode)'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Show detailed output (only in single query mode)'
    )
    
    parser.add_argument(
        '--examples',
        action='store_true',
        help='Show example research questions'
    )
    
    args = parser.parse_args()
    
    if args.examples:
        print("""
🧠 Smart Research Assistant - Example Questions
═══════════════════════════════════════════════════════════

💰 Financial Analysis:
  • What's the ROI of investing $10,000 in renewable energy stocks for 5 years?
  • Calculate compound interest on $5,000 at 7% annually for 3 years
  • Compare the risk-return profile of Tesla vs Apple stock
  
📈 Market Research:
  • Analyze growth trends in solar energy investments
  • What are the best ESG investment opportunities in 2024?
  • Research the impact of AI on healthcare stock valuations
  
🔢 Calculations:
  • Calculate the break-even point for a $50,000 business investment
  • What's the present value of $100,000 received in 10 years at 5% discount rate?
  • Analyze loan payment options for $250,000 at different interest rates
  
🌍 General Research:
  • Research the latest developments in quantum computing
  • Analyze the environmental impact of cryptocurrency mining
  • What are the emerging trends in sustainable agriculture?
        """)
        return
    
    if args.query:
        # Single query mode
        asyncio.run(run_single_query(args.query, args.verbose))
    else:
        # Interactive mode
        cli = ResearchAssistantCLI()
        # Need to run async methods in the event loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        # Monkey patch to handle async research
        original_process_command = cli.process_command
        
        def sync_process_command(command: str) -> bool:
            parts = command.strip().split(' ', 1)
            cmd = parts[0].lower()
            args = parts[1] if len(parts) > 1 else ""
            
            if cmd == 'research' or (cmd not in ['quit', 'exit', 'q', 'help', 'h', '?', 'clear', 'history']):
                # Handle research command synchronously
                question = args if cmd == 'research' else command
                if question.strip():
                    loop.run_until_complete(cli.process_research_command(question))
                return True
            else:
                return original_process_command(command)
        
        cli.process_command = sync_process_command
        cli.run_interactive()


if __name__ == "__main__":
    main()