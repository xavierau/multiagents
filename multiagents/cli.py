#!/usr/bin/env python3
"""
MultiAgents CLI - Command Line Interface for project initialization and management
"""

import os
import sys
import shutil
import argparse
from pathlib import Path
from typing import Optional

def get_package_resource_path(resource_path: str) -> Optional[Path]:
    """Get the absolute path to a package resource.""" 
    try:
        # Simple approach: look for resources relative to this file
        package_dir = Path(__file__).parent
        resource = package_dir / resource_path
        return resource if resource.exists() else None
    except Exception:
        return None


def create_project(name: str, template: str = "basic") -> bool:
    """Create a new MultiAgents project from template."""
    project_path = Path(name)
    
    if project_path.exists():
        print(f"Error: Directory '{name}' already exists")
        return False
    
    # Get template path
    template_path = get_package_resource_path(f"templates/{template}")
    if not template_path or not template_path.exists():
        available_templates = ["basic", "ecommerce", "dspy"]
        print(f"Error: Template '{template}' not found")
        print(f"Available templates: {', '.join(available_templates)}")
        return False
    
    try:
        # Copy template to new project
        shutil.copytree(template_path, project_path)
        
        # Replace placeholders in template files
        replace_placeholders(project_path, {"PROJECT_NAME": name})
        
        print(f"✅ Created MultiAgents project '{name}' using template '{template}'")
        print(f"📁 Project created at: {project_path.absolute()}")
        print("\n🚀 Next steps:")
        print(f"   cd {name}")
        print("   pip install -r requirements.txt")
        print("   python main.py")
        
        return True
        
    except Exception as e:
        print(f"Error creating project: {e}")
        return False


def replace_placeholders(project_path: Path, replacements: dict):
    """Replace placeholders in template files."""
    for file_path in project_path.rglob("*.py"):
        try:
            content = file_path.read_text()
            for placeholder, value in replacements.items():
                content = content.replace(f"{{{placeholder}}}", value)
            file_path.write_text(content)
        except Exception:
            pass  # Skip binary or unreadable files


def install_agent() -> bool:
    """Install Claude Code subagent in the current directory."""
    current_dir = Path.cwd()
    claude_dir = current_dir / ".claude"
    agents_dir = claude_dir / "agents"
    
    # Create .claude/agents directory
    agents_dir.mkdir(parents=True, exist_ok=True)
    
    # Get agent file from package
    agent_path = get_package_resource_path("agents/multiagents.md")
    if not agent_path or not agent_path.exists():
        print("Error: MultiAgents Claude Code agent not found in package")
        return False
    
    # Copy agent to project
    dest_path = agents_dir / "multiagents.md"
    try:
        shutil.copy2(agent_path, dest_path)
        print(f"✅ Installed MultiAgents Claude Code agent")
        print(f"📁 Agent installed at: {dest_path}")
        print("\n🤖 Usage:")
        print("   Start Claude Code in this directory")
        print("   Type '@multiagents' to activate the agent")
        return True
    except Exception as e:
        print(f"Error installing agent: {e}")
        return False


def list_templates() -> None:
    """List available project templates."""
    templates_path = get_package_resource_path("templates")
    if not templates_path or not templates_path.exists():
        print("No templates available")
        return
    
    print("Available templates:")
    for template_dir in templates_path.iterdir():
        if template_dir.is_dir():
            print(f"  📁 {template_dir.name}")
            
            # Try to read template description
            readme_path = template_dir / "README.md"
            if readme_path.exists():
                try:
                    content = readme_path.read_text()
                    # Extract first line as description
                    lines = content.strip().split('\n')
                    if lines and lines[0].startswith('#'):
                        description = lines[0].replace('#', '').strip()
                        print(f"     {description}")
                except Exception:
                    pass


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="MultiAgents Framework CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  multiagents init my-project                 # Create basic project
  multiagents init my-shop --template ecommerce  # Create e-commerce project
  multiagents install-agent                   # Install Claude Code agent
  multiagents list-templates                  # Show available templates
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Init command
    init_parser = subparsers.add_parser('init', help='Initialize a new MultiAgents project')
    init_parser.add_argument('name', help='Project name')
    init_parser.add_argument('--template', '-t', default='basic', 
                           help='Template to use (default: basic)')
    
    # Install agent command
    subparsers.add_parser('install-agent', help='Install Claude Code subagent')
    
    # List templates command
    subparsers.add_parser('list-templates', help='List available project templates')
    
    # Version command
    subparsers.add_parser('version', help='Show version information')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    if args.command == 'init':
        success = create_project(args.name, args.template)
        sys.exit(0 if success else 1)
    
    elif args.command == 'install-agent':
        success = install_agent()
        sys.exit(0 if success else 1)
    
    elif args.command == 'list-templates':
        list_templates()
    
    elif args.command == 'version':
        from multiagents import __version__
        print(f"MultiAgents Framework v{__version__}")
    
    else:
        parser.print_help()


if __name__ == '__main__':
    main()