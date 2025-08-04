#!/usr/bin/env python3
"""
Personality demonstration for the MultiAgents chatbot.

Shows how different personalities respond to various prompts.
"""

import asyncio
import sys
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.chatbot_agent import ChatbotAgent, ChatbotConfig
from src.config_loader import load_personalities

console = Console()


async def personality_showcase():
    """Showcase different chatbot personalities."""
    
    # Load all personalities
    personalities = load_personalities("../config/personalities.yaml")
    
    # Test prompts
    test_prompts = [
        "Tell me a joke",
        "Explain quantum computing",
        "What should I have for dinner?",
        "Help me debug this Python code: print('Hello' + 5)",
        "Write a story opening"
    ]
    
    console.print("[bold magenta]🎭 Chatbot Personality Showcase[/bold magenta]\n")
    
    for prompt in test_prompts:
        console.print(f"\n[bold yellow]Prompt: {prompt}[/bold yellow]")
        console.print("-" * 60)
        
        responses = []
        
        for name, personality in personalities.items():
            # Create chatbot with specific personality
            config = ChatbotConfig(
                personality=name,
                system_prompt=personality.system_prompt,
                temperature=personality.temperature
            )
            chatbot = ChatbotAgent(config)
            
            # Generate response
            try:
                response = await chatbot.generate_response(
                    message=prompt,
                    conversation_history=[]
                )
                
                # Truncate long responses
                if len(response) > 150:
                    response = response[:147] + "..."
                
                responses.append((name, response))
                
            except Exception as e:
                responses.append((name, f"Error: {str(e)}"))
        
        # Display responses in a nice format
        for name, response in responses:
            personality = personalities[name]
            
            panel = Panel(
                response,
                title=f"[bold cyan]{personality.name}[/bold cyan]",
                subtitle=f"[dim]{personality.description}[/dim]",
                border_style="cyan" if name == "default" else "green"
            )
            console.print(panel)
        
        # Wait a bit between prompts
        await asyncio.sleep(1)


async def personality_comparison():
    """Compare personalities side by side."""
    
    console.print("\n[bold magenta]📊 Personality Comparison[/bold magenta]\n")
    
    personalities = load_personalities("../config/personalities.yaml")
    
    # Create comparison table
    table = Table(title="Personality Traits")
    table.add_column("Personality", style="cyan", width=15)
    table.add_column("Temperature", style="yellow", width=12)
    table.add_column("Key Traits", style="green", width=50)
    
    for name, personality in personalities.items():
        traits = "\n".join(f"• {trait}" for trait in personality.traits[:3])
        table.add_row(
            personality.name,
            f"{personality.temperature}",
            traits
        )
    
    console.print(table)


async def interactive_personality_test():
    """Interactive personality testing."""
    
    console.print("\n[bold magenta]🧪 Interactive Personality Test[/bold magenta]\n")
    console.print("Enter a prompt to see how each personality responds.")
    console.print("Type 'quit' to exit.\n")
    
    personalities = load_personalities("../config/personalities.yaml")
    
    while True:
        # Get user input
        prompt = console.input("[bold cyan]Your prompt:[/bold cyan] ")
        
        if prompt.lower() in ['quit', 'exit']:
            break
        
        console.print("\n[dim]Generating responses...[/dim]\n")
        
        # Generate responses from each personality
        for name, personality in personalities.items():
            config = ChatbotConfig(
                personality=name,
                system_prompt=personality.system_prompt,
                temperature=personality.temperature
            )
            chatbot = ChatbotAgent(config)
            
            try:
                with console.status(f"[dim]Thinking as {personality.name}...[/dim]"):
                    response = await chatbot.generate_response(
                        message=prompt,
                        conversation_history=[]
                    )
                
                # Display response
                console.print(f"[bold green]{personality.name}:[/bold green]")
                console.print(response)
                console.print()
                
            except Exception as e:
                console.print(f"[red]Error with {name}: {str(e)}[/red]")


if __name__ == "__main__":
    try:
        # Run showcase
        asyncio.run(personality_showcase())
        
        # Show comparison
        asyncio.run(personality_comparison())
        
        # Run interactive test
        asyncio.run(interactive_personality_test())
        
    except KeyboardInterrupt:
        console.print("\n[yellow]Demo interrupted[/yellow]")
    except Exception as e:
        console.print(f"\n[red]Error: {str(e)}[/red]")