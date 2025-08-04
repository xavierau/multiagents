"""
Diagram Generator Example

Demonstrates how to use the DiagramGenerator to create workflow and event flow visualizations.
"""
import asyncio
from multiagents.orchestrator import DiagramGenerator
from multiagents.examples.ecommerce_order.workflow import create_ecommerce_workflow, create_advanced_ecommerce_workflow


def main():
    """Demonstrate diagram generation capabilities."""
    print("🎨 Workflow Diagram Generator Example\n")
    
    # Create workflows
    simple_workflow = create_ecommerce_workflow()
    advanced_workflow = create_advanced_ecommerce_workflow()
    
    print("=" * 80)
    print("1. SIMPLE E-COMMERCE WORKFLOW - ASCII DIAGRAM (Default)")
    print("=" * 80)
    
    # Generate ASCII workflow diagram (default)
    generator = DiagramGenerator(simple_workflow)
    ascii_diagram = generator.generate_workflow_diagram()
    print(ascii_diagram)
    
    print("\n" + "=" * 80)
    print("2. SIMPLE E-COMMERCE WORKFLOW - MERMAID DIAGRAM")
    print("=" * 80)
    
    # Generate Mermaid workflow diagram (explicit)
    mermaid_diagram = generator.generate_workflow_diagram(type="mermaid")
    print(mermaid_diagram)
    
    print("\n" + "=" * 80)
    print("3. ADVANCED WORKFLOW WITH BRANCHING - ASCII DIAGRAM")
    print("=" * 80)
    
    # Generate advanced workflow with conditional branching
    advanced_generator = DiagramGenerator(advanced_workflow)
    advanced_ascii = advanced_generator.generate_workflow_diagram()
    print(advanced_ascii)
    
    print("\n" + "=" * 80)
    print("4. ADVANCED WORKFLOW WITH BRANCHING - MERMAID DIAGRAM")
    print("=" * 80)
    
    advanced_mermaid = advanced_generator.generate_workflow_diagram(type="mermaid")
    print(advanced_mermaid)
    
    print("\n" + "=" * 80)
    print("5. EVENT FLOW DIAGRAM - ASCII (Default)")
    print("=" * 80)
    
    # Generate event flow diagram
    event_flow_ascii = generator.generate_event_flow_diagram()
    print(event_flow_ascii)
    
    print("\n" + "=" * 80)
    print("6. EVENT FLOW DIAGRAM - MERMAID SEQUENCE")
    print("=" * 80)
    
    event_flow_mermaid = generator.generate_event_flow_diagram(type="mermaid")
    print(event_flow_mermaid)
    
    print("\n" + "=" * 80)
    print("7. COMBINED ARCHITECTURE DIAGRAM - ASCII")
    print("=" * 80)
    
    architecture_ascii = generator.generate_architecture_diagram()
    print(architecture_ascii)
    
    print("\n" + "=" * 80)
    print("8. COMBINED ARCHITECTURE DIAGRAM - MERMAID")
    print("=" * 80)
    
    architecture_mermaid = generator.generate_architecture_diagram(type="mermaid")
    print(architecture_mermaid)
    
    print("\n" + "=" * 80)
    print("9. SAVING DIAGRAMS TO FILES")
    print("=" * 80)
    
    # Save diagrams to files
    try:
        # Save workflow diagrams
        generator.save_to_file("workflow_ascii.txt", "workflow", "ascii")
        generator.save_to_file("workflow.mmd", "workflow", "mermaid")
        
        # Save event flow diagrams
        generator.save_to_file("events_ascii.txt", "event_flow", "ascii")
        generator.save_to_file("events.mmd", "event_flow", "mermaid")
        
        # Save architecture diagrams
        generator.save_to_file("architecture_ascii.txt", "architecture", "ascii")
        generator.save_to_file("architecture.mmd", "architecture", "mermaid")
        
        print("✅ Diagrams saved to files:")
        print("   • workflow_ascii.txt")
        print("   • workflow.mmd")
        print("   • events_ascii.txt")
        print("   • events.mmd")
        print("   • architecture_ascii.txt")
        print("   • architecture.mmd")
        
    except Exception as e:
        print(f"❌ Error saving files: {e}")
    
    print("\n" + "=" * 80)
    print("10. USAGE EXAMPLES")
    print("=" * 80)
    
    print("""
Usage Examples:

# Basic usage with ASCII output (default)
from multiagents.orchestrator import DiagramGenerator

workflow = create_ecommerce_workflow()
generator = DiagramGenerator(workflow)

# ASCII diagrams (default)
print(generator.generate_workflow_diagram())
print(generator.generate_event_flow_diagram())

# Mermaid diagrams (explicit)
print(generator.generate_workflow_diagram(type="mermaid"))
print(generator.generate_event_flow_diagram(type="mermaid"))

# Save to files
generator.save_to_file("my_workflow.mmd", "workflow", "mermaid")
generator.save_to_file("my_events.txt", "event_flow", "ascii")

# For event flow analysis with worker manager:
generator = DiagramGenerator(workflow, worker_manager)
print(generator.generate_event_flow_diagram())
""")
    
    print("\n" + "=" * 80)
    print("🎉 Diagram Generation Complete!")
    print("=" * 80)


if __name__ == "__main__":
    main()