"""
CLI Interface for the MultiAgents Chatbot.

Provides an interactive command-line interface with rich formatting
and conversation management.
"""

import asyncio
import sys
from typing import Optional, Dict, Any
from pathlib import Path
import click
from rich.console import Console
from rich.prompt import Prompt
from rich.panel import Panel
from rich.text import Text
from rich.live import Live
from rich.spinner import Spinner
from rich.markdown import Markdown
from rich.table import Table
import structlog
from datetime import datetime

from .chatbot_agent import ChatbotAgent, ChatbotConfig
from .conversation_manager import ConversationManager
from .config_loader import load_config, load_personality, validate_environment


logger = structlog.get_logger()
console = Console()


class ChatbotCLI:
    """
    Interactive CLI for the chatbot with rich formatting.
    """
    
    def __init__(self, config: Dict[str, Any], personality_name: str = "default"):
        self.config = config
        self.chatbot_config = self._create_chatbot_config(config, personality_name)
        self.chatbot = ChatbotAgent(self.chatbot_config)
        self.conversation = ConversationManager(
            history_dir=config.get("chatbot", {}).get("conversation", {}).get("history_dir", "./conversations"),
            max_history=config.get("chatbot", {}).get("conversation", {}).get("max_history_length", 100)
        )
        
        # CLI settings
        cli_config = config.get("chatbot", {}).get("cli", {})
        self.prompt_style = cli_config.get("prompt_style", "bold cyan")
        self.bot_style = cli_config.get("bot_style", "bold green")
        self.user_style = cli_config.get("user_style", "bold yellow")
        self.system_style = cli_config.get("system_style", "dim italic")
        
        # Response settings
        response_config = config.get("chatbot", {}).get("response", {})
        self.streaming_simulation = response_config.get("streaming_simulation", True)
        self.typing_speed = response_config.get("typing_speed", 0.03)
        self.thinking_indicator = response_config.get("thinking_indicator", True)
        
        self.running = False
        
    def _create_chatbot_config(self, config: Dict[str, Any], personality_name: str) -> ChatbotConfig:
        """Create ChatbotConfig from loaded configuration."""
        model_config = config.get("chatbot", {}).get("model", {})
        conversation_config = config.get("chatbot", {}).get("conversation", {})
        
        # Load personality
        personality = load_personality(personality_name)
        system_prompt = personality.system_prompt if personality else None
        temperature = personality.temperature if personality else model_config.get("temperature", 0.7)
        
        return ChatbotConfig(
            model=model_config.get("name", "gemini/gemini-1.5-flash"),
            temperature=temperature,
            max_tokens=model_config.get("max_tokens", 1000),
            personality=personality_name,
            system_prompt=system_prompt,
            conversation_window=conversation_config.get("context_window", 5)
        )
    
    async def run(self):
        """Run the interactive chat loop."""
        self.running = True
        
        # Clear screen if configured
        if self.config.get("chatbot", {}).get("cli", {}).get("clear_on_start", True):
            console.clear()
        
        # Show welcome message
        if self.config.get("chatbot", {}).get("cli", {}).get("welcome_message", True):
            self._show_welcome()
        
        # Main chat loop
        try:
            while self.running:
                # Get user input
                user_input = self._get_user_input()
                
                if user_input is None:
                    continue
                
                # Check for commands
                if user_input.startswith("/"):
                    await self._handle_command(user_input)
                    continue
                
                # Process regular message
                await self._process_message(user_input)
                
        except KeyboardInterrupt:
            self._show_goodbye()
        except Exception as e:
            logger.error("Unexpected error in chat loop", error=str(e))
            console.print(f"[red]Error: {str(e)}[/red]")
        
    def _show_welcome(self):
        """Display welcome message."""
        personality = load_personality(self.chatbot_config.personality)
        
        welcome_text = Text()
        welcome_text.append("🤖 Welcome to MultiAgents Chatbot\n", style="bold magenta")
        welcome_text.append(f"Model: {self.chatbot_config.model}\n", style=self.system_style)
        welcome_text.append(f"Personality: {personality.name if personality else 'Default'}\n", style=self.system_style)
        
        panel = Panel(
            welcome_text,
            title="[bold blue]MultiAgents Chatbot[/bold blue]",
            border_style="blue",
            padding=(1, 2)
        )
        
        console.print(panel)
        console.print(f"[{self.system_style}]Type '/help' for available commands[/{self.system_style}]\n")
        
        # Update conversation metadata
        self.conversation.update_metadata(
            personality=self.chatbot_config.personality,
            model=self.chatbot_config.model
        )
    
    def _show_goodbye(self):
        """Display goodbye message."""
        console.print("\n[bold magenta]👋 Thanks for chatting! Goodbye![/bold magenta]")
        
        # Show conversation statistics
        stats = self.conversation.get_statistics()
        if stats["message_count"] > 0:
            console.print(f"\n[{self.system_style}]Conversation Summary:[/{self.system_style}]")
            console.print(f"  Messages: {stats['message_count']}")
            console.print(f"  Duration: {stats['duration_seconds']:.1f} seconds")
            
            # Ask if user wants to save
            if Prompt.ask("\nSave this conversation?", choices=["y", "n"], default="n") == "y":
                filepath = self.conversation.save_conversation()
                console.print(f"[green]✓ Conversation saved to: {filepath}[/green]")
    
    def _get_user_input(self) -> Optional[str]:
        """Get input from user with rich prompt."""
        try:
            user_input = Prompt.ask(f"[{self.prompt_style}]You[/{self.prompt_style}]")
            return user_input.strip()
        except EOFError:
            self.running = False
            return None
    
    async def _process_message(self, message: str):
        """Process a user message and generate response."""
        # Add user message to conversation
        self.conversation.add_message("user", message)
        
        # Show user message
        console.print(f"[{self.user_style}]You:[/{self.user_style}] {message}")
        
        try:
            # Show thinking indicator
            if self.thinking_indicator:
                with Live(Spinner("dots", text="Thinking...", style=self.system_style), refresh_per_second=10):
                    response = await self._generate_response(message)
            else:
                response = await self._generate_response(message)
            
            # Add assistant response to conversation
            self.conversation.add_message("assistant", response)
            
            # Display response
            console.print(f"\n[{self.bot_style}]Assistant:[/{self.bot_style}]")
            
            if self.streaming_simulation:
                await self._simulate_typing(response)
            else:
                console.print(response)
            
            console.print()  # Empty line for spacing
            
        except Exception as e:
            error_msg = f"Sorry, I encountered an error: {str(e)}"
            console.print(f"[red]{error_msg}[/red]")
            self.conversation.add_message("assistant", error_msg, {"error": True})
    
    async def _generate_response(self, message: str) -> str:
        """Generate response using the chatbot agent."""
        conversation_history = self.conversation.get_conversation_history(
            last_n=self.chatbot_config.conversation_window
        )
        
        response = await self.chatbot.generate_response(
            message=message,
            conversation_history=conversation_history
        )
        
        return response
    
    async def _simulate_typing(self, text: str):
        """Simulate typing effect for response."""
        for char in text:
            console.print(char, end="")
            await asyncio.sleep(self.typing_speed)
    
    async def _handle_command(self, command: str):
        """Handle slash commands."""
        parts = command.split(maxsplit=1)
        cmd = parts[0].lower()
        args = parts[1] if len(parts) > 1 else ""
        
        if cmd in ["/exit", "/quit"]:
            self.running = False
            self._show_goodbye()
            
        elif cmd == "/clear":
            self.conversation.clear_history()
            console.clear()
            console.print("[green]✓ Conversation history cleared[/green]")
            
        elif cmd == "/save":
            filename = args if args else None
            filepath = self.conversation.save_conversation(filename)
            console.print(f"[green]✓ Conversation saved to: {filepath}[/green]")
            
        elif cmd == "/personality":
            if args:
                await self._change_personality(args)
            else:
                self._list_personalities()
                
        elif cmd == "/stats":
            self._show_statistics()
            
        elif cmd == "/help":
            self._show_help()
            
        else:
            console.print(f"[red]Unknown command: {cmd}[/red]")
            console.print(f"[{self.system_style}]Type '/help' for available commands[/{self.system_style}]")
    
    async def _change_personality(self, personality_name: str):
        """Change chatbot personality."""
        personality = load_personality(personality_name)
        
        if personality:
            self.chatbot_config.personality = personality_name
            self.chatbot_config.system_prompt = personality.system_prompt
            self.chatbot_config.temperature = personality.temperature
            self.chatbot.update_config(
                personality=personality_name,
                system_prompt=personality.system_prompt,
                temperature=personality.temperature
            )
            
            self.conversation.update_metadata(personality=personality_name)
            
            console.print(f"[green]✓ Switched to personality: {personality.name}[/green]")
            console.print(f"[{self.system_style}]{personality.description}[/{self.system_style}]")
        else:
            console.print(f"[red]Personality '{personality_name}' not found[/red]")
    
    def _list_personalities(self):
        """List available personalities."""
        from .config_loader import load_personalities
        
        personalities = load_personalities()
        
        table = Table(title="Available Personalities")
        table.add_column("Name", style="cyan")
        table.add_column("Description", style="white")
        table.add_column("Temperature", style="yellow")
        
        for name, personality in personalities.items():
            is_current = "✓ " if name == self.chatbot_config.personality else ""
            table.add_row(
                f"{is_current}{name}",
                personality.description,
                f"{personality.temperature}"
            )
        
        console.print(table)
    
    def _show_statistics(self):
        """Show conversation statistics."""
        stats = self.conversation.get_statistics()
        
        table = Table(title="Conversation Statistics")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="yellow")
        
        table.add_row("Total Messages", str(stats["message_count"]))
        table.add_row("User Messages", str(stats["user_messages"]))
        table.add_row("Assistant Messages", str(stats["assistant_messages"]))
        table.add_row("Avg Message Length", f"{stats['avg_message_length']:.1f} chars")
        table.add_row("Duration", f"{stats['duration_seconds']:.1f} seconds")
        
        console.print(table)
    
    def _show_help(self):
        """Show help information."""
        help_text = """
[bold]Available Commands:[/bold]

  /help              - Show this help message
  /exit, /quit       - End the conversation
  /clear             - Clear conversation history
  /save [filename]   - Save conversation to file
  /personality [name] - Change personality (or list if no name)
  /stats             - Show conversation statistics

[bold]Tips:[/bold]
  • Type naturally - the chatbot maintains context
  • Use different personalities for different tasks
  • Save important conversations for later reference
        """
        
        console.print(Panel(help_text, title="Help", border_style="blue"))