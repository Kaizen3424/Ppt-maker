"""AI Presentation CLI - Generate professional presentations with AI."""
import os
import sys
from typing import Optional

import typer
from rich.console import Console
from rich.status import Status
from rich import print as rprint
from rich.panel import Panel

from graph import build_graph
from compiler.pptx_builder import generate_pptx

app = typer.Typer()
console = Console()


@app.command()
def generate(
    prompt: str = typer.Argument(..., help="The topic of your presentation"),
    output: str = typer.Option("output.pptx", help="Path to save the final PPTX file"),
    config: Optional[str] = typer.Option(None, help="Path to config.yaml file"),
):
    """Generate an AI-powered presentation.
    
    Example:
        python cli.py "Create a 5-slide pitch deck for a new sustainable sneaker brand" --output my_pitch.pptx
    """
    rprint(Panel.fit(
        "[bold blue]🚀 AI Presentation Agent[/bold blue]\n"
        f"[dim]Topic: {prompt}[/dim]",
        border_style="blue"
    ))
    console.print()
    
    # Initialize state
    initial_state = {
        "prompt": prompt,
        "metadata": {},
        "json_deck": {"slides": []},
        "errors": [],
        "current_agent": "Starting..."
    }
    
    # Build the graph
    graph = build_graph()
    
    # Run LangGraph with live progress updates
    final_state = None
    
    with Status("[bold green]Starting agents...", spinner="dots") as status:
        # Stream events to update UI
        for output_event in graph.stream(initial_state):
            for node_name, state_update in output_event.items():
                # Update spinner with current agent activity
                agent_msg = state_update.get("current_agent", f"Node {node_name} finished.")
                status.update(f"[bold cyan]{agent_msg}")
                
                # If QA found errors, log them
                if node_name == "visual_qa" and state_update.get("errors"):
                    for error in state_update["errors"]:
                        rprint(f"[yellow]⚠️ QA Flagged: {error}[/yellow]")
                        rprint(f"[yellow]→ Routing back to Designer for fixes...[/yellow]")
                
                # Track final state
                final_state = state_update
    
    # Check if we got a valid final state
    if final_state is None:
        rprint("[bold red]❌ Error: Failed to generate presentation[/bold red]")
        sys.exit(1)
    
    rprint("\n[bold green]✅ AI Generation Complete![/bold green]")
    
    # Compile to PPTX
    console.print()
    with console.status("[bold magenta]Compiling PPTX file..."):
        try:
            output_path = generate_pptx(final_state["json_deck"], output)
            rprint(f"[bold green]🎉 Presentation saved successfully to {output_path}[/bold green]")
        except Exception as e:
            rprint(f"[bold red]❌ Error compiling PPTX: {e}[/bold red]")
            # Print the JSON deck for debugging
            import json
            console.print("[dim]Generated JSON deck:[/dim]")
            console.print(json.dumps(final_state["json_deck"], indent=2))
            sys.exit(1)


@app.command()
def version():
    """Show version information."""
    rprint("[bold blue]AI Presentation CLI v0.1.0[/bold blue]")


if __name__ == "__main__":
    app()
