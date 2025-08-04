"""
E-commerce Workflow Diagram Generation Demo

This demo shows how to visualize the e-commerce order processing workflow
using the DiagramGenerator in both ASCII and Mermaid formats.
"""
import sys
from pathlib import Path

# Fix Python path conflicts when running from within the multiagents directory
if '' in sys.path:
    sys.path.remove('')
if '.' in sys.path:
    sys.path.remove('.')

# Add the project root to Python path
project_root = Path(__file__).parent.parent.parent
parent_dir = project_root.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

from multiagents.orchestrator import DiagramGenerator
from multiagents.examples.ecommerce_order.workflow import create_ecommerce_workflow, create_advanced_ecommerce_workflow


def demo_workflow_diagrams():
    """Demo workflow diagram generation."""
    print("🎨 E-commerce Workflow Diagram Demo")
    print("=" * 50)
    
    # Create the e-commerce workflow
    workflow = create_ecommerce_workflow()
    generator = DiagramGenerator(workflow)
    
    print("\n📋 WORKFLOW OVERVIEW")
    print("-" * 20)
    print(f"Workflow ID: {workflow.get_id()}")
    print(f"Total Steps: {len(workflow.get_steps())}")
    print("Steps:")
    for i, step in enumerate(workflow.get_steps(), 1):
        comp_info = f" (compensation: {step.compensation})" if step.compensation else ""
        print(f"  {i}. {step.name} -> {step.worker_type}{comp_info}")
    
    print("\n" + "=" * 80)
    print("1. ASCII WORKFLOW DIAGRAM (Default)")
    print("=" * 80)
    
    # Generate ASCII workflow diagram
    ascii_diagram = generator.generate_workflow_diagram()
    print(ascii_diagram)
    
    print("\n" + "=" * 80)
    print("2. MERMAID WORKFLOW DIAGRAM")
    print("=" * 80)
    
    # Generate Mermaid workflow diagram
    mermaid_diagram = generator.generate_workflow_diagram(type="mermaid")
    print(mermaid_diagram)
    
    return generator


def demo_event_flow_diagrams(generator):
    """Demo event flow diagram generation."""
    print("\n" + "=" * 80)
    print("3. ASCII EVENT FLOW DIAGRAM (Default)")
    print("=" * 80)
    
    # Generate ASCII event flow diagram
    event_ascii = generator.generate_event_flow_diagram()
    print(event_ascii)
    
    print("\n" + "=" * 80)
    print("4. MERMAID EVENT FLOW SEQUENCE DIAGRAM")
    print("=" * 80)
    
    # Generate Mermaid event flow diagram
    event_mermaid = generator.generate_event_flow_diagram(type="mermaid")
    print(event_mermaid)


def demo_advanced_workflow():
    """Demo advanced workflow with conditional branching."""
    print("\n" + "=" * 80)
    print("5. ADVANCED WORKFLOW WITH CONDITIONAL BRANCHING")
    print("=" * 80)
    
    # Create advanced workflow
    advanced_workflow = create_advanced_ecommerce_workflow()
    advanced_generator = DiagramGenerator(advanced_workflow)
    
    print("\n📋 ADVANCED WORKFLOW OVERVIEW")
    print("-" * 30)
    print(f"Workflow ID: {advanced_workflow.get_id()}")
    print(f"Total Steps: {len(advanced_workflow.get_steps())}")
    
    # Show steps with branching info
    for step in advanced_workflow.get_steps():
        branch_info = ""
        if step.next_steps:
            branches = ", ".join([f"{cond} -> {next_step}" for cond, next_step in step.next_steps.items()])
            branch_info = f" [branches: {branches}]"
        
        comp_info = f" [comp: {step.compensation}]" if step.compensation else ""
        print(f"  • {step.name} -> {step.worker_type}{comp_info}{branch_info}")
    
    print("\n🔀 ASCII BRANCHING WORKFLOW:")
    print("-" * 30)
    advanced_ascii = advanced_generator.generate_workflow_diagram()
    print(advanced_ascii)
    
    print("\n🔀 MERMAID BRANCHING WORKFLOW:")
    print("-" * 30)
    advanced_mermaid = advanced_generator.generate_workflow_diagram(type="mermaid")
    print(advanced_mermaid)


def demo_architecture_diagrams(generator):
    """Demo combined architecture diagrams."""
    print("\n" + "=" * 80)
    print("6. COMBINED ARCHITECTURE DIAGRAMS")
    print("=" * 80)
    
    print("\n🏗️  ASCII ARCHITECTURE OVERVIEW:")
    print("-" * 30)
    arch_ascii = generator.generate_architecture_diagram()
    print(arch_ascii)
    
    print("\n🏗️  MERMAID ARCHITECTURE OVERVIEW:")
    print("-" * 30)
    arch_mermaid = generator.generate_architecture_diagram(type="mermaid")
    print(arch_mermaid)


