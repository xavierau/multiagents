#!/usr/bin/env python3
"""
MultiAgents Chatbot Example - Main Entry Point

A command-line chatbot powered by DSPy and Google Gemini,
demonstrating the MultiAgents framework's LLM capabilities.
"""

import asyncio
import sys
from pathlib import Path
import click
from rich.console import Console
import structlog

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from src.cli_interface import ChatbotCLI
from src.config_loader import load_config, validate_environment
from multiagents.monitoring import MonitoringConfig


# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.dev.ConsoleRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()
console = Console()


@click.command()
@click.option(
    "--config",
    "-c",
    default="config/chatbot_config.yaml",
    help="Path to configuration file",
    type=click.Path(exists=True)
)
@click.option(
    "--personality",
    "-p",
    default=None,
    help="Initial personality to use"
)
@click.option(
    "--no-welcome",
    is_flag=True,
    help="Skip welcome message"
)
@click.option(
    "--debug",
    is_flag=True,
    help="Enable debug logging"
)
def main(config: str, personality: str, no_welcome: bool, debug: bool):
    """
    MultiAgents Chatbot - Interactive CLI powered by DSPy and Gemini.
    
    This example demonstrates how to build an LLM-powered chatbot
    using the MultiAgents framework with DSPy integration.
    """
    # Set logging level
    if debug:
        structlog.configure(
            wrapper_class=structlog.stdlib.BoundLogger,
            logger_factory=structlog.stdlib.LoggerFactory(),
            cache_logger_on_first_use=True,
        )
        logger.setLevel("DEBUG")
    
    try:
        # Validate environment
        console.print("[bold blue]🔍 Validating environment...[/bold blue]")
        env_validation = validate_environment()
        
        if not env_validation.get("GOOGLE_API_KEY"):
            console.print("[red]❌ Error: GOOGLE_API_KEY environment variable not set[/red]")
            console.print("\nPlease set your Google Gemini API key:")
            console.print("  export GOOGLE_API_KEY='your-api-key'")
            console.print("\nGet your API key from: https://makersuite.google.com/app/apikey")
            sys.exit(1)
        
        # Load configuration
        console.print("[bold blue]📁 Loading configuration...[/bold blue]")
        chatbot_config = load_config(config)
        
        # Override personality if specified
        if personality:
            chatbot_config.setdefault("chatbot", {})["default_personality"] = personality
        
        # Override welcome message if specified
        if no_welcome:
            chatbot_config.setdefault("chatbot", {}).setdefault("cli", {})["welcome_message"] = False
        
        # Initialize monitoring
        monitoring_config_path = Path(config).parent / "monitoring.yaml"
        if monitoring_config_path.exists():
            console.print("[bold blue]📊 Initializing monitoring...[/bold blue]")
            monitoring_config = MonitoringConfig.from_file(str(monitoring_config_path))
            logger.info("Monitoring initialized", config_path=str(monitoring_config_path))
        
        # Create and run chatbot
        console.print("[bold green]✅ Starting chatbot...[/bold green]\n")
        
        personality_name = chatbot_config.get("chatbot", {}).get("default_personality", "default")
        chatbot_cli = ChatbotCLI(chatbot_config, personality_name)
        
        # Run the async chat loop
        asyncio.run(chatbot_cli.run())
        
    except KeyboardInterrupt:
        console.print("\n[yellow]Interrupted by user[/yellow]")
        sys.exit(0)
        
    except Exception as e:
        console.print(f"\n[red]Fatal error: {str(e)}[/red]")
        logger.exception("Fatal error in main")
        sys.exit(1)


if __name__ == "__main__":
    main()