"""
Workflow and Event Flow Diagram Generator

Generates visual representations of workflows and event flows in ASCII and Mermaid formats.
"""
from typing import Dict, List, Optional, Set, Tuple
from .interface import IWorkflowDefinition
from .workflow import WorkflowDefinition, WorkflowStep


class DiagramGenerator:
    """
    Generates workflow and event flow diagrams in ASCII and Mermaid formats.
    
    ASCII is the default output format, with Mermaid available when explicitly requested.
    """
    
    def __init__(self, workflow: IWorkflowDefinition, worker_manager: Optional['WorkerManager'] = None):
        """
        Initialize diagram generator.
        
        Args:
            workflow: The workflow definition to visualize
            worker_manager: Optional worker manager for event flow analysis
        """
        self.workflow = workflow
        self.worker_manager = worker_manager
        
    def generate_workflow_diagram(self, type: str = "ascii") -> str:
        """
        Generate workflow diagram.
        
        Args:
            type: Output format - "ascii" (default) or "mermaid"
            
        Returns:
            Diagram as string
        """
        if type.lower() == "mermaid":
            return self._generate_workflow_mermaid()
        else:
            return self._generate_workflow_ascii()
    
    def generate_event_flow_diagram(self, type: str = "ascii") -> str:
        """
        Generate event flow diagram.
        
        Args:
            type: Output format - "ascii" (default) or "mermaid"
            
        Returns:
            Event flow diagram as string
        """
        if type.lower() == "mermaid":
            return self._generate_event_flow_mermaid()
        else:
            return self._generate_event_flow_ascii()
    
    def generate_architecture_diagram(self, type: str = "ascii") -> str:
        """
        Generate combined architecture diagram showing both workflow and events.
        
        Args:
            type: Output format - "ascii" (default) or "mermaid"
            
        Returns:
            Architecture diagram as string
        """
        if type.lower() == "mermaid":
            return self._generate_architecture_mermaid()
        else:
            return self._generate_architecture_ascii()
    
    def save_to_file(self, filename: str, diagram_type: str = "workflow", format_type: str = "ascii") -> None:
        """
        Save diagram to file.
        
        Args:
            filename: Output filename
            diagram_type: "workflow", "event_flow", or "architecture" 
            format_type: "ascii" or "mermaid"
        """
        if diagram_type == "workflow":
            content = self.generate_workflow_diagram(format_type)
        elif diagram_type == "event_flow":
            content = self.generate_event_flow_diagram(format_type)
        elif diagram_type == "architecture":
            content = self.generate_architecture_diagram(format_type)
        else:
            raise ValueError(f"Unknown diagram type: {diagram_type}")
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(content)
    
    # Workflow Diagram Generation
    
    def _generate_workflow_ascii(self) -> str:
        """Generate ASCII workflow diagram."""
        lines = []
        steps = self.workflow.get_steps()
        
        # Header
        lines.append(f"Workflow: {self.workflow.get_id()}")
        lines.append("=" * (len(self.workflow.get_id()) + 10))
        lines.append("")
        
        if not steps:
            lines.append("(No steps defined)")
            return "\n".join(lines)
        
        # Analyze workflow structure
        step_map = {step.name: step for step in steps}
        has_branches = any(step.next_steps for step in steps)
        
        if has_branches:
            return self._generate_branching_workflow_ascii(step_map, lines)
        else:
            return self._generate_linear_workflow_ascii(steps, lines)
    
    def _generate_linear_workflow_ascii(self, steps: List[WorkflowStep], lines: List[str]) -> str:
        """Generate ASCII for linear workflow."""
        for i, step in enumerate(steps):
            # Step box
            step_text = f"{step.name} ({step.worker_type})"
            compensation_text = f" [comp: {step.compensation}]" if step.compensation else ""
            timeout_text = f" [{step.timeout_seconds}s]"
            
            full_text = step_text + compensation_text + timeout_text
            box_width = max(len(full_text) + 4, 30)
            
            # Box drawing
            lines.append("┌" + "─" * (box_width - 2) + "┐")
            lines.append(f"│ {full_text:<{box_width - 4}} │")
            lines.append("└" + "─" * (box_width - 2) + "┘")
            
            # Arrow to next step
            if i < len(steps) - 1:
                lines.append("     │")
                lines.append("     ▼")
                lines.append("")
        
        return "\n".join(lines)
    
    def _generate_branching_workflow_ascii(self, step_map: Dict[str, WorkflowStep], lines: List[str]) -> str:
        """Generate ASCII for workflow with branching."""
        # Find initial step
        initial_step = self.workflow.get_initial_step()
        if not initial_step:
            lines.append("(No initial step found)")
            return "\n".join(lines)
        
        visited = set()
        self._draw_step_tree_ascii(initial_step, step_map, lines, visited, 0, "")
        
        return "\n".join(lines)
    
    def _draw_step_tree_ascii(self, step: WorkflowStep, step_map: Dict[str, WorkflowStep], 
                             lines: List[str], visited: Set[str], depth: int, prefix: str) -> None:
        """Recursively draw step tree in ASCII."""
        if step.name in visited:
            return
        visited.add(step.name)
        
        # Step representation
        step_text = f"{step.name} ({step.worker_type})"
        if step.compensation:
            step_text += f" [comp: {step.compensation}]"
        
        lines.append(f"{prefix}{step_text}")
        
        # Handle branching
        if step.next_steps:
            branches = list(step.next_steps.items())
            for i, (condition, next_step_name) in enumerate(branches):
                is_last = i == len(branches) - 1
                branch_prefix = "└── " if is_last else "├── "
                child_prefix = "    " if is_last else "│   "
                
                lines.append(f"{prefix}{branch_prefix}[{condition}]")
                
                next_step = step_map.get(next_step_name)
                if next_step:
                    self._draw_step_tree_ascii(
                        next_step, step_map, lines, visited, 
                        depth + 1, prefix + child_prefix
                    )
        else:
            # Linear continuation - find next step in order
            steps = self.workflow.get_steps()
            step_order = [s.name for s in steps]
            try:
                current_index = step_order.index(step.name)
                if current_index + 1 < len(step_order):
                    next_step_name = step_order[current_index + 1]
                    next_step = step_map.get(next_step_name)
                    if next_step and next_step.name not in visited:
                        lines.append(f"{prefix}│")
                        self._draw_step_tree_ascii(
                            next_step, step_map, lines, visited, 
                            depth + 1, prefix
                        )
            except ValueError:
                pass
    
    def _generate_workflow_mermaid(self) -> str:
        """Generate Mermaid workflow diagram."""
        lines = []
        steps = self.workflow.get_steps()
        
        # Mermaid header
        lines.append("```mermaid")
        lines.append("flowchart TD")
        lines.append("")
        
        if not steps:
            lines.append("    Start([Start]) --> End([No steps defined])")
            lines.append("```")
            return "\n".join(lines)
        
        # Generate step nodes
        step_map = {step.name: step for step in steps}
        
        # Add start node
        lines.append("    Start([Start])")
        
        # Add step nodes
        for step in steps:
            node_id = step.name.replace(" ", "_").replace("-", "_")
            label = f"{step.name}\\n({step.worker_type})"
            if step.compensation:
                label += f"\\n[comp: {step.compensation}]"
            
            # Choose node shape based on step characteristics
            if step.next_steps:
                # Decision node (diamond)
                lines.append(f"    {node_id}{{{label}}}")
            else:
                # Process node (rectangle)
                lines.append(f"    {node_id}[{label}]")
        
        lines.append("")
        
        # Add connections
        initial_step = self.workflow.get_initial_step()
        if initial_step:
            initial_id = initial_step.name.replace(" ", "_").replace("-", "_")
            lines.append(f"    Start --> {initial_id}")
        
        # Add step connections
        for step in steps:
            node_id = step.name.replace(" ", "_").replace("-", "_")
            
            if step.next_steps:
                # Conditional branches
                for condition, next_step_name in step.next_steps.items():
                    next_id = next_step_name.replace(" ", "_").replace("-", "_")
                    lines.append(f"    {node_id} -->|{condition}| {next_id}")
            else:
                # Linear flow
                step_order = [s.name for s in steps]
                try:
                    current_index = step_order.index(step.name)
                    if current_index + 1 < len(step_order):
                        next_step = steps[current_index + 1]
                        next_id = next_step.name.replace(" ", "_").replace("-", "_")
                        lines.append(f"    {node_id} --> {next_id}")
                    else:
                        # Last step
                        lines.append(f"    {node_id} --> End([End])")
                except ValueError:
                    pass
        
        # Add compensation flows (dotted lines)
        lines.append("")
        lines.append("    %% Compensation flows")
        for step in steps:
            if step.compensation:
                step_id = step.name.replace(" ", "_").replace("-", "_")
                comp_id = step.compensation.replace(" ", "_").replace("-", "_")
                lines.append(f"    {step_id} -.->|compensation| {comp_id}")
        
        lines.append("```")
        return "\n".join(lines)
    
    # Event Flow Diagram Generation
    
    def _generate_event_flow_ascii(self) -> str:
        """Generate ASCII event flow diagram."""
        lines = []
        
        # Header
        lines.append(f"Event Flow: {self.workflow.get_id()}")
        lines.append("=" * (len(self.workflow.get_id()) + 12))
        lines.append("")
        
        # Component diagram
        lines.append("Components & Event Flow:")
        lines.append("")
        lines.append("┌─────────────┐    ┌──────────┐    ┌──────────────┐    ┌─────────┐")
        lines.append("│ Orchestrator│───▶│ EventBus │◀──▶│ WorkerManager│───▶│ Workers │")
        lines.append("└─────────────┘    └──────────┘    └──────────────┘    └─────────┘")
        lines.append("        │               │                    │              │")
        lines.append("        ▼               ▼                    ▼              ▼")
        lines.append("  [publishes]      [routes]           [subscribes]    [processes]")
        lines.append("")
        
        # Event types
        events = self._analyze_workflow_events()
        
        lines.append("Event Types:")
        lines.append("─" * 12)
        for event_type, description in events.items():
            lines.append(f"• {event_type:<25} - {description}")
        
        lines.append("")
        
        # Event flows for each step
        lines.append("Step Event Flows:")
        lines.append("─" * 17)
        
        for step in self.workflow.get_steps():
            lines.append(f"\n{step.name} ({step.worker_type}):")
            lines.append(f"  Orchestrator ──[command.{step.worker_type}]──▶ WorkerManager")
            lines.append(f"  Orchestrator ◀─[result.{step.worker_type}]──── WorkerManager")
            
            if step.compensation:
                lines.append(f"  Orchestrator ──[compensation.{step.compensation}]──▶ WorkerManager")
        
        return "\n".join(lines)
    
    def _generate_event_flow_mermaid(self) -> str:
        """Generate Mermaid event flow diagram."""
        lines = []
        
        lines.append("```mermaid")
        lines.append("sequenceDiagram")
        lines.append("    participant O as Orchestrator")
        lines.append("    participant EB as EventBus")
        lines.append("    participant WM as WorkerManager")
        lines.append("    participant W as Workers")
        lines.append("    participant M as Monitoring")
        lines.append("")
        
        # Startup sequence
        lines.append("    Note over O,M: System Startup")
        lines.append("    O->>EB: subscribe to result events")
        lines.append("    WM->>EB: subscribe to command events")
        lines.append("")
        
        # Workflow execution
        lines.append("    Note over O,M: Workflow Execution")
        
        for i, step in enumerate(self.workflow.get_steps()):
            step_num = i + 1
            lines.append(f"    Note over O,W: Step {step_num}: {step.name}")
            lines.append(f"    O->>EB: command.{step.worker_type}")
            lines.append(f"    EB->>M: track event dispatch")
            lines.append(f"    EB->>WM: route command")
            lines.append(f"    WM->>M: track event pickup")
            lines.append(f"    WM->>W: process({step.worker_type})")
            lines.append(f"    W->>WM: result")
            lines.append(f"    WM->>EB: result.{step.worker_type}")
            lines.append(f"    EB->>M: track event completion")
            lines.append(f"    EB->>O: route result")
            
            if step.compensation:
                lines.append(f"    Note over O,W: Compensation Available: {step.compensation}")
            
            if i < len(self.workflow.get_steps()) - 1:
                lines.append("")
        
        lines.append("")
        lines.append("    Note over O,M: Workflow Status")
        lines.append("    O->>EB: status.workflow")
        lines.append("    EB->>M: track status event")
        
        lines.append("```")
        return "\n".join(lines)
    
    # Architecture Diagram Generation
    
    def _generate_architecture_ascii(self) -> str:
        """Generate combined ASCII architecture diagram."""
        workflow_diagram = self._generate_workflow_ascii()
        event_diagram = self._generate_event_flow_ascii()
        
        return f"{workflow_diagram}\n\n{event_diagram}"
    
    def _generate_architecture_mermaid(self) -> str:
        """Generate combined Mermaid architecture diagram."""
        lines = []
        
        lines.append("```mermaid")
        lines.append("graph TB")
        lines.append("    subgraph \"Workflow Definition\"")
        
        # Add workflow steps
        for step in self.workflow.get_steps():
            step_id = step.name.replace(" ", "_")
            lines.append(f"        {step_id}[{step.name}\\n({step.worker_type})]")
        
        lines.append("    end")
        lines.append("")
        lines.append("    subgraph \"Event System\"")
        lines.append("        O[Orchestrator]")
        lines.append("        EB[EventBus]")
        lines.append("        WM[WorkerManager]")
        lines.append("        W[Workers]")
        lines.append("        M[Monitoring]")
        lines.append("")
        lines.append("        O -->|command events| EB")
        lines.append("        EB -->|route| WM")
        lines.append("        WM -->|execute| W")
        lines.append("        W -->|result| WM")
        lines.append("        WM -->|result events| EB")
        lines.append("        EB -->|notify| O")
        lines.append("        EB -->|track| M")
        lines.append("    end")
        lines.append("```")
        
        return "\n".join(lines)
    
    # Helper Methods
    
    def _analyze_workflow_events(self) -> Dict[str, str]:
        """Analyze workflow to determine event types."""
        events = {
            "status.workflow": "Workflow status updates",
        }
        
        for step in self.workflow.get_steps():
            events[f"command.{step.worker_type}"] = f"Commands for {step.worker_type} worker"
            events[f"result.{step.worker_type}"] = f"Results from {step.worker_type} worker"
            
            if step.compensation:
                events[f"command.{step.compensation}"] = f"Compensation commands for {step.compensation}"
                events[f"result.{step.compensation}"] = f"Compensation results from {step.compensation}"
        
        return events