def demo_save_diagrams(generator):
    """Demo saving diagrams to files."""
    print("\n" + "=" * 80)
    print("7. SAVING DIAGRAMS TO FILES")
    print("=" * 80)
    
    # Create output directory
    output_dir = Path(__file__).parent / "generated_diagrams"
    output_dir.mkdir(exist_ok=True)
    
    files_created = []
    
    try:
        # Save workflow diagrams
        workflow_ascii_file = output_dir / "ecommerce_workflow_ascii.txt"
        workflow_mermaid_file = output_dir / "ecommerce_workflow.mmd"
        
        generator.save_to_file(str(workflow_ascii_file), "workflow", "ascii")
        generator.save_to_file(str(workflow_mermaid_file), "workflow", "mermaid")
        files_created.extend([workflow_ascii_file, workflow_mermaid_file])
        
        # Save event flow diagrams
        events_ascii_file = output_dir / "ecommerce_events_ascii.txt"
        events_mermaid_file = output_dir / "ecommerce_events.mmd"
        
        generator.save_to_file(str(events_ascii_file), "event_flow", "ascii")
        generator.save_to_file(str(events_mermaid_file), "event_flow", "mermaid")
        files_created.extend([events_ascii_file, events_mermaid_file])
        
        # Save architecture diagrams
        arch_ascii_file = output_dir / "ecommerce_architecture_ascii.txt"
        arch_mermaid_file = output_dir / "ecommerce_architecture.mmd"
        
        generator.save_to_file(str(arch_ascii_file), "architecture", "ascii")
        generator.save_to_file(str(arch_mermaid_file), "architecture", "mermaid")
        files_created.extend([arch_ascii_file, arch_mermaid_file])
        
        print("✅ Successfully saved diagrams:")
        for file_path in files_created:
            print(f"   📄 {file_path.name}")
        
        print(f"\n📁 All files saved to: {output_dir}")
        
        # Show file contents preview
        print(f"\n📖 Preview of {workflow_ascii_file.name}:")
        print("-" * 40)
        with open(workflow_ascii_file, 'r') as f:
            lines = f.readlines()[:10]  # First 10 lines
            for line in lines:
                print(f"   {line.rstrip()}")
            if len(lines) >= 10:
                print("   ...")
        
    except Exception as e:
        print(f"❌ Error saving diagrams: {e}")


def demo_practical_examples():
    """Show practical examples of using the diagram generator."""
    print("\n" + "=" * 80)
    print("8. PRACTICAL USAGE EXAMPLES")
    print("=" * 80)
    
    print("""
💡 Practical Usage Examples:

1. DOCUMENTATION GENERATION:
   # Generate documentation diagrams for your workflows
   workflow = create_my_workflow()
   generator = DiagramGenerator(workflow)
   generator.save_to_file("docs/workflow.mmd", "workflow", "mermaid")

2. DEBUGGING & VISUALIZATION:
   # ASCII diagrams for quick console output
   print(generator.generate_workflow_diagram())  # ASCII by default
   
3. TEAM COLLABORATION:
   # Mermaid diagrams for GitHub/GitLab markdown
   mermaid = generator.generate_workflow_diagram(type="mermaid")
   # Paste into README.md or wiki

4. EVENT FLOW ANALYSIS:
   # Understand event communication patterns
   print(generator.generate_event_flow_diagram())
   
5. ARCHITECTURE REVIEWS:
   # Combined view for system design discussions
   print(generator.generate_architecture_diagram(type="mermaid"))

6. INTEGRATION WITH MONITORING:
   # Include worker manager for runtime event analysis
   generator = DiagramGenerator(workflow, worker_manager)
   print(generator.generate_event_flow_diagram())
""")


def main():
    """Run the complete diagram generation demo."""
    print("🚀 Starting E-commerce Workflow Diagram Demo\n")
    
    try:
        # Main workflow diagrams
        generator = demo_workflow_diagrams()
        
        # Event flow diagrams
        demo_event_flow_diagrams(generator)
        
        # Advanced workflow with branching
        demo_advanced_workflow()
        
        # Architecture diagrams
        demo_architecture_diagrams(generator)
        
        # Save diagrams to files
        demo_save_diagrams(generator)
        
        # Practical examples
        demo_practical_examples()
        
        print("\n" + "=" * 80)
        print("🎉 DEMO COMPLETE!")
        print("=" * 80)
        print("""
Summary of what we demonstrated:

✅ ASCII workflow diagrams (default output)
✅ Mermaid workflow diagrams (explicit type="mermaid")
✅ Event flow visualization (both ASCII and Mermaid)
✅ Advanced workflows with conditional branching
✅ Combined architecture diagrams
✅ Saving diagrams to files
✅ Practical usage examples

Next steps:
1. Try modifying the e-commerce workflow in workflow.py
2. Run this demo again to see how diagrams change
3. Integrate diagram generation into your own workflows
4. Use Mermaid diagrams in documentation and README files
""")
        
    except Exception as e:
        print(f"\n❌ Demo failed with error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()