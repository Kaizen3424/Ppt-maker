"""LangGraph wiring - connects all agents into a directed graph."""
import os
from pathlib import Path

from langgraph.graph import StateGraph, END

from core.state import PresentationState
from core.config import get_config
from agents import (
    orchestrator_agent,
    researcher_agent,
    narrative_agent,
    designer_agent,
    visual_qa_agent
)


def build_graph():
    """Build and compile the LangGraph workflow.
    
    Returns:
        Compiled LangGraph StateGraph
    """
    # Load configuration
    config_path = Path(__file__).parent / "config.yaml"
    config = get_config(str(config_path) if config_path.exists() else None)
    
    # Create the workflow
    workflow = StateGraph(PresentationState)
    
    # Add nodes for each agent
    workflow.add_node("orchestrator", lambda s: orchestrator_agent(s, config))
    workflow.add_node("researcher", lambda s: researcher_agent(s, config))
    workflow.add_node("narrative", lambda s: narrative_agent(s, config))
    workflow.add_node("designer", lambda s: designer_agent(s, config))
    workflow.add_node("visual_qa", lambda s: visual_qa_agent(s, config))
    
    # Set entry point
    workflow.set_entry_point("orchestrator")
    
    # Define the linear flow
    workflow.add_edge("orchestrator", "researcher")
    workflow.add_edge("researcher", "narrative")
    workflow.add_edge("narrative", "designer")
    workflow.add_edge("designer", "visual_qa")
    
    # Add conditional edge for QA loop
    # If QA finds errors, loop back to designer for corrections
    workflow.add_conditional_edges(
        "visual_qa",
        qa_router,
        {
            "designer": "designer",
            "end": END
        }
    )
    
    return workflow.compile()


def qa_router(state: PresentationState) -> str:
    """Router function for QA conditional edge.
    
    Args:
        state: Current presentation state
        
    Returns:
        "designer" if there are errors to fix, "end" otherwise
    """
    errors = state.get("errors", [])
    
    if len(errors) > 0:
        # There are visual issues to fix - loop back to designer
        return "designer"
    
    # No errors - we're done
    return "end"


def run_graph(initial_state: dict) -> dict:
    """Run the graph with initial state.
    
    Args:
        initial_state: Initial state dictionary
        
    Returns:
        Final state after graph execution
    """
    graph = build_graph()
    return graph.invoke(initial_state)
